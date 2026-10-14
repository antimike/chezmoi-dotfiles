#!/usr/bin/env python3
"""Poll a shell command on an interval until a condition holds, then notify.

The detached execution engine behind `/alert-timer --detached`. Unlike the
default ScheduleWakeup-driven alert-timer (which wakes Claude each cadence to
evaluate conditions with judgment), this runs as a plain background process:
zero Claude-token cost, no session involvement, fires one notification when
the condition is met or the timeout is hit.

Because no model is in the loop, the completion condition must be
shell-decidable: it is evaluated against the check command's stdout (stripped)
and exit code, not natural-language judgment.

Deliberately stdlib-only (no rich / rich-argparse / third-party deps) so it
runs under any python3 >= 3.10 in any directory, including contexts where the
project venv or rich is unavailable. This is the documented "rich-less context"
fallback from the python-scripting conventions.

Usage:
    # Poll a Snowflake running-query count until it reaches 0, then toast
    poll_until.py \
      --check "snow sql -c prod --format json --query \\"SELECT COUNT(*) AS N FROM ...\\" | python3 -c 'import sys,json;print(json.load(sys.stdin)[0][\\"N\\"])'" \
      --until eq:0 \
      --interval 90 --timeout 3600 \
      --notify-title "refresh done" \
      --notify-body "CUSTOMER_VISIT_SUMMARY initial refresh complete on PROD"

    # Poll until a command succeeds (exit 0)
    poll_until.py --check "curl -fsS https://host/health" --until exit-zero \
      --notify-title "Service up"

--until forms (evaluated against check stdout, stripped, and exit code):
    exit-zero | exit-nonzero
    empty | nonempty
    contains:<substr>
    eq:<n> | ne:<n> | lt:<n> | gt:<n> | le:<n> | ge:<n>   (numeric)
"""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
import time
from logging import getLogger

logger = getLogger(__name__)


class HelpFormatter(
    argparse.RawDescriptionHelpFormatter,
    argparse.ArgumentDefaultsHelpFormatter,
):
    """Stdlib-only formatter: preserve description whitespace + show defaults.

    Intentionally not the rich_argparse formatter -- this engine must run with
    zero third-party deps in unsupervised contexts.
    """


def get_cli_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=HelpFormatter,
    )
    parser.add_argument(
        "--check", required=True,
        help="Shell command run each interval; its stdout/exit-code feed --until.",
    )
    parser.add_argument(
        "--until", required=True,
        help="Completion condition (see module docstring for forms).",
    )
    parser.add_argument(
        "--interval", type=int, default=90,
        help="Seconds between checks.",
    )
    parser.add_argument(
        "--timeout", type=int, default=3600,
        help="Overall cap in seconds; fire the timeout notification and exit 2.",
    )
    parser.add_argument(
        "--check-timeout", type=int, default=60,
        help="Per-check timeout in seconds (a slow/hung check counts as not-met).",
    )
    parser.add_argument(
        "--notify-title", required=True,
        help="Notification title on success.",
    )
    parser.add_argument(
        "--notify-body", default="",
        help="Notification body on success.",
    )
    parser.add_argument(
        "--timeout-title", default=None,
        help="Notification title if the timeout is reached (default: derived).",
    )
    parser.add_argument(
        "--backend", default="desktop",
        help="Notification backend: 'desktop' (~/.claude/scripts/notify; 'wsl' "
        "is accepted as an alias), 'ntfy', or an absolute path to an "
        "executable called as `<path> <title> <body>`.",
    )
    parser.add_argument(
        "--ntfy-topic", default=None,
        help="ntfy.sh topic; required when --backend ntfy.",
    )
    parser.add_argument(
        "--loglevel", "-l", default="INFO",
        type=lambda v: v.strip().upper(),
        help="Logging verbosity (DEBUG, INFO, WARNING, ERROR).",
    )
    return parser.parse_args()


def setup_logger(level: str) -> None:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s", "%H:%M:%S"))
    logger.addHandler(handler)
    logger.setLevel(level)


def condition_met(spec: str, stdout: str, exit_code: int) -> bool:
    s = stdout.strip()
    if spec == "exit-zero":
        return exit_code == 0
    if spec == "exit-nonzero":
        return exit_code != 0
    if spec == "empty":
        return s == ""
    if spec == "nonempty":
        return s != ""
    if spec.startswith("contains:"):
        return spec[len("contains:"):] in s
    numeric_ops = {
        "eq:": lambda a, b: a == b,
        "ne:": lambda a, b: a != b,
        "lt:": lambda a, b: a < b,
        "gt:": lambda a, b: a > b,
        "le:": lambda a, b: a <= b,
        "ge:": lambda a, b: a >= b,
    }
    for prefix, op in numeric_ops.items():
        if spec.startswith(prefix):
            try:
                return op(float(s), float(spec[len(prefix):]))
            except ValueError:
                return False  # stdout not numeric yet -> condition not met
    sys.exit(f"poll_until: unrecognized --until spec '{spec}'")


def run_check(cmd: str, timeout: int) -> tuple[str, int]:
    try:
        proc = subprocess.run(
            cmd, shell=True, text=True, capture_output=True, timeout=timeout,
        )
        return proc.stdout, proc.returncode
    except subprocess.TimeoutExpired:
        logger.warning("check exceeded %ss; treating as not-met", timeout)
        return "", 124


def notify(backend: str, title: str, body: str, ntfy_topic: str | None) -> None:
    if backend in ("desktop", "wsl"):
        cmd = [os.path.expanduser("~/.claude/scripts/notify"), title, body]
    elif backend == "ntfy":
        if not ntfy_topic:
            sys.exit("poll_until: --backend ntfy requires --ntfy-topic")
        cmd = [
            "curl", "-s", "-H", f"Title: {title}",
            "-d", body, f"https://ntfy.sh/{ntfy_topic}",
        ]
    else:
        cmd = [backend, title, body]
    subprocess.run(cmd, text=True, check=False)


def main() -> None:
    args = get_cli_arguments()
    setup_logger(args.loglevel)

    start = time.monotonic()
    iteration = 0
    while True:
        iteration += 1
        elapsed = int(time.monotonic() - start)
        if elapsed >= args.timeout:
            mins = elapsed // 60
            title = args.timeout_title or f"{args.notify_title} (timeout)"
            body = f"Condition not met after ~{mins}m ({iteration - 1} checks). Investigate."
            logger.warning("timeout reached after %ss; notifying", elapsed)
            notify(args.backend, title, body, args.ntfy_topic)
            sys.exit(2)

        stdout, code = run_check(args.check, args.check_timeout)
        met = condition_met(args.until, stdout, code)
        logger.info(
            "iter %d (%ds): exit=%s out=%r met=%s",
            iteration, elapsed, code, stdout.strip()[:60], met,
        )
        if met:
            notify(args.backend, args.notify_title, args.notify_body, args.ntfy_topic)
            logger.info("condition met; notification sent")
            return
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
