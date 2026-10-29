---
summary: One private repo for per-project private data (Claude memory, ticket inboxes, beads exports, bd-track config), a GitHub/restic split by kind of data, and one project registry; draft D71 with its open questions
status: draft (D71), 2026-10-29; nothing built yet except the ticket inbox (D72)
updated: 2026-10-29
---

# Private project data

Draft decision [D71](../decisions.md). MH's goal (2026-10-29): instead of one private "sidecar" repo
per kind of data (`claude-state` today; a beads state repo and a ticket repo proposed), **one
private repository for all private project data and metadata**.

## Proposed layout

```
~/.local/share/project-data/          one private git repo (replaces claude-state)
  claude/                             Claude Code auto-memory and session files (~/.claude/projects)
  projects/<name>/
    triage/  done/  triage/inbox.md   the ticket inbox (D72); ~/.local/state/triage/<name> points here
    beads/issues.jsonl                bd export, written by bd-track; restore = bd import
    bd-track/                         bd-track's per-project config (sidecar, registry entry)
```

- **Tickets** are the easy part: the inbox root simply lives in the repo.
- **Claude data:** Claude Code needs `~/.claude/projects`. Options, in order of preference:
  1. a **symlink** `~/.claude/projects -> project-data/claude` (to test: Claude Code writes through it,
     `/resume` and auto-memory still work, nothing resolves the real path into project names);
  2. a **bind mount** (a system mount unit or fstab line; needs root, D46);
  3. keep `claude-state` as its own repo for now and fold it in later.
  A **hard link is not possible**: Linux does not allow hard links to directories (and git would not
  follow one in either direction; git stores symlinks as links too, so the repo must hold the real
  directory).
- **Beads** are the hard part: each project's database is a binary Dolt store inside its own
  `.beads/`. Only the JSONL export goes into the repo; bd-track writes it (bd-track draft:
  `~/.local/src/bd-track/docs/dev/design-beads-state-repo.md`, branch `docs/beads-state-repo`).
- **Scanning:** gitleaks yes (sync-repos already refuses unattended commits without it, D36); the
  client-term grep no (the repo holds client data by design).

## Split by kind of data

| Destination | What | Why |
|---|---|---|
| Private GitHub repo (`sync-repos`) | memory files, tickets, bead JSONL exports, bd-track config | small text, worth diffing and merging, needed on a new machine |
| restic to the external SSD (encrypted, versioned) | Claude session transcripts (already, `claude-transcripts-backup`), the Dolt databases themselves, the wallpaper library (MH's own images cannot be re-fetched), a second copy of the git repo | large, binary or bulky; restic rather than rsync for versions and encryption on exFAT |

## Dolt-native options (facts checked 2026-10-29, Dolt 2.4.0, bd 1.3)

- **bd auto-backup is already on** in chezmoi and amontillado: embedded mode with a git remote turns
  it on (`backup.enabled` default), every 15 min, to `.beads/backup/` in the project (local only,
  gitignored). `bd backup init <path>` points it elsewhere, e.g. the external SSD (a full Dolt
  backup: tables, branches, history, working set); in server modes it is off by default.
- **Dolt can use a git repository as a remote**, storing its data under a git ref
  (`dolt remote add --ref <ref>`, default `refs/dolt/data`). So **several databases can share one
  GitHub repo**, each under its own ref (e.g. `refs/dolt/chz`, `refs/dolt/amo`). The option is in
  Dolt's help; **not tested here**.
  - For: full fidelity (history, branches), and the same private repo as everything else; ordinary
    clones do not fetch `refs/dolt/*` unless a refspec asks, so they stay small.
  - Against: `bd dolt push` stalls on network trouble (MH's global rule keeps it out of
    automation; it stays a manual, best-effort push); binary chunk history grows the GitHub repo
    without bound (no compaction on the remote side); two storage formats in one repo.
  - Likely blend: JSONL in git (automated, readable), Dolt backup to the SSD (automated, full
    fidelity), a Dolt git remote only as an optional manual push.
- **Shared server vs shared database** (MH's question):
  - `bd init --shared-server`: one `dolt sql-server` for all projects (`~/.beads/shared-server/`),
    **one database per project** (named after the prefix). bd also knows a separate cross-project
    database, `beads_global` (`--global`; bd-track's WSL-era metadata names it).
  - A **database shared by several projects** needs server mode (an embedded store lives in one
    project's `.beads/` and is opened in-process), so: a shared database implies a server, but a
    shared server does not imply a shared database.
  - What a project loses: verified only that auto-backup is off by default in server modes (bd's
    help: many clients would otherwise each sync the whole database). Unverified: whether a shared
    database mixes `bd ready`/`bd list` across prefixes, shares one Dolt history (so `bd dolt
    commit`, compaction and reverts are cross-project), or shares DB-stored settings. **Test in a
    scratch setup before deciding.**

## One registry

- `~/.config/projects.yaml` (chezmoi-managed, D72): project names matched to clones **by git
  remote**, the same on every machine (D35). `ticket` reads it; `mani-discover` names clones from it
  (mani's keys are paths today; mani has no alias field, but the key is the name, plus `desc` and
  `tags`), and reports named projects without a clone and clones without a name.
- **End state (MH): one registry with bd-track too**, without folding `ticket` into bd-track:
  compatible schemas and a configurable bd-track registry location. Ticket filed:
  `~/.local/state/triage/bd-track/triage/2026-10-29-shared-project-registry.md`.
- **Keeping mani current:** `mani-discover` takes 0.04 s for 76 clones, so a systemd user timer
  (hourly or daily) is cheap; proposed: such a timer, plus a run whenever the names file changes (`run_onchange_`).

## Open questions (for MH; some for a bd-track session)

1. Claude data: symlink (test first), bind mount, or keep `claude-state` separate for now?
2. Client data (from the bd-track draft): provisional (b)+(c). With one repo, (c) can be
   **git-crypt by path** (`projects/<work-project>/**` encrypted in place); (b), a separate repo,
   stays for a client whose rules forbid GitHub altogether.
3. Beads: JSONL only, plus `bd backup` to the SSD, plus an optional manual Dolt git remote per
   project (distinct refs)? Test the shared ref layout before relying on it.
4. Shared server and/or shared database: run the scratch test above; decide independently of this
   repo's layout (it changes only where the export step reads from).
5. Should `bd memories` be exported too (overlap with Claude auto-memory)?
6. Registry: the projects.yaml schema that bd-track can share (bd-track ticket above).
7. Repo name and history: rename `claude-state` (keeps its history) or start a new repo?
