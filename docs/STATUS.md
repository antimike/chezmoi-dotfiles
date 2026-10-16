---
summary: Where the work stands and what to do next; the repo's standing session-start prompt
status: current
updated: 2026-10-15
---

# Status

## Where we are
- Claude Code migration (BOCO/WSL2 → zbook, Fedora 44): **done** except the claude-mem evaluation. Log: [log/migration-steps.md](log/migration-steps.md).
- Dev environment is functional: chezmoi applied, tools pinned, `bd`/`bd-track`, `claude-state` sync and restic backups running, GPG on the YubiKey.
- `main` is trunk and in sync with origin. Docs consolidated into this tree on 2026-10-15.
- A private doc (keys, findings, client terms) is committed in `~/Source/chezmoi-boco` but **not pushed** (waiting for MH's OK).

## Next actions (in order)
1. **BOCO merge Phase 0a**: restructure this repo to `.chezmoiroot = home` ([plans/boco-merge.md](plans/boco-merge.md)). Record `chezmoi diff` first; it must be identical after. Then the rest of Phase 0 (reload script, `is-wsl` helper, `work_tooling` key, zsh switch-over with scratch-home test, git/GPG/SSH config).
2. Then Phases 1–6 of the merge, one `boco-merge/<phase>` branch each.
3. Sway work ([plans/sway.md](plans/sway.md)) after Phase 0a.
4. Atlassian/Jira review pass and gitleaks hook rollout when MH schedules them.

## Blockers / watch
- The YubiKey must be plugged in for pushes, signing tags, `pass`, and the backup/sync timers.
- Atlassian/Jira items are held until a redaction pass ([plans/boco-merge.md](plans/boco-merge.md), "Held items").
- No second machine for testing the zsh switch-over; use the scratch-home method in the plan.

## Start prompt (paste when starting or restarting a session outside this directory)
> Work in `~/.local/share/chezmoi`. Read `CLAUDE.md` and `docs/STATUS.md`, then continue with "Next actions". Confirm with me before pushing, deleting remote branches, or anything outward-facing. Follow `docs/conventions.md`; the repo is public, so scan for client/employer terms and gitleaks before committing.

## At session end
Update this file (what changed, next actions, blockers), `docs/open-items.md`, and add any decision to `docs/decisions.md`. Commit docs separately.
