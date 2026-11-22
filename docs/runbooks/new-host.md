---
summary: Bootstrap a fresh or lost Linux host up to the per-project restore hand-off (D83); bootstrap-check reports the step a host is at
status: current
updated: 2026-11-21
---

# New host bootstrap

From an installed Fedora to the point where per-project restore takes over (D83; design and prior
art: [plans/bootstrap.md](../plans/bootstrap.md)). Two cases: a **second host** (the old MacBook
Pro, D49) and a **lost host** (zbook). Steps marked *(lost host)* are skipped on a second host.
At any point, `bootstrap-check` (deployed by step 1) prints what is done and the next step number.
This runbook ends before project clones and beads: it does **not** run restore.

You need: the YubiKey, network, sudo, and (lost host) the backup SSD and the hard copy of the
restic password.

## 0. Host preparation (by hand)

- Install Fedora; create the user `hseldon` (UID 1000: `~/.ssh/config` hard-codes the agent
  socket `/run/user/1000/...`; another user name means the claude-state folder renames in step 5).
- Set the hostname (`sudo hostnamectl set-hostname <name>`): host keys in `.chezmoi.yml.tmpl`
  test it (`enable_user_lingering` lists zbook only; add the new name there if its timers should
  run without a login, then re-apply).
- MacBook: Broadcom Wi-Fi needs RPM Fusion's `broadcom-wl` (wired or phone tethering until then).
- `sudo dnf install git chezmoi`
- Log in to the **graphical session you will use** (i3/X11 on the MacBook): `chezmoi init`
  records `display_server` from it, and from ssh or a TTY it records `none`.

## 1. chezmoi

```sh
chezmoi init --apply antimike/chezmoi-dotfiles   # public repo, https: no key needed yet
```

The apply installs packages (sudo prompt), the pinned tools (bd, dolt, bd-track, pproj, ...) and
renders `~/.config/projects.yaml` (the every-machine seed) and `~/.config/bd-track/config.yaml`.
A failed installer does not stop the others; re-run `chezmoi apply` after fixing it. Later, for
pushes: `chezmoi git -- remote set-url origin git@antimike.github.com:antimike/chezmoi-dotfiles.git`.

## 2. Tools

`bootstrap-check` step 2 lists any tool still missing (`gpg pass restic yq gitleaks bd bd-track
pproj`). Known hand-installed gaps: [bootstrap-debt.md](../bootstrap-debt.md).

## 3. GPG, YubiKey, SSH

```sh
curl -fsS https://github.com/antimike.gpg | gpg --import
echo 9F049F34C91F801DEDF87BBF7C1F6727C99C6EA5:6: | gpg --import-ownertrust
gpg --card-status                 # YubiKey plugged in: creates the secret-key stubs (ssb>)
ssh-add -L > ~/.ssh/yubikey-auth.pub   # the IdentityFile ~/.ssh/config names
ssh -T git@antimike.github.com    # "Hi antimike!"
```

Open a new shell after step 1 so `SSH_AUTH_SOCK` points at gpg-agent. Card trouble (pcscd,
`No such device`): [gpg-and-signing.md](gpg-and-signing.md), "Verify".

## 4. pass store

```sh
git clone https://github.com/antimike/pass ~/.password-store
pass ls >/dev/null && echo ok      # decrypts with the YubiKey
```

## 5. claude-state (before the first Claude session)

```sh
git clone git@antimike.github.com:antimike/claude-state.git ~/.claude/projects
cd ~/.claude/projects && pre-commit install
```

Different user name or home path: rename each `-home-<olduser>-...` folder to the new path's
encoding ([memory-and-backups.md](memory-and-backups.md), "New machine"). A second host's
sessions get their own folders alongside zbook's; `sync-repos` merges them nightly.

## 6. Registry and bd-track host config

Both come from step 1; nothing to restore. The registry is host state (D83): the seed names only
the tooling repos. Register this host's own projects as you clone them (edit
`~/.config/projects.yaml`, or `bd-track init-project` for beads projects). *(lost host)* The old
host's own entries are not backed up until D71's project-data repo exists: re-register them from
`gh repo list antimike`. `bootstrap-check` warns about `pproj check` findings such as "key
claimed by no installed plugin"; they are expected until bd-track and sync-repos are pproj plugins.

## 7. Lingering

`chezmoi apply` enables it where `enable_user_lingering` is true (step 0). Without it the
`sync-repos` and bd-track timers run only while you are logged in.

## 8. Transcripts *(lost host)*

Plug in the SSD, recreate the `pass` entry `backup/restic-zbook` from the hard copy if it is
missing, then:

```sh
export RESTIC_PASSWORD_COMMAND="pass show backup/restic-zbook"
restic -r /run/media/$USER/PortableSSD/backups/zbook/claude-transcripts snapshots
restic -r /run/media/$USER/PortableSSD/backups/zbook/claude-transcripts restore latest \
    --target ~/transcripts-restore --include '*.jsonl'
rsync -a --ignore-existing ~/transcripts-restore"$HOME"/.claude/projects/ ~/.claude/projects/
```

Restore to a scratch target, not `/`: the snapshot holds absolute paths and would overwrite the
step-5 clone's newer memory files. `--ignore-existing` adds only transcripts git did not bring.
Delete `~/transcripts-restore` afterwards.

A second host starts its own repos later ([memory-and-backups.md](memory-and-backups.md), "Add a
backup drive"; not set up for the MacBook yet).

## 9. Beads state repo (placeholder, D71)

None exists yet. Beads are worked on zbook only (D83). *(lost host)* Each project's beads come
back from its local `.beads/issues.jsonl` export only if that file survived, so for now a lost
zbook loses its beads unless the disk or a restic copy is readable.

## 10. Hand-off

`bootstrap-check` prints `bootstrap complete` and the next command: `bd-track restore --all
--dry-run` once bd-track has it (bd-timew-q9o.3), otherwise the manual route. The bootstrap does
not run it.

## Drill

`tools/bootstrap-drill/bootstrap-drill` runs steps 1, 4, 5, 6 and the check in a scratch HOME
from local clones (no YubiKey, no installers); the live MacBook run covers the rest.
