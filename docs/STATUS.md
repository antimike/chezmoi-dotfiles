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
- `@docs/STATUS.md` import in `CLAUDE.md` verified working (2026-10-15): STATUS.md is in context at session start without a Read.
- BOCO merge **Phase 0a done and on `main`** (2026-10-15): chezmoi source root is now `home/`; docs, `tools/`, `CLAUDE.md`, `.envrc` and `.ripgreprc` stay at the repo root.
- A private doc (keys, findings, client terms) is committed in `~/Source/chezmoi-boco` but **not pushed** (waiting for MH's OK).

## Next actions (in order)
1. **BOCO merge, rest of Phase 0** ([plans/boco-merge.md](plans/boco-merge.md)): reload script, `is-wsl` helper, `work_tooling` key, zsh switch-over with scratch-home test, git/GPG/SSH config.
2. Then Phases 1–6 of the merge, one `boco-merge/<phase>` branch each.
3. Sway work ([plans/sway.md](plans/sway.md)); Phase 0a is done, so it can start.
4. Atlassian/Jira review pass and gitleaks hook rollout when MH schedules them.

## Blockers / watch
- `gitleaks detect --no-git` reports exactly 2 findings; they are **expected and accepted** (MH, 2026-10-15): `private_polybar-weather.service.tmpl` (generic-api-key) and `private_dot_jupyter/private_certs/private_service-key.pem` (private-key), both under `home/private_dot_config/…` and `home/private_dot_jupyter/…`. Anything beyond these two is a stop.
- The YubiKey must be plugged in for pushes, signing tags, `pass`, and the backup/sync timers.
- Atlassian/Jira items are held until a redaction pass ([plans/boco-merge.md](plans/boco-merge.md), "Held items").
- No second machine for testing the zsh switch-over; use the scratch-home method in the plan.

## Start prompt (paste when starting or restarting a session outside this directory)
> Work in `~/.local/share/chezmoi`. Read `CLAUDE.md` and `docs/STATUS.md`, then continue with "Next actions". Confirm with me before pushing, deleting remote branches, or anything outward-facing. Follow `docs/conventions.md`; the repo is public, so scan for client/employer terms and gitleaks before committing.

## At session end
Update this file (what changed, next actions, blockers), `docs/open-items.md`, and add any decision to `docs/decisions.md`. Commit docs separately.
