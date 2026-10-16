#!/usr/bin/env python3
"""Safe Markdown document moves and link-integrity audit.

Two subcommands:

  move <source> <dest> [--context-root <root>]
    Performs `git mv <source> <dest>` then rewrites all Markdown links across
    <context-root> that pointed at <source> to point at <dest>. Computes new
    relative paths from each linking file's perspective so links survive any
    depth shift between source and destination.

  audit <root> [--json]
    Scans all Markdown files under <root> and reports broken intra-repo links
    (paths that do not resolve to an existing file). External URLs and
    in-document anchors are not checked.

Both modes skip code regions (fenced ``` and ~~~ blocks, inline `code`) and
HTML comments. Inline links `[text](path)`, reference-style definitions
`[label]: path`, and `<img src="path">` references are all handled.

Folds in the corner cases observed during a large docs-tree restructure:

  - Inline links and image refs share LINK_RE
  - Reference-style definitions handled via REFDEF_RE
  - HTML img tags handled via IMG_HTML_RE
  - Bare-filename URLs (no `./` or `../` prefix) are caught by the resolver
  - Anchors preserved via partition-on-`#`
  - Code regions and HTML comments excluded from rewriting

Examples:

  move_doc_file.py move docs/old.md docs/new/old.md
  move_doc_file.py move docs/old.md docs/new/old.md --context-root .
  move_doc_file.py audit docs/ --json > broken-links.json
"""

from __future__ import annotations

import argparse
import bisect
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from logging import getLogger
from pathlib import Path

from rich.logging import RichHandler


logger = getLogger(__name__)


class HelpFormatter(
    argparse.RawDescriptionHelpFormatter,
    argparse.ArgumentDefaultsHelpFormatter,
):
    """Preserve whitespace in description/epilog AND show defaults in --help."""


LINK_RE = re.compile(r"(\]\()([^)]+)(\))")
REFDEF_RE = re.compile(r"^(\s*\[[^\]]+\]:\s+)(\S+)", re.MULTILINE)
IMG_HTML_RE = re.compile(r"""(<img[^>]+src=["'])([^"']+)(["'])""", re.IGNORECASE)
FENCED_RE = re.compile(r"```.*?```|~~~.*?~~~", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)

REMOTE_SCHEMES = ("http://", "https://", "mailto:", "ftp://", "file://")


def setup_logger(loglevel: str) -> None:
    handler = RichHandler(level=loglevel, show_time=False, show_path=False)
    logger.addHandler(handler)
    logger.setLevel(loglevel)


def find_repo_root(start: Path) -> Path:
    p = start.resolve()
    while p != p.parent:
        if (p / ".git").exists():
            return p
        p = p.parent
    sys.exit("move_doc_file: no .git directory found from " + str(start))


def get_skip_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for regex in (FENCED_RE, INLINE_CODE_RE, HTML_COMMENT_RE):
        for m in regex.finditer(text):
            spans.append((m.start(), m.end()))
    spans.sort()
    return spans


def in_skip(pos: int, spans: list[tuple[int, int]]) -> bool:
    for s, e in spans:
        if s <= pos < e:
            return True
        if pos < s:
            return False
    return False


def is_remote(link: str) -> bool:
    return link.startswith(REMOTE_SCHEMES) or link.startswith("#")


def split_anchor(link: str) -> tuple[str, str]:
    if "#" in link:
        path, _, anchor = link.partition("#")
        return path, "#" + anchor
    return link, ""


def resolve_link(file_relpath: str, link: str) -> str:
    """Resolve a (possibly relative) link against the linking file's directory.
    Returns a repo-relative path with anchor preserved."""
    path, anchor = split_anchor(link)
    if not path:
        return file_relpath + anchor
    file_dir = os.path.dirname(file_relpath)
    resolved = (
        os.path.normpath(os.path.join(file_dir, path))
        if file_dir
        else os.path.normpath(path)
    )
    return resolved + anchor


def compute_relative_link(from_file_relpath: str, to_target_relpath: str) -> str:
    target_path, anchor = split_anchor(to_target_relpath)
    from_dir = os.path.dirname(from_file_relpath)
    new_rel = os.path.relpath(target_path, from_dir) if from_dir else target_path
    return new_rel.replace(os.sep, "/") + anchor


