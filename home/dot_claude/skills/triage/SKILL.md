---
name: triage
description: Processing a project's ticket inbox (D72) with MH — read the open tickets, batch clarifying questions for vague ones, decide each one (accept, reject, duplicate, already done), turn accepted tickets into beads (label `triage`) or docs, and move handled tickets to done/ with status, resolved and outcome. TRIGGER on `/triage`, "process the inbox", "go through the tickets", or when a SessionStart notice reports open triage tickets and MH asks to handle them. For filing a ticket, use the `triage-file` skill instead.
author: Michael Haynes
scope: global
tags: [triage, tickets, beads]
timestamps:
  - action: created
    at: 2026-10-29T19:50:00-05:00
    actor: Claude (chezmoi session, bead chz-8o0.4)
  - action: edited
    at: 2026-11-02T12:00:00-06:00
    actor: Claude (chezmoi session, bead chz-bi3)
    note: steps 1 and 4-6 use `bd-track triage` where installed; the manual steps are the fallback
comments:
  - "Source: chezmoi D72 (ticket inboxes for every project). Companion of triage-file."
---

# /triage — process this project's ticket inbox

Arguments: optional project name (default: the current repo's project, from the registry
`~/.config/projects.yaml`).

The inbox is `~/.local/state/triage/<project>/`: open tickets in `triage/` (one file each),
quick notes in `triage/inbox.md` (one per paragraph), handled tickets in `done/`. Tickets may
have a frontmatter (`from`, `date`, `type`, `urgency`, `status: open`) or be free-form; both
are valid. The inbox is not a git repo: moves are plain `mv`, so be careful with them.

**MH decides.** You propose a disposition for every ticket; nothing becomes a bead, a doc edit
or a done/ file before MH agrees. Under an unattended run (no MH), stop after step 2 and leave
the proposals for MH.

## Tools: `bd-track triage`, else by hand

