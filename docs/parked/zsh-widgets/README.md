---
summary: Two zsh widgets parked out of the managed tree; not loaded anywhere
status: parked
updated: 2026-10-16
---

# Parked zsh widgets

Moved out of `home/dot_local/share/zsh/widgets/` on 2026-10-16 (BOCO zsh switch-over). Nothing loads them.
Why: [../../zsh-plugins.md](../../zsh-plugins.md). In short, `twf.zsh` binds `^T`, which clashes with fzf, and `twf` is not installed;
`command-prefixes.zsh` calls `.toggle-command-prefix`, which is defined nowhere. Revive through the keybinding manifest (D33), not by restoring the directory.
