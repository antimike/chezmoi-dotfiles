# Issue tracker: keep beads or move to something lighter (chz-47g)

Desk evaluation, 2026-11-13. Decision: draft **D80** in [../decisions.md](../decisions.md). No migration
happens here. The follow-up is a one-week `tk` trial (MH).

Origin: MH's ticket after a browser review of his repos (`~/Documents/claude/repo-reviews.11132026.md`,
sections 5-6). MH added `git-bug` and a wider search for alternatives on 2026-11-13.

**Confirmed** means checked in this session, against the tool's README, licence or source, or by running
it. **Reported** means from a secondary source and not checked.

## Pain points

1. **Dolt slowness and data loss.** Compaction lost a triage session on 2026-11-05 (uncommitted changes
   under `dolt.auto-commit batch`).
2. **Complexity.** Plain issue tracking currently takes bd + Dolt + bd-track + a JSONL export.
3. **Public-repo friction.** `bd init` commits to the repo and adds a Dolt remote. Because `.beads/` is
   gitignored, the notes live outside the public repos.
4. **Curiosity** about the rest of the ecosystem.

## What our stack actually uses (confirmed)

**bd subcommands in skills, commands, rules and deployed helpers** (grep counts): `ready`, `list` (72
each), `remember`, `config`, `update`, `memories`, `create`, `show`, `dep`, `init`, `close`, `export`,
`note`, `jira` (20; work tooling), `link`, `dolt commit`, then `import`, `gc`, `compact`, `flatten`,
`label`, `statuses`, `search`, `query`. The molecule and formula commands (`mol`, `formula`, `cook`,
`swarm`) show up only in reference docs; no workflow uses them.

**bd-track** (8.5k lines of Python) calls `bd where`, `show`, `list --json`, `update`, `sql --csv`,
`config get/set`, `export --include-memories`, `compact`, `gc`, `hooks install`, `init`, and
`dolt commit/push/show/set/stop`. About 810 of those lines exist only for Dolt: `doltpush.py` (566) and
`server.py` (244). `project.py` adds more (Dolt users, server `.envrc`, the `auto-push` hang guard).

The requirements a replacement must meet, derived from that inventory:

| # | Requirement | Used by |
|---|---|---|
| R1 | Create, show, update and close, with `--json` | everything |
| R2 | Typed edges (`blocks`, `parent-child`, `related`, `discovered-from`) and a `ready` query | `/work-queue`, `/next`, bd-track queue reorder |
| R3 | Statuses beyond open/closed (`in_progress`, `deferred`, custom) | `/work-queue` park, `/stop --status` |
| R4 | Labels and notes | `/triage`, `/work-queue` |
| R5 | Project memories (`bd remember`/`memories`) | `bd prime`, session start |
| R6 | A plain-text export that restores | session-end backup |
| R7 | An atomic claim | only multi-agent runs; `/work-queue` is the single writer |
| R8 | Jira sync | work tooling only (BOCO), not used on zbook today |

## The JSONL backup restores (confirmed)

beads' README (`gastownhall/beads`) says: "`.beads/issues.jsonl` is an export for viewers and
interchange, not the source of truth or a backup." beads 1.3.x keeps its data in Dolt only (embedded,
or `dolt sql-server`), with an experimental HTTP backend.

I tested the round trip on this repo's store (bd 1.3.1):

- Ran `bd export --include-memories`, then `bd import` into a fresh `bd init` in a scratch repo, then
  exported again.
- Everything came back: 81 issues, 94 edges (blocks 28, related 37, parent-child 21, discovered-from
  8), 78 labels, 29 notes and the memory.

What the export does **not** cover:

- Dolt history.
- Comments: we have none, so they're untested.
- `.beads/queue.yaml` and bd-track's event logs, which are separate files.
- `config.yaml`.

So the README's warning holds in general, but for our feature set the session-end export is a working
backup. `tools/beads-restore-check` repeats this test; run it after a bd upgrade.

Side finding: `bd init` in the scratch repo also wrote `AGENTS.md`, `CLAUDE.md`, `.cursor/`, `.codex/`,
`.claude/` and `.agents/`. This is the same intrusion bd-track's `init-project` hit on 2026-11-06.

## Candidates

