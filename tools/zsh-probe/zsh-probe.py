#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["rich", "rich-argparse"]
# ///
"""Render the zsh files of this chezmoi repo into a scratch home and dump the resulting shell state.

`probe` renders ~/.zshrc, ~/.zshenv and ~/.local/share/zsh from a source tree (the working tree,
or any git revision with --baseline) into a scratch home, runs an interactive zsh there in a pty,
and writes the shell's state (environment, aliases, functions, fpath, options, key bindings,
zstyles, widgets, completions) to <scratch>/<label>/probe/.  `compare` diffs two such dumps.

Why it works this way (each point was a real failure while building it):
  * zinit "turbo" (wait) plugins only load at a prompt, so a pty session with several prompt
    cycles is required; `zsh -i -c exit` never loads them.
  * The session gets a clean environment; anything inherited from the caller hides what the
    config no longer sets.
  * The session waits for zinit's scheduler queue before dumping; a fixed delay races on a cold start.
  * Random ids (mise session token, fast-syntax-highlighting widget names) are normalised so two
    renders of the same tree compare equal.
  * `chezmoi init` is run against a copy of the live config, because the config template reads
    data from an existing config.

Examples:
  uv run tools/zsh-probe/zsh-probe.py probe new                 # working tree
  uv run tools/zsh-probe/zsh-probe.py probe old --baseline main # a git revision
  uv run tools/zsh-probe/zsh-probe.py compare old new --show alias
"""

from __future__ import annotations

import argparse
import difflib
import os
import pty
import re
import select
import shutil
import subprocess
import sys
import time
from logging import getLogger
from pathlib import Path

from rich.logging import RichHandler
from rich_argparse import RawDescriptionRichHelpFormatter

logger = getLogger(__name__)

TOOL_DIR = Path(__file__).resolve().parent
DUMP_SCRIPT = TOOL_DIR / "dump.zsh"
PROBE_FILES = (
    "env",
    "env-zshenv-only",
    "alias",
    "functions",
    "fpath",
    "path",
    "options",
    "bindkey",
    "zstyle",
    "widgets",
    "comps",
    "comps-names",
    "params",
    "stderr",
)
SESSION_PATH = "/usr/local/bin:/usr/bin:/usr/sbin:/bin"


class HelpFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    RawDescriptionRichHelpFormatter,
):
    """Preserve description/epilog whitespace, show defaults, and style with Rich."""


def run(cmd: list[str], *, check: bool = True, capture: bool = False, **kwargs):
    return subprocess.run(cmd, check=check, text=True, capture_output=capture, **kwargs)


def repo_root() -> Path:
    out = run(
        ["git", "-C", str(TOOL_DIR), "rev-parse", "--show-toplevel"], capture=True
    )
    return Path(out.stdout.strip())


def default_scratch() -> Path:
    cache = os.environ.get("XDG_CACHE_HOME")
    return (Path(cache) if cache else Path.home() / ".cache") / "zsh-probe"


def default_config() -> Path | None:
    base = Path.home() / ".config" / "chezmoi"
    for name in ("chezmoi.yml", "chezmoi.yaml", "chezmoi.toml", "chezmoi.json"):
        if (base / name).exists():
            return base / name
    return None


def clean_env(home: Path, extra: dict[str, str] | None = None) -> dict[str, str]:
    user = os.environ.get("USER", "user")
    return {
        **(extra or {}),
        "HOME": str(home),
        "ZDOTDIR": str(home),
        "TERM": "xterm-256color",
        "USER": user,
        "LOGNAME": user,
        "LANG": os.environ.get("LANG", "en_US.UTF-8"),
        "SHELL": "/usr/bin/zsh",
        "PATH": SESSION_PATH,
        "XDG_RUNTIME_DIR": f"/run/user/{os.getuid()}",
    }


def render(
    source: Path, home: Path, scratch: Path, label: str, config: Path, zinit: Path
) -> None:
    """Render the zsh files from `source` into `home` using a private copy of the chezmoi config."""
    cfg = scratch / f"{label}.chezmoi{config.suffix}"
    shutil.copy(config, cfg)
    run(
        ["chezmoi", "init", "--source", str(source), "--config", str(cfg)], capture=True
    )
    shutil.rmtree(home, ignore_errors=True)
    (home / ".local" / "share").mkdir(parents=True)
    (home / ".cache").mkdir()
    (home / "probe").mkdir()
    run(["cp", "-a", "--reflink=auto", str(zinit), str(home / ".local" / "share")])
    p10k = Path.home() / ".p10k.zsh"
    if p10k.exists():
        shutil.copy(p10k, home / ".p10k.zsh")
    state = scratch / f"{label}.state.boltdb"
    state.unlink(missing_ok=True)
    targets = [home / ".zshrc", home / ".zshenv", home / ".local" / "share" / "zsh"]
    run(
        [
            "chezmoi",
            "apply",
            "--source",
            str(source),
            "--destination",
            str(home),
            "--config",
            str(cfg),
            "--persistent-state",
            str(state),
            "--force",
            *map(str, targets),
        ],
        capture=True,
    )


