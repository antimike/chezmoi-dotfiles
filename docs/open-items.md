---
summary: Every open item across the migration, BOCO merge, Sway and housekeeping, with source and who acts
status: current
updated: 2026-10-16
---

# Open items

"MH" = needs the repo owner. "Claude" = can be done in a session. Update this file when an item closes; keep decisions in [decisions.md](decisions.md).

## Next up
| Item | Who | Where |
|---|---|---|
| BOCO chezmoi merge, rest of Phase 0 | Claude | [plans/boco-merge.md](plans/boco-merge.md) |
| Push the private findings doc to `chezmoi-boco` (committed locally) | MH approval | `~/Source/chezmoi-boco/docs/zbook-migration/` |
| Distro-agnostic package map (logical names, per-manager overrides, non-native fallbacks) | MH + Claude | [Detail below](#detail-package-map-refactor); proposed as D32 |
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

## Detail: package map refactor
Status: proposed, not started ([D32](decisions.md) is a draft). Goal: make package installation distro-agnostic without scattering distro conditionals through templates.

**Today.** `home/.chezmoidata/packages.yaml` is `packages: fedora: [...]` and `run_onchange_install-packages.sh.tmpl` exits unless the distro is Fedora with `dnf`. Some other data files use `- dnf: <pkg>` / `- pipx: <pkg>` entries (`systemd.yaml`, `rofi.yaml`). Tools with pinned releases have their own `.chezmoidata/<tool>.yaml` plus `run_onchange_install-<tool>.sh.tmpl`.

**Design.**
1. **Logical-name map.** One entry per tool, keyed by a logical name. Per-manager overrides are listed only where the native package name differs. Example: `delta: { dnf: git-delta }` (the apt/pacman/brew name is `delta`).
2. **Manager key.** One derived data key (from `osRelease.id`: fedora to `dnf`, debian/ubuntu to `apt`, arch to `pacman`) selects the column. Adding a distro means one entry in that table, one install-command branch in the installer, and overrides only where names differ.
3. **Non-native tools.** A manager entry may be a *method* instead of a package name: `{ pipx: <pkg> }`, `{ mise: <backend:tool> }`, `{ cargo: <crate> }`, or `{ release: <tool-id> }` (use the repo's pinned-release installer). `false` or a missing entry means "not available here, use the `fallback`".
4. **No silent default when identity can differ.** Names that mean different programs on different distros (known case: `yq`, see below) must carry an explicit entry for every manager, never the default-to-logical-name rule. An optional `verify:` command (for example `yq --version | grep -q mikefarah`) is run after install and fails loudly on a mismatch.
5. **Fedora behaviour unchanged.** The refactor must produce the same single `dnf install` with the same package set. Acceptance: the rendered installer diff for this host shows no change in the package list.

**Open points.**
- `yq`: Fedora's `yq` is the Go tool (mikefarah). Debian/Ubuntu's `yq` is, to my recollection (not yet checked here), a different tool, the Python jq-wrapper. [bootstrap-debt.md](bootstrap-debt.md) lists `yq` as unmanaged; it is the natural first entry to model, with a `mise` or pinned-release method as the portable fallback.
- Nix derivations were considered for the non-native category and rejected as overkill for now (rationale in D32). Revisit only if more than a handful of tools need build recipes that `mise` backends cannot express.
- `git-delta` is added to the current Fedora list during Phase 0 and carried over by the refactor.
