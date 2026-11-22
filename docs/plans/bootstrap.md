---
summary: Bootstrap of a fresh or lost Linux host (the old MacBook Pro first, D49) up to the bd-track restore hand-off; prior-art entry (D81), facts checked, open decisions for MH
status: draft, awaiting MH's decisions (chz-pc5), 2026-11-21
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

## Open decisions (MH)

1. **Script, runbook, or runbook + check.** Recommended: runbook `docs/runbooks/new-host.md` as
   the single source, plus `bootstrap-check` (deployed, read-only: chezmoi applied, YubiKey/GPG
   usable, private clones present, registry and host config parse, lingering; ends by printing the
   hand-off). The drill runs the check. A full bootstrap script would automate PIN, sudo and
   hardware steps a human must be present for anyway.
2. **Hand-off target and the done criterion**, since `bd-track restore` does not exist (fact 1).
   Recommended: the bootstrap ends at "registry, host config and private clones in place", the
   check prints `bd-track restore --all --dry-run` *if the subcommand exists*, otherwise points at
   bd-track's restore runbook (`bd-timew-q9o.4`) / the manual steps. The drill's pass condition
   becomes: `pproj list` and `bd-track config` read the registry and host config from the scratch
   HOME, and the private clones exist. Alternative: block chz-pc5 on q9o.3 (delays the MacBook).
3. **The state repo and D71** (fact 2). There is nothing to clone today. Options:
   (a) leave it a placeholder step ("clone the state repo once D71 creates it") and drop it from
   the drill; (b) decide D71 Q1/Q7 now and create `project-data` first (a session of its own,
   chz-2fk); (c) use `claude-state` as the beads state repo meanwhile. Recommended: **(a)**; (c)
   puts non-Claude folders into `~/.claude/projects` (untested with Claude Code).
4. **Is the MacBook a second working host for beads?** If you will work chezmoi beads on both
   machines, that is **sync**, not restore: a one-off import diverges at the first edit on either
   side. Recommended for now: beads are worked on zbook only; the MacBook runs the desktop and
   Claude sessions without bead writes. Otherwise this pulls in D71 Q3/Q4 and D80 (kata federation).
5. **Host-only registry entries** (fact 4). Recommended: move the 5 with a remote into the
   every-machine seed (they resolve by remote and scan roots; `path` only where it is outside the
   scan roots, e.g. resume-builder), and accept that a no-remote project (baduk) is not restorable
   until it gets a remote. Alternatives: a per-host seed in chezmoi data (public repo: future
   client project names would leak), or back the live file up into `project-data` once D71 lands.
6. **bd-track config.yaml**: nothing to decide (fact 3); the runbook says so.
7. **MacBook host keys** (fact 7): make `enable_user_lingering` true on the MacBook too (timers
   for sync-repos and bd-track), or keep it zbook-only? Recommended: true, keyed by hostname once
   the MacBook's hostname is chosen. Also: transcript backups on the MacBook (needs its own
   `backup/restic-<host>` pass entry and repos), or not for now? Recommended: not for now.

## Drill (once decided)

Scratch HOME (`HOME=$(mktemp -d)`; `chezmoi init --source <worktree> --apply` with
`--exclude scripts` for the drill, since installers need sudo and are covered by the live MacBook
run), then the runbook's steps in order, then `bootstrap-check`. The private clones in the drill
come from the local clones (`git clone ~/.claude/projects`), so the YubiKey step is exercised only
on the real MacBook.