def time_startup(home: Path, out: Path, runs: int = 3) -> None:
    """Record startup time and stderr of `zsh -i -c exit` (no pty, no turbo plugins)."""
    timings, errors = [], []
    for _ in range(runs):
        start = time.monotonic()
        result = run(
            ["zsh", "-i", "-c", "exit"],
            check=False,
            capture=True,
            env=clean_env(home),
            timeout=120,
        )
        timings.append(f"{time.monotonic() - start:.3f}")
        errors.append(result.stderr)
    (out / "timing.txt").write_text("\n".join(timings) + "\n")
    (out / "stderr.txt").write_text("".join(errors))
    only_zshenv = run(
        ["zsh", "-c", "env | sort"], check=False, capture=True, env=clean_env(home)
    )
    (out / "env-zshenv-only.txt").write_text(only_zshenv.stdout)


def pty_session(
    home: Path,
    out_dir: Path,
    *,
    history_off: bool = False,
    prompts: int = 8,
    queue_tries: int = 20,
) -> None:
    """Run an interactive zsh in a pty, let turbo plugins load, then source dump.zsh."""
    master, slave = pty.openpty()
    proc = subprocess.Popen(
        ["zsh", "-i"], stdin=slave, stdout=slave, stderr=slave,
        env=clean_env(home, {"ZSH_PROBE_OUT": str(out_dir)}), start_new_session=True, close_fds=True,
    )  # fmt: skip
    os.close(slave)
    out = bytearray()

    def pump(seconds: float) -> None:
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            ready, _, _ = select.select([master], [], [], 0.1)
            if not ready:
                continue
            try:
                data = os.read(master, 65536)
            except OSError:
                return
            if not data:
                return
            out.extend(data)

    def send(text: str) -> None:
        os.write(master, text.encode())

    pump(6)  # startup and the first prompt
    if history_off:  # do not write the session's commands into the real history file
        send("fc -p /dev/null\n")
        pump(1)
    for _ in range(prompts):  # turbo tasks run at prompts, so cycle a few
        send("sleep 1\n")
        pump(1.3)
    for _ in range(queue_tries):  # zinit keeps one permanent scheduler entry
        send('print -r -- "SCHED:$(sched | wc -l)"\n')
        pump(1.5)
        counts = re.findall(rb"SCHED:(\d+)", bytes(out))
        if counts and int(counts[-1]) <= 1:
            break
    else:
        logger.warning("zinit turbo queue never settled; the dump may be incomplete")
    send(f"source {DUMP_SCRIPT}\n")
    pump(4)
    send("exit\n")
    pump(2)
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
    (out_dir / "pty-session.txt").write_bytes(bytes(out))


def normalise(home: Path, label: str, out: Path) -> None:
    """Strip anything that differs between two renders of the same tree."""
    for path in out.glob("*.txt"):
        text = path.read_text(errors="replace")
        text = text.replace(str(home), "<HOME>").replace(
            f"scratch--{label}--", "scratch--LABEL--"
        )
        text = re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", text).replace("\r", "")
        text = re.sub(r"(?m)^(__MISE_SESSION|ZSH_PROBE_OUT)=.*$", r"\1=<x>", text)
        text = re.sub(r"(?m)^(DIRENV_DIFF|DIRENV_WATCHES)=.*$", r"\1=<x>", text)
        text = re.sub(r"orig-s[0-9]*-r[0-9]*-", "orig-S-R-", text)
        path.write_text(text)


def cmd_probe(args: argparse.Namespace) -> None:
    config = args.config or default_config()
    if config is None:
        sys.exit("zsh-probe: no chezmoi config found; pass --config")
    scratch = args.scratch
    scratch.mkdir(parents=True, exist_ok=True)
    home = scratch / args.label
    worktree: Path | None = None
    source = args.source or repo_root()
    if args.baseline:
        worktree = scratch / f"{args.label}.worktree"
        run(
            [
                "git",
                "-C",
                str(repo_root()),
                "worktree",
                "add",
                "-q",
                "--detach",
                str(worktree),
                args.baseline,
            ]
        )
        source = worktree
    try:
        logger.info("rendering %s into %s", source, home)
        render(source, home, scratch, args.label, config, args.zinit_dir)
        out = home / "probe"
        time_startup(home, out)
        logger.info("running the pty session (about a minute)")
        pty_session(home, out)
        normalise(home, args.label, out)
    finally:
        if worktree is not None:
            run(
                [
                    "git",
                    "-C",
                    str(repo_root()),
                    "worktree",
                    "remove",
                    "--force",
                    str(worktree),
                ],
                check=False,
            )
    widgets = len((home / "probe" / "widgets.txt").read_text().splitlines())
    timing = (home / "probe" / "timing.txt").read_text().split()
    print(
        f"probe {args.label}: widgets {widgets}, startup {' '.join(timing)} s -> {home / 'probe'}"
    )


