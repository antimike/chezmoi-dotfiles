---
summary: How Claude auto-memory and transcripts are versioned (claude-state) and backed up (restic); restore and new-machine steps; failure modes
status: current
updated: 2026-10-15
---

# Memory and transcript backups

Two independent mechanisms protect `~/.claude/projects` (one folder per project path, `-home-hseldon-…`):

| | `claude-state` (git) | transcript backup (restic) |
|---|---|---|
| What | `memory/` folders only (transcripts gitignored) | everything: transcripts and memory |
| Where | private GitHub repo `antimike/claude-state`; `~/.claude/projects` *is* the working tree | `/run/media/hseldon/PortableSSD/backups/zbook/claude-transcripts` (restic repo on the external exFAT SSD) |
| When | `claude-state-sync.timer`, daily | `claude-transcripts-backup.timer`, daily, `Persistent=true`, only when the SSD is mounted |
| Secrets | gitleaks pre-commit hook (`.pre-commit-config.yaml`) plus a check inside the sync script | restic encrypts the repo; password in `pass` |
| Source | `dot_local/bin/executable_claude-state-sync.tmpl` | `dot_local/bin/executable_claude-transcripts-backup.tmpl` |

Units live in `private_dot_config/private_systemd/private_user/`. `cleanupPeriodDays` is 36500 so Claude never sweeps old transcripts.

## Passwords and keys

- restic password: `pass show backup/restic-zbook` (the scripts use `RESTIC_PASSWORD_COMMAND`). A hard copy exists off this machine. Losing it loses the backups.
- `pass` decrypts with the GPG key on the YubiKey ([gpg-and-signing.md](gpg-and-signing.md)). **If the key is unplugged, the backup fails** (and pushing `claude-state` fails because SSH also uses the key). Neither loses data; both retry on the next run.
- Never print the secret: `pass show`/`gpg -d` write it to stdout, which lands in the transcript. Pipe or redirect it.

## Common operations

```sh
export RESTIC_REPOSITORY=/run/media/hseldon/PortableSSD/backups/zbook/claude-transcripts
export RESTIC_PASSWORD_COMMAND="pass show backup/restic-zbook"
restic snapshots                           # list
restic restore latest --target /tmp/restore --include '*/memory/*'   # restore selected paths
restic check                               # integrity (the timer runs this at most every 30 days)
systemctl --user start claude-transcripts-backup.service   # run now
systemctl --user list-timers | grep claude                 # schedule
journalctl --user -u claude-state-sync -n 20                # last run
```
Retention (in the script): keep 14 daily, 8 weekly, 12 monthly snapshots, then prune.

## New machine

1. Clone `claude-state` into `~/.claude/projects` **before** the first Claude session (private repo; needs the YubiKey for SSH), then run `pre-commit install` there (hooks are per clone).
2. If the username or home path differs, rename each folder: `-home-<olduser>-…` → `-home-<newuser>-…` (the folder name encodes the path with non-alphanumerics replaced by `-`).
3. Apply chezmoi (installs the scripts and timers; needs lingering, `enable_user_lingering`), plug in the SSD, and restore transcripts from restic if wanted.
4. Re-create `pass` entry `backup/restic-zbook` from the hard copy.

## Gotchas

- Folder names start with `-`: use `./-home-…` with `rm`, `du`, `ls`.
- gitleaks may flag long hex (e.g. GPG fingerprints) in memory files as a "generic API key"; write key IDs instead of full fingerprints.
- The SSD is exFAT: no hard links or Unix permissions; restic stores permissions inside snapshots.
