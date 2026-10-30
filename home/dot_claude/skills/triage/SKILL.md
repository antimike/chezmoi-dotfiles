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

## 1. Read the inbox

```bash
ticket --list ${project:+-p "$project"}    # open tickets + quick-note count
```

Read every open ticket file and every paragraph of `inbox.md` in full. Note who filed each one
(`from`) and its date: an agent's ticket may describe state that has since changed.

## 2. Assess and propose

For each ticket, check it against the project before proposing anything:

- **Already done?** Search the code, `git log`, the docs and (if the project uses beads)
  `bd search` / `bd list`. A ticket whose ask is already met is `done`.
- **Duplicate?** Of an open bead, a docs open item, or another ticket in the inbox: `duplicate`,
  with what it duplicates. Merge any new detail into the original.
- **Clear enough to act on?** If not, it needs a question (step 3).
- **Worth doing here?** If it belongs in another project, propose re-filing it there
  (`triage-file`); if it is not wanted, propose `rejected` with a one-line reason.
- **Accept**: what it becomes (step 4), with type and priority.

Present one table: ticket, filer/date, your reading in one line, proposed disposition, and the
questions you need answered. Distinguish what you checked from what you assume.

## 3. Clarify (batched)

Ask all questions in one round, not one per ticket: AskUserQuestion takes up to four questions
per call, so group them; past that, list them in one message. A question the filer has to
answer (another project's session, an agent) cannot be answered here: leave that ticket open
(step 6) and say who must answer.

## 4. Act on accepted tickets

Where the project uses beads (a `.beads/` directory, or `beads:` in its registry entry):

```bash
bd create --title "<title>" --type <bug|feature|task> --priority <0-4> --labels triage \
  --description "<the ask, the context the bead needs to stand alone, and: ticket: done/<file>>"
```

- Rewrite into the project's bead style; do not paste the ticket wholesale. Keep the filer's
  evidence (errors, paths, versions).
- Add edges to related beads (`bd link` / `bd dep`; the global dependency-hygiene rule) and a
  parent epic when one fits.

Where it does not, record it in the project's docs where its plans already live (e.g. an open
items list or the roadmap), following that project's conventions.

## 5. Close handled tickets into done/

For every decided ticket, set these frontmatter keys (add a frontmatter block to a free-form
ticket; keep the other keys), then move it from `triage/` to `done/` with the same name:

```yaml
status: accepted | rejected | duplicate | done
resolved: YYYY-MM-DD
outcome: <bead id, doc path and section, what it duplicates, or the reason>
```

**Quick notes**: each handled paragraph of `inbox.md` becomes its own done/ file
(`<date>-<slug>.md`, with the frontmatter above plus `from`/`date` from the paragraph's stamp
when it has one, and the paragraph as the body); then remove that paragraph from `inbox.md`.
Leave unhandled paragraphs in place. Delete `inbox.md` only if it ends up empty.

## 6. Tickets left open

A ticket waiting for an answer stays in `triage/` with `status: open`; append a
`## Triage YYYY-MM-DD` section saying what is unclear and who must answer. If the filer is
another project, file the question there with `triage-file`.

## 7. Report

Summarize: per disposition, the tickets and their outcomes (bead IDs, doc paths); the tickets
left open and why; anything re-filed elsewhere. Then `ticket --list` again to show what remains.

## Related

- `triage-file` skill: filing a ticket (format, the `ticket` command).
- chezmoi `docs/decisions.md` D72: the design.
