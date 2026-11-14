# Issue tracker: keep beads or move to something lighter (chz-47g)

Desk evaluation, 2026-11-13, then live tests of the finalists (chz-vkf, "Hands-on: kata, ticks, beans"). Decision:
draft **D80** in [../decisions.md](../decisions.md). No migration happens here. The follow-up is a one-week trial of
kata (chz-8fp, MH).

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
| henriquebastos/beans (tested, chz-vkf) | yes, but ~180 ms per call | **built in** (XDG data dir + registry) | **no**: the documented export/rebuild flow lost an issue; the append + union workaround converges but drops one host's field edits | claim refuses a second actor (5/5 in the test), no lease | no | no labels, no notes, 3 statuses, no importer; a fork now also needs a journal fix |
| kata (tested, chz-vkf) | yes, but a daemon + socket | **built in** (`KATA_HOME`, every project) | **not via git** (binary SQLite conflict); a shared remote daemon instead (untested) | **atomic claim**, `--ttl` lease, no doubles | `verification` field and daemon tokens (untested) | no memories; importer collapses every edge to `blocks` and drops notes |
| ticks (tested, chz-vkf) | yes; daily GitHub check | **no**: store fixed at `<git root>/.tick`; one shared store with project labels only | **yes**: field-level merge driver (converged; later title wins, labels unioned) | **no**: 10 of 10 parallel claims "succeed" | no | no `related`, no memories; importer skips closed issues |
| grite | yes (daemon optional) | wrapper only, one WAL per repo | **yes** (CRDT; timestamp ties, so clock skew decides) | TTL lease locks | optional Ed25519, keys outside GPG/YubiKey, not distributed | no parent-child, no `in_progress`, no priority; 24★, quiet since July |
| Knots | yes (SQLite cache) | likely (`knots.remote`/`remoteRef`; untested) | **yes** (immutable event files) | **atomic claim + lease** (this machine only) | no | no `related`/`discovered-from`; fixed workflow (custom states need the loom DSL); git hook; 17★, one maintainer |

Time tracking is the same question for every candidate. bd-track needs `show`/`list`/`update`/claim
and a stable id string. Any of them fits behind an adapter; the work is making bd-track's calls go
through one backend layer instead of `bd`.

## Hands-on: Knots and grite (2026-11-13, MH asked)

**Setup.** Throwaway HOME and git config, bare repos standing in for GitHub and a private repo, and a
throwaway GPG key for gcrypt.

- Knots v0.18.2 was built from source with Fedora's Rust 1.98.
- grite is the v0.5.3 release binary, its sha256 matching GitHub's digest. Building grite needs
  `openssl-devel`, which isn't installed. Its source HEAD is 0.5.3 plus docs and one display fix.

The probe scripts were one-offs in the session scratchpad.

**Side effect on zbook.** The first build attempt ran `/usr/bin/cargo` with `~/.cargo/bin` first on
`PATH`. Its rustup `rustc` proxy honoured Knots' `rust-toolchain.toml` and **installed toolchain 1.93.1
into `~/.rustup` (1.3 GB)**. Remove it with `rustup toolchain uninstall 1.93.1` (or fold it into
chz-if3). The retry used `PATH=/usr/bin:/bin RUSTC=/usr/bin/rustc`.

### Knots

| Test | Result |
|---|---|
| Speed | `new`, `ls`, `show` ~0.01 s; `sync` 0.07 s plain, 0.48 s over gcrypt |
| One private repo for several projects | **works with flat ref names**: `knots.remote=private`, `init --remote-ref refs/heads/knots-<project>`; two projects and a second host synced from one bare repo. A namespaced ref (`knots/proj-a`) **breaks sync**: its fetch maps to `refs/remotes/private/knots`, which collides with `.../knots/proj-a` |
| Code leaking into the issue ref | **yes by default**: `init` branches from code HEAD, so the private repo got the whole code history and the code files. **Workaround tested:** create an empty orphan `knots-<project>` ref in the private repo first; `init` adopts it and nothing from the code repo is pushed |
| Encrypted remote | **works**: `private = gcrypt::...`; push, no plaintext on the remote, a second host read it back |
| Concurrent edits, two hosts | converge after sync; the later title wins, the tag from the other host survives (last-writer-wins per field) |
| Atomic claims | 10 parallel `poll --claim` on 5 knots: 5 distinct claims, 5 refused, no doubles |
| Edges | any kind is accepted (`related` worked), so the vocabulary is free-form. **`blocked_by` does not filter `ready`/`poll`**: the dependent must be put in the `blocked` state, and Knots resumes it when the blocker finishes |
| Footprint | `.gitignore` edited (`/.knots/`), a `post-merge` hook, a local `knots` branch, `.knots/` (256 KiB). A daily GitHub release check (2 s timeout; `KNOTS_SKIP_DOCTOR_UPGRADE` disables it) |