Where `bd-track triage --help` works (bd-track >= 0.6.0; spec in bd-track's `docs/triage.md`),
it does the bookkeeping: it lists tickets with ids, creates the bead, writes the frontmatter and
moves the file to done/. Use it, as below. Without it, do the same by hand (the "Fallback"
lines). Either way the decisions and the bead text are yours and MH's.

- It works on the inbox of the current git repo. For another project, add
  `--project-dir <clone>` (where beads are created; the registry gives the path), or
  `--inbox ~/.local/state/triage/<project>` for a project without a clone here.
- Every action takes `--dry-run`: use it the first time on an unfamiliar inbox.
- `ticket --list` stays the quick overview (MH, 2026-11-02); the split between `ticket` and
  bd-track is bd-track's decision.

## 1. Read the inbox

```bash
ticket --list ${project:+-p "$project"}    # overview: open tickets + quick-note count
bd-track triage list                       # ids for steps 4-6 (one per quick note too)
bd-track triage list --json                # full bodies and frontmatter, if you prefer
```

Fallback: `ticket --list`, then read the files in `triage/` and `inbox.md` directly.

Read every open ticket and every quick note in full. Note who filed each one (`from`) and its
date: an agent's ticket may describe state that has since changed.

## 2. Assess and propose

For each ticket, check it against the project before proposing anything:

- **Already done?** Search the code, `git log`, the docs and (if the project uses beads)
  `bd search` / `bd list`. A ticket whose ask is already met is `done`.
- **Duplicate?** Of an open bead, a docs open item, or another ticket in the inbox: `duplicate`,
  with what it duplicates. Merge any new detail into the original.
- **Superseded?** A later ticket from the same filer may replace part of an earlier one (a
  newer version pin): fold the parts into one bead and say so in both outcomes.
- **Clear enough to act on?** If not, it needs a question (step 3).
- **Worth doing here?** If it belongs in another project, propose re-filing it there
  (`triage-file`); if it is not wanted, propose `rejected` with a one-line reason.
- **Accept**: what it becomes (step 4), with type and priority.

Present one table: ticket, filer/date, your reading in one line, proposed disposition, and the
questions you need answered. Distinguish what you checked from what you assume.

## 3. Clarify (batched)

Ask all questions in one round, not one per ticket: AskUserQuestion takes up to four questions
per call, so group them; past that, list them in one message. MH may answer with a question of
their own: answer it (check the code first) and ask again rather than guess. A question the
filer has to answer (another project's session, an agent) cannot be answered here: leave that
ticket open (step 6) and say who must answer.

## 4. Act on accepted tickets

Where the project uses beads (a `.beads/` directory, or `beads:` in its registry entry):

```bash
bd-track triage resolve <id> --bead --title "<title>" --type <bug|feature|task> \
  --priority <0-4> --description "<the ask and the context the bead needs to stand alone>"
```

- It runs `bd create` with label `triage`, appends `ticket: done/<file> (from X, date)` to the
  description itself, records `status: accepted`, `outcome: bead <id>` and moves the ticket to
  done/. The new id is in its log line and in the done file's `outcome`. If `bd create` fails,
  the ticket stays open.
- Without `--type`/`--priority` it maps the ticket's type (idea/question → task) and urgency
  (high/normal/low → P1/P2/P3); set them when MH's call differs.
- Rewrite into the project's bead style; do not paste the ticket wholesale. Keep the filer's
  evidence (errors, paths, versions) and MH's decisions from step 3.
- Then add edges to related beads (`bd link` / `bd dep`; the global dependency-hygiene rule), a
  parent epic when one fits, and `bd update <id> --status deferred` for a bead parked on
  another project. Run `bd dep cycles` after.

Fallback: `bd create ... --labels triage --description "<...> ticket: done/<file>"`, then step 5
by hand.

Where the project does not use beads, record it in the project's docs where its plans already
live (e.g. an open items list or the roadmap), following that project's conventions, then close
it with `resolve <id> --done "<doc path and section>"`.

## 5. Close the other decided tickets

```bash
bd-track triage resolve <id> --done "<where it was already done, or the doc change>"
bd-track triage resolve <id> --duplicate "<bead id, ticket or doc it duplicates>"
bd-track triage resolve <id> --reject "<one-line reason>"
```

Each writes `status`, `resolved` and `outcome` into the frontmatter (adding a block to a
free-form ticket, other keys kept) and moves it to `done/` under the same name; a quick note
becomes `done/<date>-<slug>.md` and leaves `inbox.md`.

Fallback, by hand: set these frontmatter keys, then `mv` the file from `triage/` to `done/`:

```yaml
status: accepted | rejected | duplicate | done
resolved: YYYY-MM-DD
outcome: <bead <id>, doc path and section, what it duplicates, or the reason>
```

A handled quick note becomes its own done/ file (`<date>-<slug>.md`, the frontmatter above plus
`from`/`date` from the paragraph's stamp, the paragraph as the body); remove the paragraph from
`inbox.md`, and delete `inbox.md` only if it ends up empty.

## 6. Tickets left open

```bash
bd-track triage ask <id> "<what is unclear, and who must answer>"
```

It appends a `## Triage YYYY-MM-DD` section and leaves the ticket open (a quick note is first
promoted to its own `triage/` file, whose name is its id from then on). Fallback: append that section by hand, keeping
`status: open`. If the filer is another project, also file the question there with
`triage-file`.

## 7. Report

Summarize: per disposition, the tickets and their outcomes (bead IDs, doc paths); the tickets
left open and why; anything filed elsewhere. Then `ticket --list` again to show what remains.

## Related

- `triage-file` skill: filing a ticket (format, the `ticket` command).
- bd-track `docs/triage.md` (`~/.local/src/bd-track/docs/triage.md`): the `bd-track triage` CLI.
- chezmoi `docs/decisions.md` D72: the design.
