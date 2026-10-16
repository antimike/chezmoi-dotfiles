---
summary: Every open item across the migration, BOCO merge, Sway and housekeeping, with source and who acts
status: current
updated: 2026-10-15
---

# Open items

"MH" = needs the repo owner. "Claude" = can be done in a session. Update this file when an item closes; keep decisions in [decisions.md](decisions.md).

## Next up
| Item | Who | Where |
|---|---|---|
| BOCO chezmoi merge, rest of Phase 0 | Claude | [plans/boco-merge.md](plans/boco-merge.md) |
| Push the private findings doc to `chezmoi-boco` (committed locally) | MH approval | `~/Source/chezmoi-boco/docs/zbook-migration/` |
| Atlassian/Jira review and redaction pass | MH + Claude | [plans/boco-merge.md](plans/boco-merge.md), "Held items" |

## Plans waiting on a start
| Item | Who | Where |
|---|---|---|
| Sway session, then shared WM config fragment | Claude | [plans/sway.md](plans/sway.md) (Phase 0a done; unblocked) |
| claude-mem evaluation (about 30 min requirements, ~1 week trial in `CLAUDE_CONFIG_DIR=~/.claude-trial`) | MH + Claude | deferred; evidence so far favors dropping it |
| gitleaks pre-commit hook rollout across public repos | Claude | [plans/boco-merge.md](plans/boco-merge.md), Phase 3 |
| zsh switch-over test (scratch-home render first) | Claude | [plans/boco-merge.md](plans/boco-merge.md), Phase 0 |

## Housekeeping
| Item | Who | Notes |
|---|---|---|
| Delete stray remote branch `claude/implement-from-notes` in `chess_trainer` | MH approval | duplicate of `main`; deferred |
| Wire the env var for the credential moved to `pass` (consumer project unknown) | MH | details in the private doc |
| Rotate two unused keys that sit in the public chezmoi repo | MH | details in the private doc; source from `pass` |
| Extend or retire the expired old GPG key; clean the keyring | MH | [runbooks/gpg-and-signing.md](runbooks/gpg-and-signing.md) |
| Bring `~/.gitconfig`, `gpg.conf`, `~/.ssh/config` under chezmoi | Claude | Phase 0 of the BOCO merge |
| Live-test `/start`, `/stop`, `/status`, `/next` | MH | `/next` falls back to `bd ready` (`bv` not installed) |
| Prune the legacy session log in auto-memory `MEMORY.md` of the home project | Claude | it is not an index |
| LUKS partition on the external SSD (D18) | MH | needs ~60 GB moved off the exFAT drive first |
| Timers fail while the YubiKey is unplugged | info | retry next run; consider a dedicated unattended password path if annoying |
| Known gaps: java pin, Go version mismatch, unmanaged `yq`, `tofi` | Claude | [bootstrap-debt.md](bootstrap-debt.md) |
| `.chezmoi.yml` doctor warning (`suspicious-entries`) | info | cosmetic; renaming would create a second config |

## Closed recently
- BOCO merge Phase 0a (`home/` layout), merged and pushed 2026-10-15; the 2 gitleaks findings are accepted as expected.
- Public `bd-track` scrub (2026-10-15), GPG key switch, branch consolidation, step 7 (see [log/migration-steps.md](log/migration-steps.md)).

## Detail: claude-mem evaluation (deferred)
1. Requirements session with MH (~30 min).
2. Desk research (one web-search subagent): current claude-mem (is the `observer-sessions` recursion fixed?), native auto-memory, marketplace memory plugins, MCP memory servers. Criteria: footprint, dependencies, injected content, token cost, storage growth, export, maintenance, license.
3. Trial ~1 week in an isolated profile (`CLAUDE_CONFIG_DIR=~/.claude-trial`) vs a native-only baseline. Measure session-start tokens, `/usage` deltas, disk growth, and log whether it surfaced anything useful.
4. Decide, then migrate data. Clean its DB (drop `observer-sessions` and client rows, `VACUUM`) only if it stays. Evidence so far: 9,211 hook firings vs one `mem-search` invocation. Held items in chezmoi: `claude-mem-audit` skill/command, `claude-mem-cleanup` script and timer, `.claude-mem/` settings.
