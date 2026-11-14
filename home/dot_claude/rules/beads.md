# Beads (bd)

Always loaded (no `paths:`): `bd` is driven by commands, so no file read would trigger a path-scoped rule, and several of these guard against data loss.

## Network ops

- Do NOT run `bd dolt push` as part of session-end automation, cleanup, or checkpointing. The Dolt-side push is the user's responsibility to run interactively when convenient.
- The JSONL state (the human-readable issues export) IS pushed via plain `git push` from the project's `.beads/` directory. That's small, fast, and adequate for cross-session visibility into bead state.
- This convention exists because `bd dolt push` can stall on transient network issues (LSO bugs, PMTU blackholes, TCP metrics cache poisoning — see project pitfall docs); blocking session-end on it is unacceptable. The JSONL push is reliable; the Dolt push is best-effort.

## Performance

- **Slow `bd` commands** (5-30s): caused by journal bloat or commit history growth in the embedded Dolt store. Fix: `bd dolt commit; bd compact --days 7 --force && bd gc --skip-decay --force`. Nuclear reset: `bd dolt commit; bd flatten --force && bd gc --skip-decay --force`. **Always `bd dolt commit` first** before a raw compact/flatten (`bd-track cleanup` >= 0.10.1 commits first and aborts if that fails; never pass it `--no-commit`): compact/flatten discard uncommitted changes under `dolt.auto-commit batch` (a whole triage session lost, 2026-11-05). See `~/.claude/references/beads-performance.md`.
- **New project setup**: always run `bd config set dolt.auto-commit batch` and `bd config set no-push true` after `bd init`. Add the daily maintenance cron (commit + compact + gc). Details in the reference file.

## Gotchas

**Dependency hygiene (standing practice)**: whenever you work on a cluster of related beads -- creating, reviewing, or restructuring them -- actively discover the relationships between them and formalize each as an edge via `bd link` (`blocks` / `tracks` / `related` / `parent-child` / `discovered-from`) or `bd dep` (`blocks`). Err on the side of more edges, not fewer: **when in doubt, add the edge.** Prose-only relationships are invisible to `bd ready`, `bd dep list`, and `bd dep cycles`. After any cluster restructure, run `bd dep cycles` to confirm no loop was introduced.

One-line gotchas (detail in cheatsheet — see end of section):

- **Edge types beyond `blocks`**: `bd link <a> <b> --type <T>` accepts `blocks` / `tracks` / `related` / `parent-child` / `discovered-from`; `bd dep add/remove` only handles `blocks`. Edges are directed even for symmetric types.
- **Node-type rule for `blocks`**: epic↔epic OK; epic→task **rejected**. To make a task depend on an epic, block it on the epic's terminal leaf task.
- **Custom statuses**: `bd config set status.custom <comma-list>`; entry shape `<name>` or `<name>:<category>`; name regex `[a-z][a-z0-9_-]*`. Mirror to the project's `beads.statuses` in `~/.config/projects.yaml` without the category suffix.
- **`.envrc` and `BEADS_*`**: never export `BEADS_DIR` from an `.envrc` (it leaks into other projects' shells and silently points `bd` at the wrong database). Export `BEADS_DOLT_PASSWORD` only in server-mode projects and only from a credential command (today `pass`), never a literal; embedded projects omit it. If contaminated, `unset` them. Rule and target design: project-registry D22-D26 (`~/.local/src/project-registry/docs/decisions.md`).
- **Dependency edge removal**: `bd dep remove <id> <depends-on-id>` removes whichever edge exists between two beads regardless of type.
- **`bd init` commits and adds a Dolt remote**: it commits `.beads/` to the outer repo and makes git `origin` a Dolt remote (`sync.remote`). `bd config set` stops committing once `no-git-ops` is set; `bd config unset` commits anyway. For a public repo: `bd config set no-git-ops true`, `bd dolt remote remove origin`, `bd config unset sync.remote`, gitignore `.beads/`, then `git reset` (mixed) over bd's commits and check `git log`.
- **Searching memories**: `bd memories <substring>` matches slugs; add `--json` for full bodies. Cheap — reach for it before guessing bd syntax. **Note**: bd memories are per-project; slugs only resolve inside their originating project.

**Maintenance**: when new bd findings turn up, add a one-liner here (`~/.claude/rules/beads.md`) if broadly useful and expand `~/.claude/references/beads-cheatsheet.md`.

**Full reference**: `~/.claude/references/beads-cheatsheet.md`.