@dataclass
class LinkOccurrence:
    file: str
    line: int
    col: int
    raw: str
    resolved: str
    kind: str


def iter_links(text: str, file_relpath: str) -> list[LinkOccurrence]:
    """Yield link occurrences in `text`, skipping code regions and HTML comments."""
    skip = get_skip_spans(text)
    line_starts = [0]
    for i, ch in enumerate(text):
        if ch == "\n":
            line_starts.append(i + 1)

    def line_col(pos: int) -> tuple[int, int]:
        line_idx = bisect.bisect_right(line_starts, pos) - 1
        return line_idx + 1, pos - line_starts[line_idx] + 1

    out: list[LinkOccurrence] = []
    for regex, kind, group in (
        (LINK_RE, "inline", 2),
        (REFDEF_RE, "refdef", 2),
        (IMG_HTML_RE, "img-html", 2),
    ):
        for m in regex.finditer(text):
            if in_skip(m.start(), skip):
                continue
            link = m.group(group)
            line, col = line_col(m.start())
            resolved = resolve_link(file_relpath, link)
            out.append(LinkOccurrence(file_relpath, line, col, link, resolved, kind))
    return out


def rewrite_file_for_move(
    repo_root: Path,
    file_relpath: str,
    moves: dict[str, str],
    file_old_relpath: str | None = None,
) -> tuple[int, list[tuple[str, str]]]:
    """Rewrite links in `file_relpath` so links resolving to any key in `moves`
    point at the corresponding value. Returns (count, sample_changes)."""
    if file_old_relpath is None:
        file_old_relpath = file_relpath
    file_abspath = repo_root / file_relpath
    try:
        text = file_abspath.read_text(encoding="utf-8")
    except (UnicodeDecodeError, IsADirectoryError, FileNotFoundError):
        return 0, []

    skip = get_skip_spans(text)
    samples: list[tuple[str, str]] = []
    sub_count = 0

    def maybe_rewrite(link: str) -> str:
        nonlocal sub_count
        if is_remote(link):
            return link
        old_resolved = resolve_link(file_old_relpath, link)
        old_path, anchor = split_anchor(old_resolved)
        new_path = moves.get(old_path)
        if not new_path:
            return link
        new_link = compute_relative_link(file_relpath, new_path + anchor)
        if new_link != link:
            sub_count += 1
            samples.append((link, new_link))
        return new_link

    def sub_inline(m: re.Match[str]) -> str:
        if in_skip(m.start(), skip):
            return m.group(0)
        return m.group(1) + maybe_rewrite(m.group(2)) + m.group(3)

    def sub_refdef(m: re.Match[str]) -> str:
        if in_skip(m.start(), skip):
            return m.group(0)
        return m.group(1) + maybe_rewrite(m.group(2))

    def sub_img(m: re.Match[str]) -> str:
        if in_skip(m.start(), skip):
            return m.group(0)
        return m.group(1) + maybe_rewrite(m.group(2)) + m.group(3)

    new_text = LINK_RE.sub(sub_inline, text)
    new_text = REFDEF_RE.sub(sub_refdef, new_text)
    new_text = IMG_HTML_RE.sub(sub_img, new_text)

    if sub_count and new_text != text:
        file_abspath.write_text(new_text, encoding="utf-8")
    return sub_count, samples


