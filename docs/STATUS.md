---
summary: Where the work stands and what to do next; the repo's standing session-start prompt
status: current
updated: 2026-11-21
---

# Status

History (every earlier session, with merges, SHAs and test results): [log/sessions.md](log/sessions.md). Done items: [open-items.md](open-items.md), "Closed recently". Decisions: [decisions.md](decisions.md).

## Where we are
- **Priority (D50, 2026-10-18): functional daily driver first**; MH is job searching. Ricing, the keybinding manifest and other compositors are spare-time side quests ([plans/ricing-backlog.md](plans/ricing-backlog.md)).
- **Desktop: Hyprland is the daily driver (D62)**, SwayFX the fallback; "work" and "riced" logins (D66). Daily-driver checklist done except 2.9 (i3 off zbook) ([plans/wayland-desktop.md](plans/wayland-desktop.md), "Functional daily driver"). NVIDIA 615.78.08 installed; D61 (no docked suspend) still in force.
- **Theming: done through amontillado v0.9.0** (pinned, D70/D73): every app's colours come from amontillado's theme cache; GTK3/GTK4 live (D82); riced bar/dunst/blur (chz-8bg.5) and kitty tab bar (chz-8bg.12) done; LS_COLORS from vivid (chz-n6i); kitty and vivid follow the variant (pins lifted, chz-8bg.13; light tone soft; amontillado pinned at v0.13.0).
- **Work tracking:** beads (prefix `chz`, D80 keep beads); ticket inboxes (D72) with `/triage`; work queues via `/work-queue <scope>`. Design gates (D81) in `~/.claude/rules/design-gates.md`.
- **Infrastructure:** project registry via `pproj` (D76); `sync-repos` and transcript backups run on systemd credentials (D74), backups to every drive in `.chezmoidata/backups.yaml`; package map (D32) with `add-package`.
- **Git:** `main` is trunk, pushed 2026-11-21. Finished branches are archived as `refs/archive/<name>` or deleted (D65, `git retire-branch`; [conventions.md](conventions.md)).
- Claude Code migration (BOCO/WSL2 → zbook) done except the claude-mem evaluation ([log/migration-steps.md](log/migration-steps.md)).
- MH's untracked `ricing.md` stays unmodified at the repo root for MH's review; never commit it.

## Next actions
**Latest (2026-11-25 evening): amo v0.13.0 pinned (chz-0bb), D81 client rule amended (chz-psd), rofi pickers smart-case (chz-3h5); Bluetooth picker fixed and restyled** (chz-3iv ANSI strip, chz-lx8 connected rows in the accent + unique duplicate names; MH live, closed). Pushed. **Next:** **chz-1lm**, **chz-rr4**, **chz-64x** (unblocked); **chz-hbu** live MacBook run. Detail: [open-items.md](open-items.md).

Standing items (in order):
1. **GitHub Support request (MH)** to purge cached views / stale refs of the old (pre-rewrite) SHAs on `antimike/chezmoi-dotfiles`. The force-push is done; this is the last step that keeps the old client terms reachable until GitHub acts.
2. i3 off zbook (checklist 2.9; D50 amends D49).
3. **Home network follow-ups** (open items): DNS pinning, Wi-Fi profile cleanup, router move + re-measure; MH's router projects.
4. **Keychron mic key → F20** (low priority, MH when convenient): [runbooks/keychron-launcher.md](runbooks/keychron-launcher.md).
5. Atlassian/Jira review pass when MH schedules it.
6. Phase 4 (mail): **low priority** (MH: time-consuming, and webmail covers the need).

Side quests (spare time, D50): keybinding manifest, `swindings`, hyprpaper, other compositors' configs ([plans/ricing-backlog.md](plans/ricing-backlog.md)).
Deferred: hooks in `bd-track`/`claude-config`; chezmoi provisioning of `claude-state` and of one `dstask` repo (all in [open-items.md](open-items.md)).

## Blockers / watch
- **SQM decision point (D67; MH torn between options, keep in view):** option A (cake both ways, Shortcut-FE off) pegs the router CPU on big downloads (~30 Mbit/s shaped ceiling). Revisit B (SFE on, upload-only), C (25 Mbit/s down) or cake-autorate if the router moves, download speed starts to matter more, latency under load creeps back, or the router lags: [runbooks/home-network.md](runbooks/home-network.md), "SQM on the router".
- **No suspend while docked (D61)**: unplug the monitors first. A wedged display: SysRq REISUB (hold Alt, tap Fn+Home, then R E I S U B; installed and tested); holding the power key is a hard power cut.
- `gitleaks dir .` reports **no leaks**: the accepted finding (D30; one since chz-71g, 2026-11-02) is in `.gitleaksignore` by `file:rule:line` fingerprint. If that file changes so the finding moves line, it reappears: re-review, then refresh the fingerprint. Anything else is a stop.
- The YubiKey must be plugged in for pushes, signing tags and `pass`; the transcript backup and `sync-repos` (claude-state) no longer need it (D74 credentials).
- The PortableSSD sits on the USB-C hub at USB 2 (no free USB-C port); it logged UAS aborts on 2026-10-29. If they return: the `usb-storage.quirks=0781:55b0:u` modprobe.d quirk (open items, chz-6w5 row).
- Atlassian/Jira items are held until a redaction pass ([plans/boco-merge.md](plans/boco-merge.md), "Held items").
- No second machine for testing the zsh switch-over; use the scratch-home method in the plan.

## Start prompt (paste when starting or restarting a session outside this directory)
> Work in `~/.local/share/chezmoi`. Read `CLAUDE.md` and `docs/STATUS.md`, then continue with "Next actions". Confirm with me before pushing, deleting remote branches, or anything outward-facing. Follow `docs/conventions.md`; the repo is public, so scan for client/employer terms and gitleaks before committing.

## At session end
Update this file (what changed, next actions, blockers), `docs/open-items.md`, and add any decision to `docs/decisions.md`. Commit docs separately. **Keep this file under ~6k characters** (it loads into every session): replace the "Latest" entry, moving the previous one to the top of [log/sessions.md](log/sessions.md), and keep "Where we are" to current state, not history.