| Tool | Storage | R2 edges/ready | R3 statuses | R5 memories | R7 claim | Licence, size, adoption | Fit |
|---|---|---|---|---|---|---|---|
| **beads** (now) | Dolt | yes | custom | yes | `--claim` | MIT, Go, ~29k stars | does everything; the cost is Dolt |
| **tk** (`wedow/ticket`) | Markdown + YAML in `.tickets/`, one file per ticket | `dep`, `dep tree`, `dep cycle`, `link`, `ready`, `blocked` | open/in_progress/closed (**check custom statuses in the trial**) | no (use a Markdown file) | none | MIT, one Bash script (coreutils; `jq` for plugins), ~930 stars, no tagged releases | best match for "simpler"; `migrate-beads` imports `issues.jsonl` |
| **Knots** (`acartine/knots`, `kno`) | append-only events on an `origin/knots` branch + SQLite cache | `blocked_by`, `parent_of`, `ready` | its own fixed workflow (planning/implementation/shipment, each with review) | handoff capsules | atomic `poll --claim`, 10-min leases | MIT, Rust, `curl \| sh`, **17 stars** | good design reading; too small and too opinionated to adopt |
| **beads_rust** (`br`) | SQLite + JSONL (classic beads) | yes | yes | ? | ? | **excluded** (below), Rust, ~20k lines | no |
| **git-bug** | operation packs in `refs/bugs/*` | **no** | open/closed only | no | no | GPL-3+, Go, ~11k stars, v0.12.0 (2026-11-07) | tickets, not beads (below) |

**beads_rust licence (confirmed, LICENSE file).** MIT plus a rider that names "OpenAI, L.L.C.; Anthropic,
PBC; any of their respective Affiliates" as Restricted Parties. It says "no rights are granted to any
Restricted Party" and forbids letting them have access to the software ("make available, or otherwise
permit access"). Our sessions drive the tracker through Claude Code. That is plausibly "permitting
access", and the rider "controls" and terminates the licence on breach. This is not a legal opinion, but
the risk is easy to avoid: excluded.

**tk details (confirmed, README).** Plugins are any executable named `tk-<cmd>` or `ticket-<cmd>` on
`PATH`, and a plugin can override a built-in. Two consequences for us:

- Our `~/.local/bin/ticket-picker` would appear as `tk picker`.
- Our `ticket` command already takes the script's real name, so install the script only as
  `~/.local/bin/tk`.

tk has no locking. That's acceptable for one operator plus a single-writer `/work-queue`, but not for
`auto-session` swarms.

### Wider search (MH asked for a double check; second pass from the source)

The first pass judged these from READMEs and one blog post. The second pass (2026-11-13, MH's
questions) read each repo's source, shallow-cloned, and replaces it.

There are **two different tools called "beans"**:

- **`hmans/beans`**: Go, Markdown files.
- **`henriquebastos/beans`**: Python, SQLite plus a JSONL journal. PyPI `magic-beans`, CLI `beans`.

MH's description ("SQLite instead of Dolt") fits the second.

