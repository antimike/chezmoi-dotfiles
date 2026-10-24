# chezmoi source repo (zbook)

Dotfiles and Claude Code config for this machine, managed with chezmoi. **Public repo**: no secrets, client names or
employer identifiers (see docs/conventions.md; pattern list is in the private repo `~/Source/chezmoi-boco/docs/zbook-migration/`).

- Docs map: `docs/README.md`. Current state and next actions: @docs/STATUS.md
- Rules: `docs/conventions.md`. Decisions: `docs/decisions.md`. Open items: `docs/open-items.md`.
- This file, `docs/` and `tools/` (dev scripts; index in `tools/README.md`) are chezmoi-ignored (not deployed). After the `home/` restructure (BOCO merge Phase 0a) they stay at the repo root, outside the managed source.
- Project tooling goes in `tools/`, not the session scratchpad or `/tmp`: any diagnostic, test harness or helper that a later session or a re-test could reuse (e.g. `resume-check`). Give it a usage header, add a row and usage notes to `tools/README.md`, lint it (shellcheck/ruff), and commit it. The scratchpad is only for truly one-off scripts (a single data transform, a probe whose result is recorded in the docs). Helpers MH runs day to day belong in `home/dot_local/bin/` instead (deployed).
- Python conventions: the `python-scripting` skill is the source of truth (pointer in the global `~/.claude/CLAUDE.md`). Before the first `chezmoi apply` on a new machine, read its source copy: `home/dot_claude/skills/python-scripting/SKILL.md`.
- Porting a desktop helper: read MH's script in `~/Source/antimike/i3-config-mbp/bin/` first, recommend port or rewrite for the target stack, and review the script's quality for MH (detail: auto-memory `feedback-reuse-i3-config-mbp`).
- Confirm with the user before pushing, deleting branches, or other outward-facing actions.
- At session end, update `docs/STATUS.md` and `docs/open-items.md`.
