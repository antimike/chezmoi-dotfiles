# Beads (bd) Cheat Sheet -- long-form reference

Comprehensive command reference. The short "Beads (bd) Gotchas" section in `~/.claude/CLAUDE.md` is the always-on summary; this file is the on-demand expansion. Long-form details and rationale for individual gotchas live in `bd memories <keyword>` entries (search by keyword) -- this file lists which memories are worth pulling when.

## Common commands

### Finding work

- `bd ready` -- show issues with no active blockers (open + dependencies resolved). The default "what should I work on" query.
- `bd list --status=<s>` -- filter by status (`open`, `in_progress`, `blocked`, `deferred`, `closed`, plus any custom statuses defined via `bd config set status.custom`).
- `bd list --label=<l>` / `--label-pattern=<glob>` / `--label-any=<l1,l2>` -- AND, glob, OR matching on labels.
- `bd show <id>` -- full detail including description, dependencies, parent, children. Add `--with-context` (via `/show` slash command) to also pull recent memories matching the title.

### Creating and updating

- `bd create "<title>" --type=<t> --priority=<0-4|P0-P4> --parent=<id> --labels=<csv> --description=<text>` -- minimum-friction issue creation.
  - `--body-file=<path>` reads description from a file (cleaner for long descriptions; sidesteps quote-escaping).
  - `--silent` emits just the bead ID on stdout -- useful for scripting (`ID=$(bd create ... --silent)`).
  - `--external-ref=<url>` adds the Jira/GitHub/etc link.
- `bd update <id> --status=<s>` -- transition status.
- `bd update <id> --append-notes "<text>"` -- append to the bead's running notes with newline separation. Use for in-bead state evolution (e.g., "2026-05-20: blocked on X resolved, resuming"). Distinct from `--description` which replaces.
- `bd update <id> --claim` -- atomically set assignee to current user + status to in_progress. Idempotent.
- `bd update <id> --add-label / --remove-label / --set-labels` -- label mutations (note: not the same flag shape as `--labels` on `create`).
- `bd close <id> [--reason="..."]` -- mark complete. Reason is captured in the close event.

### Deferring and reactivating

- `bd defer <id> [--until <date>]` -- hide from `bd ready` until the specified date (or indefinitely if no `--until`). Date formats: `+1d`, `+2w`, `tomorrow`, `next monday`, `2026-06-01`.
- `bd undefer <id>` -- restore a deferred bead to `open`.
- **Gotcha**: `bd defer` is distinct from `bd update --status=deferred` -- the former is a richer "snooze" mechanism with a wake date; the latter just sets the status string. Prefer `defer` unless you specifically need the status value for filtering.
- **Gotcha**: `bd-track queue clean` removes both `closed` AND `deferred` beads from queues. If you want a paused bead to survive auto-clean while waiting on something, use status `blocked` instead of `deferred`. (See bd memory `beads-dir-envvar-contamination` for the unrelated env-var issue.)

### Memory store

- `bd remember "<slug>: <body>"` -- persist a project-technical fact. Stored in the project's `.beads/` (travels with the repo). Auto-injected at `bd prime` time. Slug should be kebab-case-with-hyphens and descriptive.
- `bd memories <substring>` -- search slugs by substring. Add `--json` for full bodies.
- **What to remember**: pitfalls, naming conventions, environment quirks, non-obvious tool behavior. NOT in-flight task state (use beads) or user preferences (use auto-memory).

### Dependency graph

- `bd link <id1> <id2> --type <T>` -- general edge creation. Types: `blocks` (default), `tracks`, `related`, `parent-child`, `discovered-from`.
- `bd dep add <id1> <id2>` / `bd dep <id1> --blocks <id2>` -- shorthand for `bd link --type blocks`. Two flag orientations (`--blocked-by`, `--depends-on`) are aliases that mean the same thing.
- `bd dep remove <id> <depends-on-id>` -- remove ANY edge type between two beads (not just blocks).
- `bd dep list <id>...` -- show OUTBOUND edges from each bead (what does it depend on). Does not show inbound edges in this command; use `bd dep list <other-id>` and look for `<id>` in the output.
- `bd dep cycles` -- detect dependency cycles across the project.
- **Directed edges**: even conceptually-symmetric types like `related` are stored as directed edges. To make a relationship visible from both sides, add both directions explicitly.

### Scripting

- `--silent` (on `create`, `update`, `close`) -- minimal stdout, errors still go to stderr. Useful in shell pipelines.
- `--json` -- machine-readable output for `list`, `show`, `memories`, `config show`, etc.
- `--actor "<name>"` -- override the recorded actor name (default: git user.name or $BEADS_ACTOR). Useful when scripts are run by automation but you want the audit trail to attribute correctly.
- `BEADS_ACTOR` env var -- same effect as `--actor`, applied to all commands in the shell.

## Custom statuses

Configure via `bd config set status.custom "<comma-list>"`. Each entry is `<name>` (defaults to `wip` category) or `<name>:<category>`.

Categories (workflow stages):

- `active` -- ready / available for work (sibling of built-in `open`)
- `wip` -- in flight (sibling of built-in `in_progress`)
- `done` -- complete (sibling of built-in `closed`)
- `frozen` -- on hold / deferred (sibling of built-in `blocked` / `deferred`)

Status name regex: `[a-z][a-z0-9_-]*` (lowercase only, letter-first, hyphens and underscores OK, no spaces, no caps). Hierarchical-feeling names require hyphens: `review-local:wip`, `review-pr:wip` -- the colon does NOT separate sub-names.

bd-track sidecar mirroring: `~/.config/bd-track/repos.yaml` has `repos[].statuses` as a free-text array. Keep it aligned with bd's `status.custom` (minus the `:category` suffix) so `bd-timew` recognizes the same status names.