| | hmans/beans | henriquebastos/beans | grite | Knots | beads (now) |
|---|---|---|---|---|---|
| Storage | one Markdown file per bean; no database | SQLite (WAL mode) + journal table, exported as JSONL | CBOR events in `refs/grite/wal` + a sled cache per actor | JSON event files on a `knots` branch (worktree) + SQLite cache | Dolt |
| Kept outside the worktree? | yes: `BEANS_PATH` / `--beans-path`, or an absolute `beans.path` | **yes by default**: `~/.local/share/beans/<project>`, registry `~/.config/beans/config.json` keyed by git remote; `MAGIC_BEANS_DIR` | no flag: it discovers the git repo from cwd (libgit2 `discover`) and uses the fixed ref `refs/grite/wal`. A central repo works through a wrapper (`cd`), with every project in one WAL (separated by labels) | `-C`/`KNOTS_REPO_ROOT`, `--db`; git config `knots.remote` + `knots.remoteRef`, so per-project refs in one shared private repo look possible (**untested**); named projects are local-only (no git) | `.beans/` per repo |
| Edges | `parent`, `blocking`/`blocked_by` | `blocks` + `parent_id` | `blocks`, `depends_on`, `related_to` (no parent-child) | `blocked_by`/`blocks`, `parent_of` | blocks, parent-child, related, discovered-from, more |
| `ready` | `beans list --ready` (also excludes implicitly blocked children) | `beans ready` | `grite dep topo` (topological order, not a ready list) | `kno ready`, `kno poll --claim` | `bd ready` |
| Statuses | fixed five: todo, in-progress, draft, completed, scrapped | fixed three: open, in_progress, closed | open, closed | workflow states from loom bundles (planning, implementation and shipment, each with a review step; blocked, deferred) | built-in + custom |
| Labels / notes | tags / body only | **neither** (labels table dropped in schema v2) / body only | labels, comments | tags, notes, handoff capsules | both |
| Memories | archive of completed beans | no | `ProjectContextUpdated` key-value | no | `bd remember` |
| Claims | none (ETag optimistic writes) | `claim`/`release` (assignee + in_progress) | lease locks as refs (`refs/grite/locks/*`, TTL; policy off/warn/require) | atomic `poll --claim`, leases (10 min, refreshed by writes, **this machine only**) | `--claim` |
| Multi-host merge | none: git text merges, one file per bean | none: `export-journal` / `rebuild`; journal rows are whole-bean snapshots | CRDT: last-write-wins by timestamp for scalar fields, add/remove sets; a rejected push re-appends on the fetched head | union of immutable event files; refuses differing bytes; rebase-and-retry push | Dolt merge |
| Signing | no | no | optional Ed25519 per event; keys plain in `.git/grite/actors/<id>/keys/`, public keys only in the local actor config; `grite db verify` | no | no |
| Invasiveness | `beans prime` hooks, agent runner, web UI | none; prints a skill on request | writes `AGENTS.md` | **installs a `post-merge` hook**, `.claude/skills` | git hooks, agent files, Dolt remote |
| Size (GitHub language bytes) | Go 1.0 MiB + TS | Python 158 KiB (1.7k lines) | Rust 0.7 MiB | Rust 3.1 MiB (~70k non-test lines) | Go 47 MiB |
| Adoption, activity | 965★, last push 2026-04-06 | 66★, last push 2026-09-02 | 24★, created 2026-01, last push 2026-07-02 | 17★, last push 2026-08-28 | 28.7k★, daily |

**Encryption of just the issue ref (tested, grite's question c).**

- **gcrypt works.** A throwaway-key test pushed only `refs/grite/*` to a `gcrypt::` remote. The code
  branch stayed out, a plaintext grep of the remote found nothing, and a fetch decrypted the WAL.
- **But `grite sync` can't drive it.** grite syncs through libgit2, and libgit2 can't run `gcrypt::`
  remote helpers. So the transport is plain `git push`/`fetch` of `refs/grite/*`. That loses grite's
  re-append-on-rejected-push step, which needs a wrapper and a two-host divergence test.
- **git-crypt can't help.** It encrypts working-tree files through gitattributes filters, and grite
  writes git objects directly.
- **Knots should work with gcrypt (untested).** It calls the git binary and reads `knots.remote`.

**Performance (measured).** `bd show` costs 0.31 s per call, mostly opening embedded Dolt. `bd list
--json` returns all 81 issues in 0.34 s. `bd-track queue list -t` is slow because it calls `bd show`
once per line (`queue.py` `_fetch_title`). One `bd list --json` would make it constant time. That's a
bd-track fix, not a reason to change trackers.

A Python CLI also pays its imports on every call. henriquebastos/beans (typer + pydantic) is
unmeasured: installing it from PyPI was blocked by this session's permission check.

**Other names seen, not read:** wesm/kata (SQLite), epiq (events on a git branch), abarth/thicket,
pengelbrecht/ticks, bjia56/bodega, kostyay/kticket, Backlog.md, TrackDown, signalnine/bd (a
stripped-down beads fork, still on Dolt).

**git-bug-agent** is `https://github.com/selesy/git-bug-ax`. "git-bug-agent" is the README's name and
`gba` the binary. Confirmed: it adds status, priority, `blocks`, `parent` and claims to git-bug as
prefixed fields; 0 stars, no licence.

**git-issue** (`dspinellis/git-issue`, 2016, GPL-3.0, shell, 886★) has no dependencies, so it can't
replace beads. Its `.issues/` is its own git repo (one commit per change) and is found by walking up
from cwd. Each issue is a directory of small files: description, tags, comments, plus fields for
weight, milestone, due date, time estimate and time spent. It has two-way GitHub/GitLab sync. MH has a
fork in `~/Source/antimike/git-issue`. Compared with `ticket` and `tk` as a ticket store: see "Tickets"
below.

## git-bug (MH's questions)

**(a) Fit with the stack.** git-bug stores data in the repo's own refs (`refs/bugs/<id>`,
`refs/identities/<id>`), not the working tree. So there's nothing to gitignore. Refs travel only with
`git bug push`/`pull` or an explicit refspec; a plain `git push` leaves them out.