### grite

| Test | Result |
|---|---|
| Speed | `create`, `list` ~0.01 s; `sync` 0.01 s |
| Footprint | writes `AGENTS.md` unless `--no-agents-md`; **auto-starts a background daemon** (`--no-daemon` per command; `daemon stop`) |
| Dependencies | `depends_on` cycle refused; `related_to` accepted; `dep topo` shows creation dates as "Dec 31, 69" (fixed after 0.5.3) |
| **Second host** | **failed.** A second clone gets `refs/grite/wal`, through `grite sync` or by fetching it before `init`, but materialises **0 issues**: `rebuild` reports 0 events and `show <id>` is `not_found`. Repeated on three fresh clones. Each WAL commit's tree holds only that commit's chunk. Maybe a usage error, but it follows the documented flow (`init`, `sync`) |
| Rebuild on the first host | counted 6 events, then `issue list` returned **0** while `show <id>` still worked (the list index is lost) |
| Cross-host locks | **work**: a lock acquired on host 1 and pushed blocks host 2 (`conflict: held by <actor> (expires in 595s)`) |
| Signing | `actor init --generate-key` creates a **new actor** (key: a 64-byte file, mode 600, in `.git/grite/actors/<id>/`); after `actor use`, new events are signed and `db verify` passes them. Earlier events stay unsigned and count as errors |

**Verdict.** Knots holds up in practice. It meets the goals (one private encrypted repo, merges,
atomic claims) once two things are configured: flat ref names and pre-created orphan refs. Its
`ready` doesn't use the dependency graph, though. grite fails its central promise in our test (a
second host sees nothing), so it's out until that's fixed upstream. Its locks and signing work, and
the design remains a good reference.

## henriquebastos/beans in practice (third pass, MH leans towards it for personal projects)

Everything below is read from the source (v0.7.0).

**Where the data lives.** `MAGIC_BEANS_DIR` selects **one** store, so it overrides a single project.
The consolidation mechanism is the **registry**:

- `~/.config/beans/config.json` maps a project's normalised git remote (or its path) to a store
  directory.
- `beans init` puts the store in `$XDG_DATA_HOME/beans/<project>`.
- One private repo for everything means each project's `store` points at `~/<issues-repo>/<project>`,
  or the repo is checked out at `~/.local/share/beans`.

What gets committed and what doesn't:

- The store's `.gitignore` keeps only `journal.jsonl`; the SQLite file stays out of git.
- **Nothing writes `journal.jsonl` automatically.** It's `beans export-journal > journal.jsonl` by
  hand, so a commit wrapper or timer has to do it.

**Migration from beads.** Possible, but not a one-command job:

- **Ids.** `ID_PATTERN` is `^[a-z]+-[0-9a-f]+$`, and beads ids are base36 (`chz-47g` contains a `g`).
  So **existing ids are rejected**: migrated beans need new ids, with the old one kept in `ref_id`.
- **References.** Every reference to a bead id has to be rewritten: in other beans, in bd-track
  events, in ticket `outcome:` lines, and in docs and commit messages. Without that, history loses
  its links.
- **Converter.** A converter is about 100 lines: read `bd export` JSONL, write journal `create` and
  `dep_add` entries, then `beans rebuild`.
- **What's lost.** Labels, notes, statuses other than open/in_progress/closed, and every edge type
  except `blocks` and `parent`.

**Merging two hosts.** `rebuild` replays a journal with plain INSERTs. Concatenating two hosts'
journals fails on the second `create` of a bean (primary key), and the journal rows are whole-bean
snapshots. There's no merge; one host at a time, or a fork adds a merge rule.

