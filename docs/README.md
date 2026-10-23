---
summary: Index of docs/ for Claude and humans: what each file is and when to read it
status: current
updated: 2026-10-23
---

# docs/ index

Organized for Claude to navigate: one topic per file, front matter (`summary`, `status`, `updated`) on every file,
at most two directory levels. Read [STATUS.md](STATUS.md) first; it is auto-imported by the repo's `CLAUDE.md`.
Facts live in one place and are linked, not copied. Update `updated:` when you change a file.

| File | What it is | Read when |
|---|---|---|
| [STATUS.md](STATUS.md) | Current focus, next actions, blockers, start prompt | every session start; update at session end |
| [conventions.md](conventions.md) | Commit, branch, scan, push, chezmoi and shell rules | before committing or pushing |
| [decisions.md](decisions.md) | Decision log D1–D51 | before changing a design; append new decisions |
| [open-items.md](open-items.md) | All open items with owner and pointer | choosing what to do next |
| [bootstrap-debt.md](bootstrap-debt.md) | Hand-installed tools and known gaps chezmoi should own | touching installers or packages |
| [zsh-plugins.md](zsh-plugins.md) | zsh plugins dropped, abandoned or worth investigating, with what each provided | dropping or adding a zsh plugin; missing a shell feature |
| [todo.md](todo.md) | Older checklist of files to add to chezmoi | porting dotfiles (partly superseded by the BOCO merge plan) |
| [plans/boco-merge.md](plans/boco-merge.md) | Phased plan to merge the employer-era chezmoi repo here | working on the merge, `home/` layout, guards |
| [plans/wayland-desktop.md](plans/wayland-desktop.md) | Compositor trial (SwayFX full port; niri, Hyprland, Wayfire minimal), uwsm, shared helper units, i3 → Sway mapping, greeter | desktop/Wayland work |
| [plans/keybinding-manifest.md](plans/keybinding-manifest.md) | Parked side quest: Lua keybinding manifest proposal and review; interim cheat sheet, `swindings` | resuming the manifest; building the cheat sheet |
| [plans/theming.md](plans/theming.md) | Theme bundles and switcher, wallpapers and palettes, fonts, pickers, lush.nvim | theming work (after the SwayFX daily driver) |
| [plans/devices-and-audio.md](plans/devices-and-audio.md) | Audio stack and media control review; hotplug for monitors, audio outputs, Bluetooth, drives, Wi-Fi | audio or device work on the desktop |
| [plans/ricing-backlog.md](plans/ricing-backlog.md) | Low-priority improvements checklist | looking for spare-time work |
| [runbooks/memory-and-backups.md](runbooks/memory-and-backups.md) | claude-state + restic: how, restore, failure modes | anything about transcripts, memory, timers |
| [runbooks/display-session-recovery.md](runbooks/display-session-recovery.md) | Failsafe for DM, greeter, compositor and GPU changes: prep, safe test, symptom table, rollback card | **before** any display manager, greeter, compositor or GPU change |
| [runbooks/gpg-and-signing.md](runbooks/gpg-and-signing.md) | GPG keys, git signing config, verification | signing, `pass`, YubiKey problems |
| [runbooks/keychron-launcher.md](runbooks/keychron-launcher.md) | Remapping the Keychron Q3 Pro (Launcher/WebHID), the udev rule, layout backup; open mic-key → F20 task | Keychron keys, VIA/Launcher access |
| [runbooks/home-network.md](runbooks/home-network.md) | Network layout (wired via the GL-AR750S repeater, Wi-Fi fallback), router firmware and pitfalls, NetworkManager commands, slow-link diagnosis | network problems, router work, Wi-Fi band, `tcp_metrics` |
| [log/migration-steps.md](log/migration-steps.md) | Completed Claude Code migration work log | history or provenance questions |
| [../tools/README.md](../tools/README.md) | Dev scripts: `compare-trees.py` (tree survey) and `zsh-probe/` (scratch-home zsh harness) | re-running the BOCO survey; testing zsh changes without touching `$HOME` |

Private companion docs (keys, findings, client terms) are in the private repo: `~/Source/chezmoi-boco/docs/zbook-migration/`.
This tree is public and chezmoi-ignored: never put secrets, client names or employer identifiers here (see [conventions.md](conventions.md)).