That fits beads alongside: accepted tickets become beads with `external_ref` set to the git-bug id. Its
bridges also import and export GitHub/GitLab/Jira/Launchpad issues, which our ticket files can't do.

It **clashes with D72** in two ways:

- **Tickets would move into the target repo.** Today a ticket is a file in
  `~/.local/state/triage/<project>/`, and filing one never touches the target repo. With git-bug,
  filing writes refs in that repo's `.git`. v0.12 removed the repo-wide lock, so concurrent writes are
  safe, but filing still writes to another project's repository.
- **Public repos.** `git bug push origin` publishes every ticket. Those projects would need a separate
  private remote just for git-bug refs.

There's also a cost per repo: an identity (`git bug user new`) and the cache in `.git/git-bug`.

**(b) How much of beads it replaces.** Little:

- It **has** titles, comments, labels, open/closed, search and authorship.
- It **lacks** dependencies, priority, `ready`, statuses beyond open/closed, and memories. The upstream
  requests for relations and priority are marked rotten or "awaiting more evidence".
- Labels can stand in for priority and status, but then we'd be rebuilding beads on top of git-bug,
  which is what `gba` does.

It could replace the **ticket inbox**, not beads.

**(c) Time tracking.** It's **neutral if git-bug only holds tickets**, because bd-track times beads, not
tickets. **Harder if it replaced beads**: there's no claim or `in_progress` to hang `/start` on (it
would become a label edit), there's no `ready` for `/work-queue`, and bd-track would need a second
backend. Its 7-character hash ids would work unchanged as bd-track's id strings.

**(d) The architecture (append-only logs in git refs).**

**Worth adopting for bd-track's event log**, in a simpler form than git-bug's:

- bd-track's events are already an append-only operation log: JSONL, ULID event ids, `correction`
  events folded latest-wins, one file per session.
- What git-bug adds is the transport. Commit those files under a per-host ref such as
  `refs/bd-track/<host>` and git syncs them without working-tree files or gitignore games.
- Each host writes only its own ref, so there are no concurrent edits. git-bug's Lamport clocks and DAG
  merge go unused, and "sync" is fetching every host's ref and folding the union by event id.
- That's a few dozen lines of `git hash-object`, `mktree` and `commit-tree`. It also gives D71 (one
  private repo for project data) a transport: push those refs only to the private remote.

**For a custom tracker, the same rule applies: one writer per ref, a union fold, last-write-wins on
scalar fields by event id.** That avoids the hard part of git-bug and grite, merging divergent DAGs.

Two things to avoid:

- Reusing git-bug's `entity/dag` package: it's GPL-3 Go, against our Python tooling.
- Pushing these refs to a **public** remote. GitHub doesn't show custom refs, but anyone can fetch
  them.

Build this only under the rule in the ticket: it must delete more code than it adds, and only after tk
fails a named requirement.

## Fit with MH's goals (second pass)

MH's goals, stated 2026-11-13:

1. Escape Dolt's slowness and fragility.
2. Less config.
3. All projects' issues in one private repo, outside the worktrees.
4. Conflict-free merges across hosts.
5. Exclusive claims for agent swarms.
6. Signed audit trails.