**Time tracking without labels.** bd-track uses labels only to resolve the billing tuple
(`.beads/bd-track.yaml`: a `case:` label, then label patterns, then the project default).

- For personal projects the tuple is empty, so labels don't matter there.
- **Per-project default.** The sidecar `default:` block (already exists) covers a project billed as
  one unit.
- **Type.** Custom bean types (`beans types add`), with pattern rules matched on `type:` instead of
  labels.
- **Parent.** The tuple is inherited from the epic (`parent_id`): one tuple per epic.
- **Tags on the interval.** bd-track's events already carry their own `tags`. Tags given at `start`
  live in bd-track, not the tracker.

**Forking to add labels and edge types.**

- **Labels.** Upstream added labels in 0.6.0 and **dropped them** in schema v2 ("defer to phase 8";
  phase 8.5 of its build plan lists labels again). So ask upstream first; a fork that re-adds them
  diverges on purpose. The work: a `labels` JSON column (or table), journal snapshots carrying it,
  `label add/remove`, and `--label` filters on `list` and `ready`. Small, maybe half a day with tests.
- **Edge types.** The `dep_type` column already exists and `dep add --type` is already accepted.
  But the primary key is `(from_id, to_id)`, so a pair can carry only one edge, and `ready` filters
  on `blocks`. The work: the key becomes `(from_id, to_id, dep_type)`, plus removal and display by
  type.
- **Also needed for us.** Relax `ID_PATTERN` (migration), add statuses (`deferred`, `blocked`), and
  notes. All small.
- **Total.** Roughly one to two days, in MH's language, for a 1.7k-line codebase. The lasting cost is
  tracking upstream.

## Five more tools (MH's list, screened from the source)

| | kata (`kenn-io/kata`) | epiq (`ljtn/epiq`) | ticks (`pengelbrecht/ticks`) | Backlog.md (`MrLesk/Backlog.md`) | TrackDown (`mgoellnitz/trackdown`) |
|---|---|---|---|---|---|
| Model | issue ledger: claim, close with evidence, threaded comments with confirm/refute/supersede verdicts | **kanban board** (boards, lanes, tickets), event-sourced; replay | beads-like issues + epics + gates | Markdown tasks + kanban, milestones, **docs and decisions** | all issues in **one Markdown file** + a roadmap file |
| Storage | **one SQLite under `KATA_HOME` (`~/.kata`) for every project**; the repo holds only `.kata.toml` | per-user JSONL logs on a state branch, checked out at `~/.epiq-global/worktrees/<id>`; `.epiq/project.json` in the repo | one JSON file per issue in `.tick/issues/`, always at the git root (the screening's `TICK_DIR` doesn't exist in 0.32.0; chz-vkf) | Markdown in a **project-relative** folder (`backlog/`); `--no-git` for a standalone folder | that file on a `trackdown` branch, commit hook |
| Edges / ready | parent, related, blocks/blocked-by, duplicate-of; `ready`, `next`, `inbox` | parent node, links; **no blocking deps, no ready** | `blocked_by`, `parent`, `discovered_from`, `after`; `ready`, `next` | dependencies, milestones | none |
| Statuses, labels | open/closed + claim ownership; labels | lanes; tags, assignees | open/in_progress/closed + `defer_until`; labels, notes, `external_ref`, acceptance criteria | configurable list; labels | free text |
| Multi-host | **not via git**: an opt-in remote daemon or federation (Postgres optional) | **git**: one log file per user, deterministic replay (ULID + parent "edge" event), later event wins | **git**: different issues are different files; a **field-by-field three-way merge driver** for the same issue | git (Markdown files in the repo) | git; one shared file, so concurrent edits conflict |
| Background process | local daemon, auto-started, idle timeout | GUI server on demand | none | web UI on demand | commit hook |
| Agent extras | MCP, `KATA_TEAMMATE` identities, `init --with-agents` opt-in, cron and workflows | MCP with per-agent identity, skill | owner scoping (`tk ready` shows yours), skill, **beads importer** | MCP, `AGENTS.md` | none |
| Beads import | **`kata import --source-format beads`** | no | **yes** (`internal/beads`) | no | no |
| Size, adoption | Go 25 MiB, 520★, created 2026-04, pushed daily | TypeScript 4.3 MiB, 584★, pushed daily | Go 1.7 MiB, **10★**, last push 2026-10-07; binary **named `tk`** (clashes with wedow's tk) | TypeScript 5.6 MiB, **7.4k★**, active | shell, 1.6k lines, 38★, since 2015 |
| Licence | MIT | MIT | MIT (ticfac: none, 0★) | MIT | GPL-3.0 |

Quick verdicts (screening, not tested):

- **kata.** Closest to MH's goals for one person and many agents. It keeps all projects' issues
  outside the repos, has rich relations and an evidence model, and imports from beads. The costs: a
  25 MiB Go service with a daemon, and multi-host sync that means running a daemon, not git. That's
  the opposite bet from git-based tools.
- **ticks.** The best **data-model fit** for what we use today: labels, notes, deferral,
  `discovered_from`, `external_ref`. It has a beads importer and a real three-way merge driver.
  Tiny adoption.
- **epiq.** A board, not a dependency tracker; it can't replace beads. Its sync design is the
  interesting part (below).
- **Backlog.md.** The most adopted by far. It is a project's in-repo planning record (tasks, docs,
  decisions, milestones), reviewable in PRs, which suits public repos where the plans *should* be
  public. It isn't for private notes.