def cmd_move(args: argparse.Namespace) -> int:
    repo_root = find_repo_root(Path.cwd())
    context_root = (
        Path(args.context_root).resolve() if args.context_root else repo_root
    )
    source = Path(args.source).resolve()
    dest = Path(args.dest).resolve()

    if not source.exists():
        sys.exit(f"move_doc_file: source not found: {source}")
    if dest.exists():
        sys.exit(f"move_doc_file: dest already exists: {dest}")
    try:
        source_rel = str(source.relative_to(repo_root))
        dest_rel = str(dest.relative_to(repo_root))
    except ValueError:
        sys.exit("move_doc_file: source/dest must be inside the repo root")

    logger.info("Moving %s -> %s (context: %s)", source_rel, dest_rel, context_root)

    if args.dry_run:
        logger.info("[dry-run] would: git mv %s %s", source_rel, dest_rel)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "-C", str(repo_root), "mv", source_rel, dest_rel],
            check=True,
            text=True,
        )

    moves = {source_rel: dest_rel}
    skip_patterns = ("/.git/", "/node_modules/")
    candidate_files = sorted(
        {
            p
            for ext in ("*.md", "*.markdown")
            for p in context_root.rglob(ext)
            if not any(s in str(p) for s in skip_patterns)
        }
    )

    total_files = 0
    total_subs = 0
    for p in candidate_files:
        try:
            rel = str(p.resolve().relative_to(repo_root))
        except ValueError:
            continue
        file_old = source_rel if rel == dest_rel else rel
        if args.dry_run:
            text = p.read_text(encoding="utf-8", errors="ignore")
            for occ in iter_links(text, file_old):
                if is_remote(occ.raw):
                    continue
                resolved_path, anchor = split_anchor(occ.resolved)
                if resolved_path == source_rel:
                    new_link = compute_relative_link(rel, dest_rel + anchor)
                    logger.info(
                        "[dry-run] %s:%d %r -> %r", rel, occ.line, occ.raw, new_link
                    )
            continue
        n, samples = rewrite_file_for_move(
            repo_root, rel, moves, file_old_relpath=file_old
        )
        if n:
            total_files += 1
            total_subs += n
            logger.info("%s: %d substitutions", rel, n)
            for old, new in samples[:3]:
                logger.debug("  %r -> %r", old, new)
            if len(samples) > 3:
                logger.debug("  ... and %d more", len(samples) - 3)

    logger.info(
        "Summary: %d files touched, %d substitutions", total_files, total_subs
    )
    return 0


@dataclass
class BrokenLink:
    file: str
    line: int
    col: int
    link: str
    resolved: str
    reason: str


def cmd_audit(args: argparse.Namespace) -> int:
    repo_root = find_repo_root(Path.cwd())
    root = Path(args.root).resolve() if args.root else repo_root

    skip_patterns = ("/.git/", "/node_modules/")
    files = sorted(
        p
        for p in root.rglob("*.md")
        if not any(s in str(p) for s in skip_patterns)
    )

    broken: list[BrokenLink] = []
    for path in files:
        try:
            rel = str(path.resolve().relative_to(repo_root))
        except ValueError:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for occ in iter_links(text, rel):
            if is_remote(occ.raw):
                continue
            target_path, _ = split_anchor(occ.resolved)
            if not target_path:
                continue
            target_abs = repo_root / target_path
            if not target_abs.exists():
                broken.append(
                    BrokenLink(
                        rel,
                        occ.line,
                        occ.col,
                        occ.raw,
                        occ.resolved,
                        "target file not found",
                    )
                )

    if args.json:
        json.dump([asdict(b) for b in broken], sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        if not broken:
            logger.info(
                "No broken intra-repo links found across %d files under %s",
                len(files),
                root,
            )
        else:
            logger.warning(
                "Found %d broken intra-repo links across %d files:",
                len(broken),
                len(files),
            )
            for b in broken:
                print(
                    f"{b.file}:{b.line}:{b.col}: {b.link!r} -> {b.resolved!r} ({b.reason})"
                )
    return 1 if broken and args.fail_on_broken else 0


def get_cli_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="move_doc_file",
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
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_move = sub.add_parser(
        "move",
        help="Move a Markdown file and rewrite links across the context root.",
    )
    p_move.add_argument("source", help="Source path of the file to move.")
    p_move.add_argument("dest", help="Destination path.")
    p_move.add_argument(
        "--context-root",
        help="Directory to scan for linking files (defaults to git repo root).",
    )
    p_move.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Show planned changes without applying them.",
    )

    p_audit = sub.add_parser(
        "audit",
        help="Verify that all Markdown links under a root resolve to existing files.",
    )
    p_audit.add_argument(
        "root", nargs="?", help="Directory to scan (defaults to git repo root)."
    )
    p_audit.add_argument(
        "--json", action="store_true", help="Emit results as JSON to stdout."
    )
    p_audit.add_argument(
        "--fail-on-broken",
        action="store_true",
        help="Exit non-zero if any broken links are found (for CI).",
    )

    return parser.parse_args()


def main() -> int:
    args = get_cli_arguments()
    setup_logger(args.loglevel)
    if args.cmd == "move":
        return cmd_move(args)
    if args.cmd == "audit":
        return cmd_audit(args)
    sys.exit(f"move_doc_file: unknown command {args.cmd!r}")


if __name__ == "__main__":
    sys.exit(main())