| Tool | 1-2 | 3 | 4 | 5 | 6 | Gaps against R1-R5 |
|---|---|---|---|---|---|---|
| tk | yes | `TICKETS_DIR` | git text merges (one file per ticket) | no | no | statuses, memories |
| hmans/beans | yes | `BEANS_PATH` | git text merges | no | no | statuses fixed, no notes or related edges; quiet since April |
| henriquebastos/beans | yes | **built in** (XDG data dir + registry) | **no** (snapshot journal, no merge) | claim, no lease | no | no labels, no notes, 3 statuses; it's a small Python codebase, so a fork could fill the gaps |
| grite | yes (daemon optional) | wrapper only, one WAL per repo | **yes** (CRDT; timestamp ties, so clock skew decides) | TTL lease locks | optional Ed25519, keys outside GPG/YubiKey, not distributed | no parent-child, no `in_progress`, no priority; 24★, quiet since July |
| Knots | yes (SQLite cache) | likely (`knots.remote`/`remoteRef`; untested) | **yes** (immutable event files) | **atomic claim + lease** (this machine only) | no | no `related`/`discovered-from`; fixed workflow (custom states need the loom DSL); git hook; 17★, one maintainer |

Time tracking is the same question for every candidate. bd-track needs `show`/`list`/`update`/claim
and a stable id string. Any of them fits behind an adapter; the work is making bd-track's calls go
through one backend layer instead of `bd`.

## Tickets: `ticket` vs git-issue vs tk (MH's question)

- **Ours.** `ticket` (458 lines of Python) plus `ticket-picker` (80). Per-project inboxes live outside
  the repos. Frontmatter: `from`, `date`, `type`, `urgency`, `status`, `resolved`, `outcome`. There's a
  `triage/` and `done/` split, quick notes in `inbox.md`, and integrations with `/triage`, Super+T, the
  SessionStart hook and zsh completion.
- **git-issue.** Gains: git history of every change, comments, attachments, time estimate and time
  spent, and GitHub/GitLab sync. Losses: the one-file-per-ticket Markdown format (each issue is a
  directory of small files), the provenance and resolution fields (they'd become tags), and every
  integration. It also has no env var to relocate the store; you `cd` above `.issues/`.
- **tk.** It's the closest format (Markdown + YAML) and has `TICKETS_DIR`, plus links that suit
  "duplicate of". Its statuses don't cover accepted, rejected and duplicate. It's also the same tool as
  the tracker trial.

Neither is a drop-in. Keep `ticket`. If the tk trial passes, tickets could become tk tickets in the same
store, which removes one tool. git-issue's real advantage is GitHub sync, the same as git-bug's.

## Proposal (draft D80)

1. **Keep beads for now.** The data-loss risk is covered: the export restores (above), and bd-track
   0.10.1+ commits before compacting. Dolt's cost is real but already paid. Moving off it pays only if
   it deletes the ~810 Dolt lines in bd-track and the server/`.envrc` setup.
2. **One-week tk trial**, follow-up bead, MH. Pass/fail against R1-R6:
   - Run `tk migrate-beads` and check the edge types survive.
   - Check custom/`deferred` statuses (R3).
   - Decide where memories live (R5).
   - Note what `/work-queue` and bd-track would need (a `tk` backend behind `bd show`/`list`/`update`).
   - Log every place tk was slower or clumsier than bd.
3. **Ticket inboxes stay files (D72); git-bug is not adopted.** It replaces only the inbox, which works.
   It would also put tickets inside target repos and need private remotes for public projects. Revisit
   if tickets should mirror GitHub Issues (git-bug's bridges are its real advantage).
4. **bd-track's event log in git refs** is a candidate transport for D71, filed as a design note there
   and not built now.
5. **beads_rust excluded** (licence rider); **Knots** read but not adopted (17 stars, fixed workflow).

### Trial project

**Recommended: `antimike/transition-2026`** (private; not cloned on zbook). Reasons:

- It already has `.beads/` committed, so the trial tests `migrate-beads` on real data.
- It's private, so `.tickets/` can be committed. That's tk's intended model, and the one public repos
  can't use.
- It's small (docs, runbooks, a decision log) and isn't a consumer of bd-track or `/work-queue`. A bad
  week costs nothing elsewhere.

Caveat: its last commit was 2026-06-20. The trial only means something if MH tracks this week's
transition and job-search tasks there. If those live somewhere else, a new private `job-search-2026`
repo is justified **only** for that reason (real daily use).

Not chosen:

- `resume-builder`: public, and dormant since 2024 (one commit 2026-10-17). It is cloned, at
  `~/Documents/personal/resume-builder`.
- `chess_trainer`: dormant.
- `chezmoi`: public, and every consumer of beads lives here.
