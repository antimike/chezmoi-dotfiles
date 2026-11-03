---
summary: How Claude auto-memory and transcripts are versioned (claude-state) and backed up (restic); restore and new-machine steps; failure modes
status: current
updated: 2026-10-17
---

# Memory and transcript backups

Two independent mechanisms protect `~/.claude/projects` (one folder per project path, `-home-<user>-…`):

| | `claude-state` (git) | transcript backup (restic) |
|---|---|---|
| What | `memory/` and `reports/` folders only (transcripts gitignored; `reports/` added 2026-10-23 for session reports holding private detail) | everything: transcripts and memory |
| Where | private GitHub repo `antimike/claude-state`; `~/.claude/projects` *is* the working tree `/run/media/$USER/<drive>/backups/zbook/claude-transcripts` on each drive in `.chezmoidata/backups.yaml` (restic repos; primary: PortableSSD, the external exFAT SSD) |
| When | `sync-repos.timer`, daily (`claude-state` is its list entry; the dedicated `claude-state-sync` timer was retired 2026-10-17); a failed run retries 3 times, 15 min apart | `claude-transcripts-backup.timer`, daily, `Persistent=true`, only when at least one listed drive is mounted (unmounted ones are skipped) |
| Secrets | gitleaks scan inside `sync-repos` on every unattended commit (refuses without gitleaks), plus the repo's pre-commit hook for commits by hand | restic encrypts the repo; password in `pass`, read unattended from a systemd credential (D74) |
| Source | `dot_local/bin/executable_sync-repos.tmpl`, list: projects with `sync_repo: true` in `~/.config/projects.yaml` (D75; seeded by `modify_projects.yaml`) | `dot_local/bin/executable_claude-transcripts-backup.tmpl` |

Units live in `private_dot_config/private_systemd/private_user/`. `cleanupPeriodDays` is 36500 so Claude never sweeps old transcripts.

## Passwords and keys

- restic password: `pass show backup/restic-zbook` (the scripts use `RESTIC_PASSWORD_COMMAND`). A hard copy exists off this machine. Losing it loses the backups.
- The timer run reads a copy of it from the systemd credential `claude-transcripts-backup.restic` (D74, chz-6w5; logs `using credential ...`) and falls back to `pass` without it. Create or refresh it after a password change (the YubiKey PIN is asked once; the whole `pass` output, exactly what `RESTIC_PASSWORD_COMMAND` gives restic):
  `(umask 077; pass show backup/restic-zbook | systemd-creds --user --name=claude-transcripts-backup.restic encrypt - ~/.config/credstore.encrypted/claude-transcripts-backup.restic)` (the umask gives the file mode 0600 like the deploy keys; made 2026-11-03)
- `sync-repos` pushes `claude-state` with its own deploy key since 2026-11-02 (D74, [automation-keys.md](automation-keys.md)), so it no longer needs the YubiKey; a repo without a deploy key falls back to the YubiKey.
- `pass` decrypts with the GPG key on the YubiKey ([gpg-and-signing.md](gpg-and-signing.md)). **If the key is unplugged, a backup without the credential fails** (and so does a `sync-repos` push for any repo without a deploy key). Neither loses data: `sync-repos` retries 3 times 15 min apart and then waits for the next day (each failed run sends one notification); the backup retries on its next run.
- Never print the secret: `pass show`/`gpg -d` write it to stdout, which lands in the transcript. Pipe or redirect it.

## Common operations

```sh
export RESTIC_REPOSITORY=/run/media/$USER/PortableSSD/backups/zbook/claude-transcripts
export RESTIC_PASSWORD_COMMAND="pass show backup/restic-zbook"
restic snapshots                           # list
restic restore latest --target /tmp/restore --include '*/memory/*'   # restore selected paths
restic check                               # integrity (the timer runs this at most every 30 days)
systemctl --user start claude-transcripts-backup.service   # run now
systemctl --user list-timers | grep claude                 # schedule
journalctl --user -u sync-repos -n 20                       # last claude-state sync
systemctl --user start sync-repos.service                  # sync now
```
Retention (in the script): keep 14 daily, 8 weekly, 12 monthly snapshots, then prune.

## Add a backup drive

