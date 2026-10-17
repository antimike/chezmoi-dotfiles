#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["rich", "rich-argparse"]
# ///
"""Regenerate the Neovim lazy.nvim lockfile under a process cap and verify the merged config loads.

Headless `:Lazy! sync` fans out dozens of concurrent git clones plus compiler runs for treesitter
parsers, so this wraps it in a transient systemd scope with a TasksMax cap (and a wall-clock
timeout) to keep a fork storm from swamping the host. After the sync it runs a load probe that opens
a Lua and a Python buffer to force lazy-loaded plugins (treesitter, LSP, completion, formatting) to
initialise, then scans `:messages` for real errors.

`--clean` does a full clean-profile reconcile: it removes the installed plugins, state and cache and
truncates the lockfile first, so lazy resolves the whole graph fresh. This is what untangles stale
branch pins (e.g. nvim-treesitter stuck on the deprecated `master` branch) after a big LazyVim jump.

Error signals the probe treats as failures:
  * "too many rounds of missing plugins" - lazy could not finish installing a plugin across 5 rounds
    (on this host that was luarocks rock builds failing; see README).
  * "Error in <config>/init.lua" and any lazy spec error.
Cosmetic noise (headless nvim-notify, not-yet-installed LSP servers, the ruff binary) is ignored.

Examples:
  uv run tools/nvim-lazy-sync/nvim-lazy-sync.py                 # sync + verify in place
  uv run tools/nvim-lazy-sync/nvim-lazy-sync.py --clean         # full clean-profile reconcile
  uv run tools/nvim-lazy-sync/nvim-lazy-sync.py --verify-only   # just run the load probe
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from logging import getLogger
from pathlib import Path

from rich.logging import RichHandler
from rich_argparse import RawDescriptionRichHelpFormatter

logger = getLogger(__name__)

ANSI = re.compile(r"\x1b\[[0-9;]*m")

# Lines that mean the config is genuinely broken.
FAILURE_PATTERNS = (
    re.compile(r"too many rounds of missing plugins", re.IGNORECASE),
    re.compile(r"error in .*init\.lua", re.IGNORECASE),
    re.compile(r"error executing", re.IGNORECASE),
)
# Expected-absent tooling and headless-only noise - not config defects.
IGNORE_PATTERNS = (
    re.compile(r"nvim-notify", re.IGNORECASE),
    re.compile(r"quit with exit code", re.IGNORECASE),
    re.compile(r"no such file or directory", re.IGNORECASE),
    re.compile(r"lsp\.log", re.IGNORECASE),
)


class HelpFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    RawDescriptionRichHelpFormatter,
):
    """Preserve description whitespace, show defaults, and style with Rich."""


def get_cli_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=HelpFormatter,
    )
    parser.add_argument(
        "--loglevel",
        "-l",
        default="INFO",
        type=lambda v: v.strip().upper(),
        help="Logging verbosity (DEBUG, INFO, WARNING, ERROR).",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Full clean-profile reconcile: remove installed plugins/state/cache and truncate the "
        "lockfile before syncing, so the whole graph resolves fresh.",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Skip the sync; only run the load probe and report.",
    )
    parser.add_argument(
        "--nvim-config",
        type=Path,
        default=_default_nvim_config(),
        help="Neovim config directory (holds lazy-lock.json).",
    )
    parser.add_argument(
        "--nvim",
        default="nvim",
        help="nvim executable to use.",
    )
    parser.add_argument(
        "--tasks-max",
        type=int,
        default=512,
        help="Process cap (cgroup pids.max) for the systemd scope around nvim.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Wall-clock timeout (seconds) per nvim invocation.",
    )
    parser.add_argument(
        "--no-cap",
        action="store_true",
        help="Do not wrap nvim in a systemd scope (fallback when systemd-run is unavailable).",
    )
    return parser.parse_args()


def setup_logger(args: argparse.Namespace) -> None:
    handler = RichHandler(level=args.loglevel)
    logger.addHandler(handler)
    logger.setLevel(args.loglevel)


def _default_nvim_config() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "nvim"


def _data_dirs() -> list[Path]:
    home = Path.home()
    xdg_data = Path(os.environ.get("XDG_DATA_HOME", home / ".local" / "share"))
    xdg_state = Path(os.environ.get("XDG_STATE_HOME", home / ".local" / "state"))
    xdg_cache = Path(os.environ.get("XDG_CACHE_HOME", home / ".cache"))
    return [xdg_data / "nvim" / "lazy", xdg_state / "nvim" / "lazy", xdg_cache / "nvim"]


def wrap(cmd: list[str], args: argparse.Namespace) -> list[str]:
    """Prefix a command with a process cap + timeout unless disabled."""
    timed = ["timeout", str(args.timeout), *cmd]
    if args.no_cap or shutil.which("systemd-run") is None:
        if not args.no_cap:
            logger.warning("systemd-run not found; running without a process cap")
        return timed
    return [
        "systemd-run",
        "--user",
        "--scope",
        "--quiet",
        "-p",
        f"TasksMax={args.tasks_max}",
        "--",
        *timed,
    ]


def clean_profile(args: argparse.Namespace) -> None:
    for d in _data_dirs():
        if d.exists():
            logger.info("removing %s", d)
            shutil.rmtree(d)
    lock = args.nvim_config / "lazy-lock.json"
    logger.info("truncating lockfile %s", lock)
    lock.write_text("{}\n")


def run_nvim(nvim_cmds: list[str], args: argparse.Namespace) -> str:
    cmd = [args.nvim, "--headless"]
    for c in nvim_cmds:
        cmd += ["+" + c] if not c.startswith("+") else [c]
    cmd.append("+qa")
    full = wrap(cmd, args)
    logger.debug("running: %s", " ".join(full))
    proc = subprocess.run(
        full, check=False, text=True, capture_output=True, timeout=args.timeout + 60
    )
    return ANSI.sub("", (proc.stdout or "") + (proc.stderr or ""))


def sync(args: argparse.Namespace) -> None:
    logger.info(
        "running Lazy! sync (tasks-max=%d, timeout=%ds)", args.tasks_max, args.timeout
    )
    out = run_nvim(["Lazy! sync"], args)
    for line in out.splitlines():
        if any(p.search(line) for p in FAILURE_PATTERNS):
            logger.warning("sync: %s", line.strip())


def probe(args: argparse.Namespace) -> list[str]:
    """Open Lua + Python buffers to force lazy-load, dump :messages, return real error lines."""
    with tempfile.TemporaryDirectory() as td:
        lua = Path(td) / "probe.lua"
        py = Path(td) / "probe.py"
        lua.write_text("local M = {}\nreturn M\n")
        py.write_text("def f(x):\n    return x + 1\n")
        out = run_nvim(
            [
                f"edit {lua}",
                "sleep 2",
                f"edit {py}",
                "sleep 3",
                "messages",
            ],
            args,
        )
    seen: list[str] = []
    for line in out.splitlines():
        text = line.strip()
        if not text or any(p.search(text) for p in IGNORE_PATTERNS):
            continue
        if any(p.search(text) for p in FAILURE_PATTERNS) and text not in seen:
            seen.append(text)
    return seen


def main() -> None:
    args = get_cli_arguments()
    setup_logger(args)

    if not (args.nvim_config / "init.lua").exists():
        sys.exit(f"nvim-lazy-sync: no init.lua under {args.nvim_config}")
    if shutil.which(args.nvim) is None:
        sys.exit(f"nvim-lazy-sync: {args.nvim} not found on PATH")

    if args.clean and not args.verify_only:
        clean_profile(args)
    if not args.verify_only:
        sync(args)

    logger.info("running load probe")
    errors = probe(args)
    if errors:
        logger.error("config load reported %d error(s):", len(errors))
        for e in errors:
            logger.error("  %s", e)
        sys.exit("nvim-lazy-sync: config does not load cleanly (see errors above)")
    logger.info("config loads cleanly")
    lock = args.nvim_config / "lazy-lock.json"
    print(lock)


if __name__ == "__main__":
    main()