- **TrackDown.** One file for all issues: worse than `ticket` for an inbox.

### epiq's architecture compared

- **Where the state lives.** epiq keeps it on a **dedicated branch of the project's own repo**,
  checked out as a **worktree outside the project** (`~/.epiq-global/worktrees/<id>`). The code
  checkout never sees issue files, and its branch switches never touch them. That's the same idea as
  Knots (a `knots` branch in a worktree) and close to grite and git-bug (a ref with no checkout). beads,
  ticks, tk and Backlog.md keep files in the worktree; kata and henriquebastos/beans keep them outside
  git.
- **What it makes easier.**
  - Sandboxes: an agent's sandbox can mount the code checkout read-write and the state worktree
    separately, or not at all.
  - Code branches and PRs stay clean.
  - Git worktrees for parallel agents all share one state worktree, so there's no per-worktree
    copy to reconcile. That's the problem ticks solves with a merge driver.
- **What it complicates.**
  - The state branch is pushed to **`origin`, hard-coded** (`git-constants.ts`). In a public repo,
    every ticket is published. That rules it out for private notes unless that constant changes.
  - Global state in `~/.epiq-global` is one more directory to back up and to keep out of sandboxes.
  - A per-project worktree has to be repaired when a repo moves.
- **"Local-first with eventual consistency" in the code.**
  - Every edit is applied locally and appended to the editing user's own JSONL file.
  - Sync is `pull --rebase` then `push` of the state branch. Users write different files, so git
    never sees a conflict.
  - State is rebuilt by replaying the union of all files in a deterministic order: ULIDs plus a
    reference to the last event the writer had seen.
  - **Conflicting concurrent edits: the later event wins, and the earlier one stays visible only
    in the log.** Once every host has synced, all replicas replay the same events in the same order
    and converge.
  - It's the same rule as bd-track's event log (one writer per file, union fold) and grite's CRDT,
    and weaker than ticks' field-level merge for two edits to the same field.
  - The same user on two machines writes the same file. A pending-log mechanism handles that (read,
    not tested).

## Hands-on: kata, ticks, beans (chz-vkf, 2026-11-13)

**Setup.** `tools/tracker-trial run` (one command, ~1.5 min; [../../tools/README.md](../../tools/README.md)). Each
tool runs in its own sandbox: two "hosts" with their own `HOME`/XDG dirs, bare repos for code and a private remote
(plain and `gcrypt::`), a throwaway GPG key, and code repos with real history and a marker string to catch code leaking
into the issue store. Versions:

- kata 0.23.0 and ticks 0.32.0: release binaries, sha256 matching GitHub's digests.
- beans: magic-beans 0.7.0 via pipx.

Knots was not rerun in the harness; its numbers are from the earlier hands-on above. Raw results:
`~/.cache/tracker-trial/results.md` after a run.

How each tool's store was set up for tests 3-5:

- **kata.** The daemon's SQLite under `KATA_HOME`, which holds all projects. The git variant tested: stop the daemon,
  snapshot `kata.db` into the private repo, merge, copy back. kata's own multi-host answer is a shared remote daemon
  (`KATA_SERVER`) or federation, which was not tested.