## Dependency edge type semantics

| Type | Use when |
|---|---|
| `blocks` | Hard dependency. The blocker must close before the blocked bead can proceed. Counts toward `bd ready` filtering. |
| `tracks` | Soft monitoring. Bead A tracks bead B when A's content is affected by B's status (e.g., A documents a gap that B's completion eliminates). A is interested in B's transitions without being blocked by them. |
| `related` | Loose semantic association. The two beads touch the same code, share a design, or are companion edits across PRs. Discoverable on both sides when explicitly added bidirectionally. |
| `parent-child` | Hierarchical. Child beads aggregate under a parent (epic, multi-step task). Parents don't close until children close. Children show under the parent in `bd show <parent>`. A bead has at most one parent. |
| `discovered-from` | Surfaced while working on another bead but otherwise independent. Lighter than `parent-child` -- no closure dependency. Useful for "I noticed this while doing X" follow-ups that don't block anything. |

### Node-type rule for `blocks` edges

Blocking edges have a node-type constraint:

- task blocks task -- OK
- epic blocks epic -- OK (verified: a "manual config" epic blocking a "pipeline" epic works)
- epic blocks task -- **REJECTED** with `Error: tasks can only block other tasks, not epics`

So you cannot express "task X depends on the completion of epic E" with `bd dep E --blocks X`. Instead, block X on the **terminal leaf task** of E's internal dependency chain -- the deepest node that everything else in E feeds into. That leaf closing is the practical proxy for "E is done."

Memory: `bd-blocking-edge-epic-task-constraint`.

### Dependency hygiene (the standing practice)

When you work on a cluster of related beads -- creating, reviewing, or restructuring them -- discover the relationships between them and formalize each as a graph edge. **When in doubt, add the edge.** Rationale:

- Prose-only relationships ("X depends on Y", written in a bead description) are invisible to `bd ready`, `bd dep list`, and `bd dep cycles`. They do not gate readiness, do not show in dependency listings, and do not participate in cycle detection. A relationship that only lives in text is, operationally, not a dependency at all.
- The cost of a spurious edge is low (it's easy to `bd dep remove`); the cost of a missing edge is high (work gets picked up out of order, or a blocker is missed). Asymmetry favors more edges.
- Use the right edge type: `blocks` for hard ordering, `tracks` for "A cares about B's state", `related` for companion work, `parent-child` for aggregation, `discovered-from` for incidental follow-ups.
- After restructuring a cluster, run `bd dep cycles` to confirm no loop was introduced.

This is a standing instruction (also captured inline in `~/.claude/CLAUDE.md`), not a one-time setup step.

## Common pitfalls

### `BEADS_DIR` environment-variable contamination

`BEADS_DIR` exported from one project's `.envrc` leaks into shells that have cd'd through that direnv and silently overrides bd's cwd-based auto-discovery in other projects. Symptoms: bd commands from project B return project A's beads.

Fix: do NOT export `BEADS_DIR` from any project's `.envrc`. bd's cwd-walking auto-discovery works correctly when the variable is unset. If contaminated: `unset BEADS_DIR BEADS_DOLT_PASSWORD`. Same issue affects `BEADS_DOLT_PASSWORD`.

Memory: `beads-dir-envvar-contamination`.

### Custom-status colon collision

The colon in `<name>:<category>` is bd's category separator. So `review:local` is parsed as `status=review, category=local` and rejected (category must be `active|wip|done|frozen`). For hierarchical-feeling names use hyphens: `review-local`, `review-pr`.

Memory: `bd-custom-status-syntax-and-validation`.

### Directed edges for symmetric relationships

`bd link A B --type related` only shows B on A's dep list, not vice versa. Add the reverse edge for full symmetry: `bd link B A --type related`.

Memory: `bd-link-edge-types-and-syntax`.

### Dependency edge removal

`bd dep remove <id> <depends-on-id>` removes whichever edge exists between two beads, regardless of edge type. There is no per-type remove flag.

### Slow bd commands

Journal / commit-history bloat in the embedded Dolt store. Fix: `bd compact --days 7 --force && bd gc --skip-decay --force`. Nuclear: `bd flatten --force && bd gc --skip-decay --force`. Add a daily maintenance cron for active projects.

### Memory entries vs auto-memory

- `bd remember` -- project-technical facts; lives in `.beads/`, auto-injected at prime time, shared across machines that clone the repo.
- Auto-memory (`~/.claude/projects/<project>/memory/`) -- user preferences, collaboration feedback, cross-project user facts; loaded on-demand via the `MEMORY.md` index.
- Don't duplicate. If the fact is about how the project works, bd remember. If it's about how the user wants to work, auto-memory.

## Maintenance

This reference is intended to evolve. When non-obvious bd functionality requires research or experimentation to verify (e.g., I had to test that `related` edges are directed; the user had to point out that `bd link` accepts non-blocks types), capture the finding in two places:

1. **Add a one-line gotcha** to the "Beads (bd) Gotchas" section in `~/.claude/CLAUDE.md` if the finding is something a future session would benefit from seeing always-on.
2. **Expand the relevant section here** with the long-form rationale, examples, and edge cases.
3. **`bd remember`** the underlying technical fact, with a slug that this reference can point at (`Memory: <slug>` line under the gotcha entry).

If a finding is purely about one project (e.g., one project's specific label taxonomy), put it in that project's CLAUDE.md or a project-local memory file instead. Global reference is for multi-project conventions.

Source of truth for this file: `~/.local/share/chezmoi/dot_claude/references/beads-cheatsheet.md`. Edit there, then `chezmoi apply` or copy to `~/.claude/references/beads-cheatsheet.md`.