The transcript backup goes to every drive listed in `home/.chezmoidata/backups.yaml` (`backups.claude_transcripts.drives`)
that is mounted; PortableSSD is the primary and the Kingston stick `Backups` the second copy (MH, 2026-11-03). A drive is named by its filesystem label, which udisks
uses as the mount point. All repos share the one restic password, so the one credential covers them.

1. Give the drive a unique label (exFAT keeps it readable on other systems): `sudo exfatlabel /dev/sdX1 <Label>`
   (or `sudo mkfs.exfat -L <Label> /dev/sdX1` for a blank drive), then mount it read-write
   (`udisksctl mount -b /dev/sdX1`; check `findmnt -no OPTIONS /run/media/$USER/<Label>` starts with `rw`).
2. Add `<Label>` to the list, commit, `chezmoi apply` (renders the script's drive list and one
   `ConditionPathIsMountPoint=|...` per drive; the `run_after_` reload picks up the unit).
3. Create the repo with the primary's password and chunker parameters (so `restic copy` deduplicates), and
   optionally copy the existing history over (the YubiKey PIN is asked once; gpg-agent caches it):
   ```sh
   primary=/run/media/$USER/PortableSSD/backups/zbook/claude-transcripts
   new=/run/media/$USER/<Label>/backups/zbook/claude-transcripts
   export RESTIC_PASSWORD_COMMAND="pass show backup/restic-zbook" RESTIC_FROM_PASSWORD_COMMAND="pass show backup/restic-zbook"
   mkdir -p "$(dirname "$new")"
   restic -r "$new" init --from-repo "$primary" --copy-chunker-params
   restic -r "$new" copy --from-repo "$primary"      # optional: seed the snapshots
   ```
   Without the PIN: the credential holds the same password, so `pc="systemd-creds --user
   --name=claude-transcripts-backup.restic decrypt $HOME/.config/credstore.encrypted/claude-transcripts-backup.restic -"`
   and `export RESTIC_PASSWORD_COMMAND="$pc" RESTIC_FROM_PASSWORD_COMMAND="$pc"` work too (used for Backups, 2026-11-03).
4. Check: `systemctl --user start claude-transcripts-backup.service`, then
   `journalctl --user -u claude-transcripts-backup -n 30` shows `== <Label>: ...` and `snapshot ... saved` per drive.

A listed drive that is mounted but has no repo, or is mounted read-only, fails the run (one notification; the other
drives are still backed up). To retire a drive, remove it from the list; its repo stays on the drive. Tests:
`tools/claude-transcripts-backup-test/claude-transcripts-backup-test`.

## New machine

1. Clone `claude-state` into `~/.claude/projects` **before** the first Claude session (private repo; needs the YubiKey for SSH), then run `pre-commit install` there (hooks are per clone; or `mani-discover && mani run install-hooks --all`). chezmoi does not clone it yet (open item).
2. If the username or home path differs, rename each folder: `-home-<olduser>-…` → `-home-<newuser>-…` (the folder name encodes the path with non-alphanumerics replaced by `-`).
3. Apply chezmoi (installs the scripts and timers; needs lingering, `enable_user_lingering`), plug in the SSD, and restore transcripts from restic if wanted.
4. Re-create `pass` entry `backup/restic-zbook` from the hard copy.

## Gotchas

- Folder names start with `-`: use `./-home-…` with `rm`, `du`, `ls`, and `--` with git.
- Until 2026-10-17 most daily syncs failed silently-ish: the timer fired on resume before DNS was up (`Could not resolve hostname github.com`) and never retried, stranding commits locally. `sync-repos` now waits up to 120 s for NetworkManager, then retries via the service.
- gitleaks may flag long hex (e.g. GPG fingerprints) in memory files as a "generic API key"; write key IDs instead of full fingerprints.
- The SSD is exFAT: no hard links or Unix permissions; restic stores permissions inside snapshots.
- **Read-only mount** (2026-10-29, chz-6w5): after a dirty unplug or USB resets (the SSD behind the USB-C hub linked at USB 2 and logged UAS aborts), the exFAT volume came up `ro` and every run failed with `repo not writable (read-only mount?)`. Check with `findmnt /run/media/$USER/PortableSSD`; fix: `udisksctl unmount -b /dev/sdX1 && sudo fsck.exfat -y /dev/sdX1 && udisksctl mount -b /dev/sdX1`. Mount paths are by label, so the hub does not move them.