- **ticks.** The store is always `<git root>/.tick`, so one private repo holds a single `.tick` store and projects
  become labels. Sync is commit, pull (merge driver), push.
- **beans.** The private repo is checked out at `$XDG_DATA_HOME/beans`, and the registry maps each project there. Sync
  is `export-journal`, commit, pull, push, then `rebuild`.

| Test | kata | ticks | beans |
|---|---|---|---|
| 1 Footprint in the repo | `.kata.toml` + a `.gitignore` line | `.tick/`, `.gitattributes`, 4 merge-driver keys in `.git/config` | none |
| 1 Footprint outside | `KATA_HOME` (db, hooks, runtime keys); **daemon left running** (auto-started); unix socket in `$XDG_RUNTIME_DIR/kata/` | `~/.config/tk/update-cache.json` | registry `~/.config/beans/config.json`, store dir |
| 1 Network | none | **synchronous GitHub release check on the first command each 24 h** (`api.github.com`; no opt-out; `tk version` always checks) | none |
| 2 Speed (median, ms): create / list / show / sync | 26 / 27 / 29 / 149 (daemon warm) | 22 / 18 / 21 / 67 | **182 / 178 / 173 / 216** (Python start-up) |
| 3 One private store, 2 projects, outside the worktrees | **yes, built in** (`KATA_HOME`, all projects; `list --all`) | only as one shared store with project labels (no `TICK_DIR` in 0.32.0, despite the screening note) | **yes, built in** (registry by git remote) |
| 3 Code in the private remote | no | no | no |
| 4 gcrypt remote: push, second host reads, plaintext | yes / yes / none | yes / yes / none | yes / yes / none |
| 5 Two hosts edit one issue | **binary conflict in `kata.db`**, no merge | **merged per field**: later title wins, both labels kept, converged | documented flow: **issue lost** (below); append workaround: converged, but **h2's field edit lost** (whole-bean snapshots) |
| 6 10 parallel claims on 5 items | 5 ok / 5 refused, no doubles | **10 / 0: all 10 "succeed"** (claim = `update --status in_progress --owner`, no check) | 5 ok / 5 refused, no doubles |
| 7 Import of this repo's beads (84 issues; `bd ready` = 11) | 84 issues; **all 98 edges become `blocks`** (related, parent-child, discovered-from); deferred/in_progress become labels; **notes lost**; labels kept; `ready` = 9 | **closed issues skipped** (26 of 84); `related` and edges to closed issues dropped; deferred → open (date lost); notes and labels kept; **fails on the memory record** (needs an issues-only file); `ready` = 22 | no importer; jq converter (in the harness): 84 issues, `blocks` + parent kept; **labels have nowhere to go**; deferred → open; notes appended to the body; `ready` = 20 |
| 8 `ready` hides a blocked item, shows it after the close | yes, yes | yes, yes | yes, yes |
| Edge types | blocks, parent (no gating), related, duplicate-of | blocked_by, parent, discovered_from, after (soft); no related | blocks, parent_id (one edge per pair) |

**Findings that change the screening.**

- **beans' journal loses data in its own documented flow.** `rebuild` replays into the tables but not into the
  journal table: after a rebuild, `export-journal` holds 0 rows (confirmed by hand, 2 beans). The next host that
  exports and commits therefore overwrites `journal.jsonl` without the `create` entries. In test 5 the bean vanished
  on h1, and h2 hit a journal conflict.
  - The workaround the harness tests: append each export, `merge=union` on the journal, replay. It converges, but every
    journal row is a whole-bean snapshot, so the host that syncs last overwrites the other host's field edit.
- **ticks' claims are not exclusive.** There's no claim command. `update --status in_progress` is idempotent and
  ignores the current owner (`cmd/tk/cmd/update.go`). That's fine for `/work-queue` (a single writer), and wrong for
  swarms (goal 5).
- **ticks' merge driver** lives in `.git/config`. A fresh clone lacks it until the first `tk` command, which
  re-registers it (`CheckAndInstallMergeDrivers` runs on every command). A `git pull` before any `tk` command would
  text-merge the JSON.
