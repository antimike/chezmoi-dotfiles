---
summary: Decision log (D1–D31) for the Claude Code migration, chezmoi merge, Sway and docs; one line per decision
status: current
updated: 2026-10-15
---

# Decisions

Append new decisions at the end; mark replaced ones "superseded by Dn". "MH" is the repo owner. Sensitive specifics
(keys, client names, findings) live in the private repo; see [conventions.md](conventions.md).

## Claude Code migration (D1–D18, 2026-10-08 to 2026-10-14)

| # | Decision |
|---|---|
| D1 | Superseded: clone the employer-era chezmoi repo from GitHub with full history (the drive copy had no unique committed content). |
| D2 | All chezmoi changes for the migration go on one branch off `AddSystemdConfigs`. Merged into `main` and the branch deleted 2026-10-15 (D26). |
| D3 | Keep generic work skills and commands. Do not migrate client-project material, memory or tooling (term list is private). |
| D4 | Migrate personal projects' memory **and** transcripts. |
| D5 | claude-mem stays on hold until evaluated (open item, see [open-items.md](open-items.md)). |
| D6 | Tool installs are managed by chezmoi `run_` scripts; bootstrap-by-hand is allowed meanwhile (tracked in [bootstrap-debt.md](bootstrap-debt.md)). |
| D7 | `bd-track` owns its installer; chezmoi pins a tag and delegates. |
| D8 | User lingering is enabled through chezmoi (`/var/lib/systemd/linger`), not etckeeper. |
| D9 | Notifier is `notify-send`; a per-host adapter (`~/.claude/scripts/notify`) translates the WSL shim's interface. |
| D10 | Files copied from the exFAT drive take permissions from neighbouring files. |
| D11 | Model `opusplan`, `effortLevel: medium`. |
| D12 | Auto-memory is versioned in a private `claude-state` repo. |
| D13 | This repo is authoritative. The employer-era repo is a read-only reference clone at `~/Source/chezmoi-boco`; files move across gradually with provenance trailers. |
| D14 | Copy the former work-account repos to the personal account as plain copies (not forks); keep the old remote as read-only `upstream`. |
| D15 | Skill/command dispositions approved. Dropped: `/time-report`, `task-init`. |
| D16 | `claude-state` design approved; transcript backups go to the external SSD. |
| D17 | Repo visibility table approved; restic chosen for transcript backups; gitleaks and restic installed. |
| D18 | Follow-up: consider a LUKS-encrypted partition on the external SSD (the old backup there is unencrypted). Needs ~60 GB moved off first. Open. |

## Migration execution (2026-10-14/15)

| # | Decision |
|---|---|
| D19 | Public repos (`chezmoi-dotfiles`, `bd-track`, `claude-config`, `chess_trainer`, `resume-builder`) are scanned for client/employer references and gitleaks *before* every commit; MH reviews the redaction diff. |
| D20 | Employer-specific *data* (colleague details, tenant IDs) is held back from the public chezmoi repo pending a review and redaction pass. Applies to the Atlassian data/template, the `jira-comment-drafter` agent and the Jira CLI config. |
| D21 | `bd-track` public history is not rewritten; the current tree is cleaned instead (JSONL export untracked, client prefix replaced). |
| D22 | gpg: `pass` and all GPG operations use key `9F049F34…` (valid to 2028). Git signing key switched from the expired one; see [runbooks/gpg-and-signing.md](runbooks/gpg-and-signing.md). |
| D23 | Secret scanning uses gitleaks as a pre-commit hook (via the pre-commit framework) in each repo that needs it, not inside sync tooling. |

## BOCO chezmoi merge (see [plans/boco-merge.md](plans/boco-merge.md))

| # | Decision |
|---|---|
| D24 | The employer-era repo is authoritative for tool-specific config (all Neovim themes/plugins, zsh, `.bashrc`); exceptions are the keep-ours list in the plan. |
| D25 | Keep all personally authored BOCO tooling, even if unused here. WSL-specific items are copied and guarded **inline in templates** (shared `is-wsl` helper); employer-only tooling is guarded by a `work_tooling` data key, default false. |
| D26 | Adopt the `.chezmoiroot = home` layout here (Phase 0a). Branch strategy: `main` is trunk; `BOCO-migration` and other merged branches were deleted 2026-10-15; each phase uses a `boco-merge/<phase>` branch. |
| D27 | Mail: personal and professional accounts only; the university account is dropped. |
| D28 | `sync-repos` is ported as low-priority BOCO tooling with an empty repo list; `mani` is optional for interactive status. |

## Desktop (see [plans/sway.md](plans/sway.md))

| # | Decision |
|---|---|
| D29 | Add a Sway session beside GNOME. Units are scoped to their session target, not excluded per host. Keep dunst and use gammastep. One shared WM config fragment drives both i3 and Sway. |
| D30 | The 2 gitleaks findings in the tree (a polybar-weather API key in a service template, a Jupyter service-key `.pem`) are expected and accepted (MH, 2026-10-15); a scan showing anything else is a stop. |

## Documentation

| # | Decision |
|---|---|
| D30 | Docs live in `docs/`, are organized for Claude to navigate (see [README.md](README.md)), and are public, so sensitive material goes to the private repo. `CLAUDE.md` + `docs/STATUS.md` replace one-shot session prompts. |
| D31 | Superseded plan drafts and the scratch notes file are deleted (rollback copy kept locally in `~/.local/state/claude-migration-backups/docs-2026-10-15/`). |

## Resolved questions (migration)

- **Q2 notifier:** `notify-send` plus the adapter; every caller (hooks, auto-session, `/reminder`, `/alert-timer`) uses the adapter.
- **Q3 timew:** not needed; bd-track 0.5 dropped it (SessionEnd hook uses `bd-track status`).
- **Q6 settings:** `modify_settings.json.tmpl` manages `cleanupPeriodDays`; model, effort, `autoCompactEnabled`, `awaySummaryEnabled` are set only if absent.
- **Q13 backups:** restic over rsync because the SSD is exFAT (no hard links), so rsync could only keep one unencrypted mirror.
