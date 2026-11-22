---
summary: Bootstrap of a fresh or lost Linux host (the old MacBook Pro first, D49) up to the bd-track restore hand-off; prior-art entry (D81), facts checked, open decisions for MH
status: decided (D83), 2026-11-21; building (chz-pc5)
updated: 2026-11-21
---

# Host bootstrap (chz-pc5)

Goal: from a freshly installed Fedora to the point where per-project restore can take over, following
only one document. First real client: the **old MacBook Pro** (D49: i3 on X11, no NVIDIA,
`work_tooling` off), a *second* host, not a replacement. Second client: a lost zbook.
Out of scope: the OS install itself, per-project restore (bd-track/pproj own it, below), and
running `bd-track restore` (MH 2026-11-03: the bootstrap stops and prints it).

## Facts checked (2026-11-21)

1. **`bd-track restore` does not exist.** Installed bd-track is 0.10.1 (`restore` is not a
   subcommand); `bd-timew-q9o.3` is open at P3. pproj's ticket to bd-track (2026-11-07, open)
   says restore becomes a `project-restore` hook of **`pproj restore` (pproj v0.3, unbuilt)**, and
   bd-track stops cloning. The hand-off command is therefore not settled either.
2. **No beads state repo exists.** `~/.config/bd-track/config.yaml` sets no `state_export` /
   `state_repo`; chezmoi's beads copy is the local `.beads/issues.jsonl` (CLAUDE.md interim). The
   repo it would go to is D71's `project-data`, still a draft (chz-2fk).
3. **bd-track's host config is already rendered by chezmoi** (`home/private_dot_config/bd-track/config.yaml.tmpl`,
   chz-uir), per host (`dolt_push` from WSL detection). It needs no backup.
4. **The registry**: `modify_projects.yaml` seeds 5 every-machine projects. zbook's live file has
   6 host-only entries; 5 have a GitHub remote (chezmoi-boco, claude-config, resume-builder,
   chess-trainer, pywhisper-dictation), one has none (baduk: its code is not off-machine at all).
5. **Private repos a host needs before Claude/bd-track run**: `claude-state` → `~/.claude/projects`
   (cloned by hand, [memory-and-backups.md](../runbooks/memory-and-backups.md) "New machine"), and
   the `pass` store (`~/.password-store`, origin on GitHub; needed for `backup/restic-<host>`).
   Both need the YubiKey: SSH goes through gpg-agent (`dot_zshenv.tmpl`), so the GPG public key and
   card stubs must be in place first ([gpg-and-signing.md](../runbooks/gpg-and-signing.md)).
6. **Transcripts** are per-host restic repos (`<drive>/backups/<host>/claude-transcripts`). A new
   host (MacBook) restores nothing; a lost zbook restores from PortableSSD.
7. `chezmoi init` builds the config from nothing (bootstrap-debt, fixed 2026-10-16). Host keys:
   `display_server` is detected at init, so **init must run from an X11 session on the MacBook**
   (from ssh it becomes `none`); `enable_user_lingering` is zbook-only, so bd-track's and
   sync-repos' timers would not fire without a login session on the MacBook.
8. The i3 config is not host-gated (`.chezmoiignore` has no i3 rule), so it deploys everywhere.

## Prior art (D81)

The bootstrap has two halves: machine setup (packages, dotfiles, installers), which chezmoi
already does, and a short, ordered, interactive sequence around it (YubiKey, private clones,
restic, hand-off). The candidates are judged on the second half.

| Candidate | What it would do | Requirement it fails |
|---|---|---|
| `chezmoi init --apply antimike/chezmoi-dotfiles` (get.chezmoi.io one-liner) | Clone source, render config, run every installer | Nothing for the machine half: **keep, it is step 1.** It cannot do the YubiKey/GPG setup that the private clones need before them, nor the restic restore (needs `pass`) |
| chezmoi `.chezmoiexternal` `git-repo` (claude-state, pass) | Clone private repos on apply | From chezmoi's docs (not tested): a failed external fails the apply, so every apply on a host or moment without the YubiKey would break; and `refreshPeriod` pulls inside chezmoi while `sync-repos` also pushes/pulls the same clone |
| chezmoi `run_once_after_` script for the private clones | Same, once | Runs non-interactively inside `apply` with a PIN prompt mid-run; a failure leaves run_once state to clear by hand. Viable but gains little over two documented commands |
| Ansible / `ansible-pull` | Whole bootstrap as a playbook | No hard requirement fails; rejected on cost: a second config language for ~6 steps, duplicating the `run_onchange_` installers or wrapping chezmoi. Revisit only if hosts multiply |
| `mani sync` / myrepos `mr checkout` | Clone many repos from a list | Project code clones are restore's job (pproj `clone`/`restore` v0.3); the bootstrap only clones 2-3 private data repos |
| `pproj restore` (v0.3) / `bd-track restore` | Per-project clone + beads + event logs | Not built (facts 1). Downstream of the bootstrap anyway: the hand-off target |
| yadm `bootstrap`, Fedora kickstart, bootc | Dotfiles-manager hook; OS install | yadm = switching managers; kickstart/bootc sit below our scope (the MacBook needs a hand install, Broadcom Wi-Fi first) |

**Conclusion:** chezmoi for the machine half (no new tool); the ordered interactive half is a
**runbook**, optionally with a small read-only **check script** that says which step a host is at.

## Decisions (MH, 2026-11-21: D83)

1. **Runbook + read-only check**: [runbooks/new-host.md](../runbooks/new-host.md) is the single
   source; `bootstrap-check` (deployed) reports which step a host has reached and ends with the
   hand-off.
2. **Done criterion redefined**: the bootstrap ends when the registry, bd-track's host config and
   the private clones are in place. The check prints `bd-track restore --all --dry-run` once the
   subcommand exists, otherwise the manual route (bd-track's restore runbook, `bd-timew-q9o.4`).
3. **State repo: a placeholder** until D71 creates `project-data`; not part of the drill.
4. **Beads are worked on zbook only.** The MacBook runs the desktop and Claude sessions without
   bead writes; multi-host beads would be sync (D71 Q3/Q4, D80), not restore.
5. **The registry is host state** (MH): the seed keeps only the tooling repos (chezmoi, bd-track,
   project-registry, claude-state; amontillado as a chezmoi dependency and ticket target). Other
   projects are registered per host; a lost host's entries are re-registered by hand until D71's
   repo backs up the live file.
6. **bd-track config.yaml**: rendered by chezmoi, nothing to back up.
7. Still open, not blocking: `enable_user_lingering` and transcript backups on the MacBook (both
   need its hostname; recommended: lingering yes, backups later).

## Drill

Scratch HOME (`HOME=$(mktemp -d)`; `chezmoi init --source <worktree> --apply` with
`--exclude scripts` for the drill, since installers need sudo and are covered by the live MacBook
run), then the runbook's steps in order, then `bootstrap-check`. The private clones in the drill
come from the local clones (`git clone ~/.claude/projects`), so the YubiKey step is exercised only
on the real MacBook.