- **kata's SQLite in git is not a sync method.** Two hosts give a binary conflict. A plain `cp` right after
  `kata daemon stop` sometimes missed the last writes, which were still in the WAL; the harness uses `sqlite3 .backup`.
  Multi-host kata means one daemon that both machines talk to.
- **kata's beads importer drives a live `bd`** (not the JSONL): it needs the export restored into a scratch bd first.
  It maps every dependency to `blocks`, so `related` (37 here) starts gating `ready`.

**What migrating this repo's 84 beads would lose.**

- **kata.** Bd notes, all edge types (they would need re-typing by hand, or an own importer through `kata create
  --related/--parent`), and the deferred status (kata has `schedule`/`someday` instead).
- **ticks.** The 58 closed issues (history), `related` edges, deferral dates and memories. The issue ids change.
- **beans.** All labels and every edge type except `blocks` and parent. Notes go into the body, and all ids change
  (base36 ids fail `ID_PATTERN`).

**Verdicts.**

- **kata.** The strongest tool: rich relations, atomic claims with TTL, labels, comments, an all-projects store outside
  the repos, JSONL export, active (daily pushes). The cost is a daemon and its socket, plus multi-host through a shared
  daemon rather than git, so goal 4 (git merges) is out by design. The importer is lossy enough that an own import
  script (about 84 `kata create` calls with the right relation flags) would be needed, or a fresh start.
- **ticks.** The best git story (a field-level merge that actually worked) and the closest data model to beads. But
  it has no out-of-tree store, non-exclusive claims, an unasked network call, 10★, and a lossy import (skips closed
  issues). Not adopted.
- **beans.** Out. Too thin (no labels or notes, 3 statuses), the slowest, and its sync loses data unless wrapped.
  Forking it (planned above at one to two days) would now also mean fixing the journal, so it's no longer small.

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
2. **Live tests done (chz-vkf): no finalist replaces beads outright.** Every one fails at least one of
   MH's goals or R1-R5:
   - kata fails git merges (goal 4).
   - ticks fails the out-of-tree store (goal 3) and exclusive claims (goal 5).
   - beans fails merges, labels and notes, and loses data in its own sync flow.
   - Knots' `ready` ignores the dependency graph and it imposes a fixed workflow.

   **Recommendation: kata**, if anything replaces beads. It has the best data model, atomic claims, an all-projects
   store outside the repos, and active development. The price is a daemon, plus a second host through a shared
   daemon instead of git. If git-based merges between hosts are a hard requirement, nothing tested qualifies:
   **keep beads**.
3. **One-week trial (chz-8fp, MH) of kata, not a migration.** Do it on a new or small private project, starting fresh,
   not through kata's importer. Pass/fail against R1-R6:
   - Map our flows onto kata: `/work-queue` park as `schedule`/`someday` (R3); memories (R5) as a docbank file or a
     plain Markdown file.
   - Measure the daemon's cost: memory, start-up after a reboot, a stale socket after a crash.
   - Try `KATA_SERVER` from the second machine against the zbook daemon, the multi-host path tested nowhere yet.
   - Note what `/work-queue` and bd-track would need (a backend behind `show`/`list`/`update`).
   - Log every place kata was slower or clumsier than bd.
   - If the trial passes, migrating this repo needs an own import script (edge types, notes) instead of
     `kata import --source-format beads`.
4. **Ticket inboxes stay files (D72); git-bug is not adopted.** It replaces only the inbox, which works.
   It would also put tickets inside target repos and need private remotes for public projects. Revisit
   if tickets should mirror GitHub Issues (git-bug's bridges are its real advantage).
5. **bd-track's event log in git refs** is a candidate transport for D71, filed as a design note there
   and not built now.
6. **Out:**
   - beads_rust (licence rider).
   - grite (second clone sees no issues, 0.5.3).
   - henriquebastos/beans (sync loses data, no labels or notes).
   - ticks (non-exclusive claims, no out-of-tree store, unasked network call).
   - epiq and TrackDown.

   tk stays a fallback. Backlog.md is a separate question (chz-1rs).

### Trial project

The section below was written for a tk trial (first pass). kata keeps its data outside the repo (only
`.kata.toml` is committed), so the "private, so the data can be committed" point no longer matters. Any active
private or personal project where MH tracks this week's real tasks will do, with a fresh kata project instead of an
import.

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
