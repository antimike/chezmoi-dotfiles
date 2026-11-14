---
paths:
  - "home/**"
  - ".chezmoi*"
  - "**/.local/share/chezmoi/**"
---

# Chezmoi (dotfiles)

Loads when a chezmoi source file is read or edited in a session started in the chezmoi repo or in `~` (globs match relative to the working directory). From any other directory, the pointer in `~/.claude/CLAUDE.md` says to read this file first.

- **Chezmoi edits**: respect templating layers and known pitfalls when modifying dotfiles. See `feedback-chezmoi-patterns.md`.
- **Chezmoi propagation -- never `cp`**: to push a source edit to its live target, use `chezmoi apply --force <target>`, NOT `cp ~/.local/share/chezmoi/... ~/.claude/...`. A raw `cp` bypasses chezmoi's state bookkeeping, so a later `chezmoi apply` sees the target as externally-modified and tries to prompt before overwriting -- which fails with `could not open a new TTY` in a non-interactive shell. Using `apply` consistently keeps the bookkeeping coherent; `--force` skips the destination-modified confirmation.
- **Chezmoi worktree testing**: `chezmoi apply` always reads from the canonical source (`~/.local/share/chezmoi/`), not the active feature worktree. To test from a worktree: `chezmoi apply --source ~/Source/chezmoi-features/home --force <target>`.
- **Chezmoi repo docs**: plans, decisions, open items and current status for the dotfiles repo live in `~/.local/share/chezmoi/docs/` (start at `docs/STATUS.md`; the repo's own `CLAUDE.md` auto-loads it when the session runs there). When working on chezmoi from another directory, read it first.
