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

### Wider search (MH asked for a double check)

The reviewer's shortlist holds up. Nothing else found beats tk on simplicity or beads on features.

| Tool | Notes | Verdict |
|---|---|---|
| **beans** (`hmans/beans`) | Apache-2.0, Go, Markdown in `.beans/` + `.beans.yml`, CLI/TUI/GraphQL, `beans prime` hooks for Claude Code. Confirmed: "still under heavy development", not accepting contributions. Dependencies not documented. | Closest rival to tk, but heavier and less stable. |
| **git-issue** (`dspinellis/git-issue`) | GPL-3.0, shell, `.issues/` as its own git repo, with weights, estimates, **time spent**, milestones and two-way GitHub/GitLab sync. Confirmed: no dependencies. | No dependencies, so out. MH already has a fork in `~/Source/antimike/git-issue`. |
| **grite** (`neul-labs/grite`) | Reported (author's post): CBOR events in `refs/grite/wal`, last-write-wins plus set CRDT, a sled cache, TTL locks, `link ... blocks`. | Too new to adopt; relevant to the architecture question (below). |
| **git-bug-agent** (`selesy/git-bug-ax`, `gba`) | Confirmed: adds status, priority, `blocks`, `parent` and claims to git-bug as prefixed fields. 0 stars, no licence. | Shows how much has to be built on top of git-bug to get beads. |
| kata, epiq, thicket, ticks, bodega, kticket, Backlog.md | Seen in search results only; not read. | Unverified. |

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
