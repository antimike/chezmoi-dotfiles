# chezmoi source repo (zbook)

Dotfiles and Claude Code config for this machine, managed with chezmoi. **Public repo**: no secrets, client names or
employer identifiers (see docs/conventions.md; pattern list is in the private repo `~/Source/chezmoi-boco/docs/zbook-migration/`).

- Docs map: `docs/README.md`. Current state and next actions: @docs/STATUS.md
- Rules: `docs/conventions.md`. Decisions: `docs/decisions.md`. Open items: `docs/open-items.md`.
- This file, `docs/` and `tools/` (dev scripts: `compare-trees.py`, `zsh-probe/`; see `tools/README.md`) are chezmoi-ignored (not deployed). After the `home/` restructure (BOCO merge Phase 0a) they stay at the repo root, outside the managed source.
- Porting a desktop helper: read MH's script in `~/Source/antimike/i3-config-mbp/bin/` first, recommend port or rewrite for the target stack, and review the script's quality for MH (detail: auto-memory `feedback-reuse-i3-config-mbp`).
- Confirm with the user before pushing, deleting branches, or other outward-facing actions.
- At session end, update `docs/STATUS.md` and `docs/open-items.md`.
