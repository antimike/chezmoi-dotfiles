---
summary: Index of docs/ for Claude and humans: what each file is and when to read it
status: current
updated: 2026-10-16
---

# docs/ index

Organized for Claude to navigate: one topic per file, front matter (`summary`, `status`, `updated`) on every file,
at most two directory levels. Read [STATUS.md](STATUS.md) first; it is auto-imported by the repo's `CLAUDE.md`.
Facts live in one place and are linked, not copied. Update `updated:` when you change a file.

| File | What it is | Read when |
|---|---|---|
| [STATUS.md](STATUS.md) | Current focus, next actions, blockers, start prompt | every session start; update at session end |
| [conventions.md](conventions.md) | Commit, branch, scan, push, chezmoi and shell rules | before committing or pushing |
| [decisions.md](decisions.md) | Decision log D1–D31 | before changing a design; append new decisions |
| [open-items.md](open-items.md) | All open items with owner and pointer | choosing what to do next |
| [bootstrap-debt.md](bootstrap-debt.md) | Hand-installed tools and known gaps chezmoi should own | touching installers or packages |
| [zsh-plugins.md](zsh-plugins.md) | zsh plugins dropped, abandoned or worth investigating, with what each provided | dropping or adding a zsh plugin; missing a shell feature |
| [todo.md](todo.md) | Older checklist of files to add to chezmoi | porting dotfiles (partly superseded by the BOCO merge plan) |
| [plans/boco-merge.md](plans/boco-merge.md) | Phased plan to merge the employer-era chezmoi repo here | working on the merge, `home/` layout, guards |
| [plans/sway.md](plans/sway.md) | Sway session plan and i3 → Sway mapping | desktop/Wayland work |
| [plans/ricing-backlog.md](plans/ricing-backlog.md) | Low-priority improvements checklist | looking for spare-time work |
| [runbooks/memory-and-backups.md](runbooks/memory-and-backups.md) | claude-state + restic: how, restore, failure modes | anything about transcripts, memory, timers |
| [runbooks/gpg-and-signing.md](runbooks/gpg-and-signing.md) | GPG keys, git signing config, verification | signing, `pass`, YubiKey problems |
| [log/migration-steps.md](log/migration-steps.md) | Completed Claude Code migration work log | history or provenance questions |
| [../tools/compare-trees.py](../tools/compare-trees.py) | Path-level comparison of two chezmoi source trees | re-running the BOCO survey |

Private companion docs (keys, findings, client terms) are in the private repo: `~/Source/chezmoi-boco/docs/zbook-migration/`.
This tree is public and chezmoi-ignored: never put secrets, client names or employer identifiers here (see [conventions.md](conventions.md)).
