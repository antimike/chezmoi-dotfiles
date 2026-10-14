# ~/.claude/scripts/

Cross-project utilities invoked by Claude Code sessions or by the user directly. These scripts are stable, expected to live across many projects, and managed via chezmoi.

## Contents

| Script | Purpose | Skill / docs |
|---|---|---|
| `move_doc_file.py` | Safe Markdown file moves with link rewriting; Markdown-link integrity audit | `~/.claude/skills/move-markdown-doc/SKILL.md` |

## Conventions

All scripts under this directory follow the conventions in the `python-scripting` skill:

- Python 3.10+, `#!/usr/bin/env python3` hashbang
- `argparse` + custom `HelpFormatter` + `--loglevel`
- `logging` (with `RichHandler`) over `print` for diagnostics
- `pathlib.Path` over `os.path` string manipulation
- Module docstring becomes the `--help` description via `description=__doc__`
- No hardcoded credentials, paths, hostnames, or usernames