def cmd_live(args: argparse.Namespace) -> None:
    """Dump the state of the real home (not a render), without touching shell history."""
    home = Path.home()
    out = args.scratch / args.label / "probe"
    shutil.rmtree(out.parent, ignore_errors=True)
    out.mkdir(parents=True)
    time_startup(home, out)
    logger.info("running the pty session against the real home (about a minute)")
    pty_session(home, out, history_off=True)
    normalise(home, args.label, out)
    print(f"live {args.label}: dump in {out}")


def cmd_compare(args: argparse.Namespace) -> None:
    first, second = (args.scratch / label / "probe" for label in (args.a, args.b))
    for directory in (first, second):
        if not directory.is_dir():
            sys.exit(f"zsh-probe: no probe dump at {directory}")
    differs = 0
    for name in PROBE_FILES:
        left = (
            (first / f"{name}.txt").read_text().splitlines()
            if (first / f"{name}.txt").exists()
            else []
        )
        right = (
            (second / f"{name}.txt").read_text().splitlines()
            if (second / f"{name}.txt").exists()
            else []
        )
        if left == right:
            print(f"same     {name}")
            continue
        differs += 1
        diff = [
            line
            for line in difflib.unified_diff(left, right, lineterm="", n=0)
            if line[:1] in "+-" and line[:3] not in ("+++", "---")
        ]
        added = sum(1 for line in diff if line[0] == "+")
        print(f"DIFFERS  {name}  (+{added} -{len(diff) - added})")
        if name in args.show:
            for line in diff:
                print(f"    {line[:160]}")
    for label, directory in ((args.a, first), (args.b, second)):
        timing = (
            (directory / "timing.txt").read_text().split()
            if (directory / "timing.txt").exists()
            else []
        )
        print(f"startup {label}: {' '.join(timing)} s")
    sys.exit(1 if differs else 0)


def get_cli_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=HelpFormatter)
    parser.add_argument(
        "--loglevel", "-l", default="INFO", type=lambda v: v.strip().upper(),
        help="Logging verbosity (DEBUG, INFO, WARNING, ERROR).",
    )  # fmt: skip
    parser.add_argument(
        "--scratch", type=Path,
        default=Path(os.environ.get("ZSH_PROBE_DIR") or default_scratch()),
        help="Directory for scratch homes (env ZSH_PROBE_DIR overrides the default).",
    )  # fmt: skip
    sub = parser.add_subparsers(dest="cmd", required=True)

    probe = sub.add_parser(
        "probe", help="Render and dump shell state.", formatter_class=HelpFormatter
    )
    probe.add_argument(
        "label", help="Name of this render; its dump goes to <scratch>/<label>/probe/."
    )
    group = probe.add_mutually_exclusive_group()
    group.add_argument(
        "--source",
        type=Path,
        help="Chezmoi source directory (default: this repo's working tree).",
    )
    group.add_argument(
        "--baseline",
        metavar="REV",
        help="Render this git revision through a temporary worktree.",
    )
    probe.add_argument(
        "--config", type=Path, help="Chezmoi config to copy (default: the live one)."
    )
    probe.add_argument(
        "--zinit-dir",
        type=Path,
        default=Path.home() / ".local" / "share" / "zinit",
        help="Zinit tree to copy into the scratch home.",
    )
    probe.set_defaults(func=cmd_probe)

    live = sub.add_parser(
        "live",
        help="Dump the real home's shell state (read-only).",
        formatter_class=HelpFormatter,
    )
    live.add_argument("label", help="Name of this dump.")
    live.set_defaults(func=cmd_live)

    compare = sub.add_parser(
        "compare",
        help="Diff two dumps; exit 1 if any differ.",
        formatter_class=HelpFormatter,
    )
    compare.add_argument("a", help="Label of the first dump.")
    compare.add_argument("b", help="Label of the second dump.")
    compare.add_argument(
        "--show",
        nargs="*",
        default=[],
        choices=PROBE_FILES,
        help="Print the diff lines for these files.",
    )
    compare.set_defaults(func=cmd_compare)
    return parser.parse_args()


def setup_logger(args: argparse.Namespace) -> None:
    handler = RichHandler(level=args.loglevel, show_path=False)
    logger.addHandler(handler)
    logger.setLevel(args.loglevel)


def main() -> None:
    args = get_cli_arguments()
    setup_logger(args)
    args.func(args)


if __name__ == "__main__":
    main()
