---
name: move-markdown-doc
description: Safe Markdown file moves with cross-file link rewriting, and Markdown-link integrity audits. TRIGGER when moving or renaming any .md file inside a docs tree that has cross-references, when reorganizing a docs/ subtree, or when the user asks to "check for broken links" / "audit markdown links" across a project. Wraps the move_doc_file.py utility at ~/.claude/scripts/move_doc_file.py.
author: Michael Haynes
scope: global
tags: [markdown, docs, refactor, links]
timestamps:
  - action: created
    at: 2026-05-19T23:00:00-05:00
    actor: Michael Haynes
comments:
  - "Source: 2026-05-19 session. Built from the corpus of corner cases observed during a large coord-repo docs/ reorg that motivated this tool."
related: [python-scripting, ado-pr-draft]
---

# move-markdown-doc

Wraps `~/.claude/scripts/move_doc_file.py`, a Python utility for safely moving Markdown files and auditing Markdown link integrity across a project.

## When to invoke this skill autonomously

- The user asks to move, rename, or relocate any `.md` file that may be referenced from other Markdown files.
- A docs reorganization is planned (multiple `.md` files moving across a tree).
- The user asks to "check for broken links", "audit markdown links", or "verify docs links resolve" across a project or subdirectory.
- A pre-merge sanity check before opening a PR that touches doc paths.

## When NOT to invoke

- Moving a single `.md` file that has no cross-references (plain `git mv` is fine).
- Moving non-Markdown files. The tool only handles `.md` and `.markdown`.
- Cross-repository moves where the source and destination live in different git repos.

## Two modes

### `move`

```
move_doc_file.py move <source> <dest> [--context-root <root>] [--dry-run]
```

Runs `git mv <source> <dest>` then rewrites every Markdown link across `<context-root>` that resolves to `<source>` so it points at `<dest>` instead. New relative paths are computed from each linking file's perspective, so a depth shift between source and destination is handled transparently.

`<context-root>` defaults to the git repo root containing `<source>`.

`--dry-run` shows planned edits without applying them; useful before committing to a move.

### `audit`

```
move_doc_file.py audit [<root>] [--json] [--fail-on-broken]
```

Scans all `.md` files under `<root>` (default: git repo root) and reports broken intra-repo links: relative paths and bare-filename URLs that do not resolve to an existing file.

External URLs (`http://`, `https://`, `mailto:`, etc.) and in-document anchors (`#section`) are not checked. Cross-repo references (links pointing outside the audited root, e.g., `../other-repo/docs/...`) may appear as false positives when the audit is run from inside a single-repo worktree; treat as expected if the target actually exists in the broader filesystem at runtime.

`--json` emits a machine-readable list to stdout; useful for piping into other tools or saving as evidence.

`--fail-on-broken` exits non-zero if any broken links are found; useful in CI.

## What the tool handles

- Inline links: `[text](path)` and `[text](path#anchor)`
- Reference-style definitions: `[label]: path`
- HTML image tags: `<img src="path">`
- Anchors preserved across rewrites
- Bare-filename URLs without `./` or `../` prefix (resolved against the file's directory)
- Skip regions: fenced code blocks (` ``` ` and `~~~`), inline code (backticks), HTML comments (`<!-- ... -->`)

## What the tool deliberately does not handle

- Link **display text** updates. If a link reads `[OLD_NAME.md](new/path.md)`, only the URL gets rewritten; the display text stays as-is. Display-text drift is editorial cleanup, not a mechanical concern.
- Section anchor existence checks. The tool verifies the target file exists; it does not parse the target file to confirm a `#section` anchor exists inside it.
- Cross-repo reorganization. Each invocation is scoped to a single git repo.

## Source code and provenance

- Source: `~/.claude/scripts/move_doc_file.py`
- Provenance: 2026-05-19 session, built from corner cases observed during a coord-repo `docs/` restructure.
- Predecessor prototypes (kept for reference): `~/.claude/scripts/docs-reorg/path-substitute.py` and `~/.claude/scripts/docs-reorg/relative-link-fix.py`. These are subsumed by `move_doc_file.py`; remove the prototypes when convenient.

## Usage examples

```
# Dry-run a move, see planned link rewrites
move_doc_file.py move docs/old/foo.md docs/new/foo.md --dry-run

# Apply
move_doc_file.py move docs/old/foo.md docs/new/foo.md

# Quick audit of the whole repo
move_doc_file.py audit

# Audit a subdirectory, JSON output for downstream tooling
move_doc_file.py audit docs/ --json > broken-links.json

# CI gate
move_doc_file.py audit docs/ --fail-on-broken || echo "Fix the broken links above"
```
