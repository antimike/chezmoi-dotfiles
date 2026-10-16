---
summary: Completed work log of the Claude Code migration (steps 0–7), with commits and how each was verified
status: complete except 7.2
updated: 2026-10-15
---

# Migration work log (BOCO/WSL2 → zbook, Fedora 44)

Historical record; current work is in [../STATUS.md](../STATUS.md). Decisions are in [../decisions.md](../decisions.md).
Original plan written 2026-10-08; steps executed 2026-10-08 to 2026-10-14.

| Step | Result | Notes / verification |
|---|---|---|
| 0 | `editorMode: vim` | |
| 1 Prepare chezmoi | Reviewed WIP; i3 screenshot bindings committed; `pyproj` work captured and merged; chezmoi 2.41 → 2.73 and mise 2024.2 → 2026.9 upgraded | All 317 managed files rendered byte-identically under both chezmoi versions. |
| 1 (tooling) | `mani`, `ghq`, `gitleaks`, `restic` installed | `mise` backend; pins in chezmoi. |
| 2 Reference clone | Employer-era repo cloned to `~/Source/chezmoi-boco`; private mirror created on the personal account | gitleaks over 253 commits: one historical finding, handled outside the repo (details private). |
| 3 Settings | `cleanupPeriodDays: 36500`, `model: opusplan`, `effortLevel: medium` | Made permanent by the modify script (4.3). |
| 4.0 Unblock chezmoi | Every `{{ output }}` call goes through `.chezmoitemplates/safe-output.sh` (a broken tool warns instead of aborting); pdm/argcomplete repaired; `okularrc` becomes `create_okularrc`; xsettingsd path bug fixed | Full `chezmoi diff` completes. |
| 4.1/4.2 Claude config | `dot_claude/` imported (commands, skills, scripts, references, auto-session); client specifics made generic *before* commit | Dropped: `/time-report`, `fewer-permission-prompts`, auto-session design logs. Held: claude-mem items, Atlassian data/agent. Found: chezmoi ignores source mode bits, so 7 auto-session scripts needed `executable_`. |
| 4.3 Settings modify script | `modify_settings.json.tmpl` | Tested against live, empty and customized input. |
| 4.4 Notifier adapter | `~/.claude/scripts/notify`, rendered per host | Verified with stubs, a real `notify-send`, a real systemd-run `reminder`. Found and fixed a latent WSL bug (shim rejected `--sound`/`--urgent`). |
| 4.5 SessionEnd hook | `bd-track status --session-id` replaces the timew hook | End-to-end check done in 6.4. |
| 4.6 Host data | `notifier`, `enable_user_lingering` added to `.chezmoi.yml.tmpl` | `enable_systemd_session_services` has a different meaning here (i3 session); not reused. |
| 4.7 Path fixes | Dropped the `home/` source prefix from ~33 paths; timer doc adapted | **Reversed by Phase 0a** of [plans/boco-merge.md](../plans/boco-merge.md). |
| 4.8 Apply | 119 changes applied, no conflicts | `chezmoi status` empty afterwards. |
| 5 Personal projects | `bd-track`, `claude-config`, `chess_trainer` cloned with history and published to the personal account (public); `transition-2026`, `blog`, `claude`, `confluence-connector`, `problems` published (private); `resume`, `resume-builder` pushed | gitleaks clean on all repos except two handled findings (details private). `chess_trainer` `main` now tracks the real project branch; the stale one is `legacy-main`. |
| 6.1 Tool pins | mise config + `.tool-versions` under chezmoi with exact pins; Fedora package list and dnf installer | See [bootstrap-debt.md](../bootstrap-debt.md). |
| 6.2 Beads | `bd` 1.3.1, `dolt` v2.4.0 installers | Newest releases ≥14 days old; checksum-verified. |
| 6.3 bd-track | justfile, installer fix, default URL → personal account; tag `v0.5.1` (v0.5.0's justfile was not idempotent) | Pinned in `.chezmoidata/bd_track.yaml`. |
| 6.4 Beads workflow | Underlying `bd`/`bd-track` steps run in a scratch project | The slash-command markdown itself has not been live-tested. |
| 6.5 Lingering | `run_onchange_after_enable-linger.sh.tmpl`; enabled via polkit | |
| 7.1 Memory/transcripts | 11 personal project folders + the home folder copied, renamed from the old username's path prefix to `-home-hseldon-*` | Byte counts matched per folder. Client/`-tmp-*`/`observer-sessions` folders excluded. |
| 7.2 claude-mem evaluation | **Deferred** | See [../open-items.md](../open-items.md). |
| 7.3 `claude-state` | `~/.claude/projects` is a git repo (only `memory/` tracked) pushed to a private repo; gitleaks pre-commit via the pre-commit framework | Negative test: a fake token blocked the commit. |
| 7.4 Transcript backups | restic repo on the external SSD, seeded; daily timer | `restic check` passes; see [runbooks/memory-and-backups.md](../runbooks/memory-and-backups.md). |
| Timers | `claude-state-sync`, `claude-transcripts-backup`, `claude-auto-session-logrotate` | Each run once under systemd. |

## Post-migration (2026-10-15)

- `bd-track` public tree scrubbed (see D21); GPG signing key switched (D22).
- BOCO merge plan written ([plans/boco-merge.md](../plans/boco-merge.md)); Sway plan extended ([plans/sway.md](../plans/sway.md)).
- Branches consolidated onto `main` (D26); docs consolidated into this tree (D30).
