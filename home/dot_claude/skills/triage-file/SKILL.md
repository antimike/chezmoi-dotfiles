---
name: triage-file
description: Filing a ticket (bug, feature, task, question) into another project's ticket inbox, or into this project's own for later. TRIGGER when work in one project turns up something another project should handle ("file a ticket against bd-track", "report this to amontillado", "note this for the chezmoi session"), when the user asks to file, report or hand off an issue to a project, or when you are about to edit another project's repo or beads to record a request. Codifies the `ticket` command, the inbox layout (D72), the ticket format (title, Context, Ask, Done when) and the rule that filing never touches the target repo or its beads.
author: Michael Haynes
scope: global
tags: [triage, tickets, cross-project]
timestamps:
  - action: created
    at: 2026-10-29T19:50:00-05:00
    actor: Claude (chezmoi session, bead chz-8o0.4)
comments:
  - "Source: chezmoi D72 (ticket inboxes for every project). Replaces /file-ticket, which ran bd create inside the target project."
  - "Companion: the `triage` skill processes an inbox (/triage)."
---

# Filing a ticket (D72)

Every project has an inbox at `~/.local/state/triage/<project>/`:

```
triage/            open tickets, one Markdown file each
triage/inbox.md    quick notes, one ticket per paragraph (append-only)
done/              handled tickets (moved there by /triage)
```

Project names come from the registry `~/.config/projects.yaml`; `ticket --projects` lists them.
A project not in the registry cannot receive tickets: ask MH to add it (chezmoi source
`home/private_dot_config/projects.yaml`) rather than inventing a name.

## The one rule

**Filing never touches the target project**: no edits in its repo, no `bd create` in its beads,
no `cd` there. The target project's own session decides what a ticket becomes. This keeps
sessions from writing into each other's state (and from `BEADS_DIR` contamination).

## How to file

Use the `ticket` command; it writes the frontmatter and picks the file name.

```bash
ticket -p <project> --type bug|feature|task|question --urgency low|normal|high \
  --title "<title>" - <<'EOF'
**Context.** ...

## Ask

...

## Done when

...
EOF
```

- `-p` is required unless the ticket is for the project you are working in (default: the current
  repo's project). An unknown name is refused with the closest matches.
- `from` defaults to `<user>@<current project>`. When you (Claude) file, pass
  `--from claude@<current project>` so the recipient knows the ticket came from an agent.
- `ticket` prints the new file's path; tell the user the path and the title.
- `--quick` appends one paragraph to `inbox.md`: for MH's one-line notes. Prefer a full ticket
  when you file.

## What a good ticket says

The recipient session starts cold: it has none of your context. Write for it.

- **Title**: the problem or the request in one line, specific enough to tell tickets apart
  (`` `queue prune` asks to queue parent epics before their children ``, not "queue bug").
- **Context**: what you observed and where (commands, paths, versions, error text), and why it
  matters to the filer. Say what is confirmed and what is a guess.
- **Ask**: what you want, as concrete as you can make it; numbered when there are several parts.
  Name open questions as open questions rather than deciding them for the recipient.
- **Done when**: how the recipient (and you) will know it is handled.
- One concern per ticket. Two unrelated asks are two tickets.
- No secrets, tokens or credentials. Inboxes are private, but accepted tickets turn into beads
  or docs, and some projects are public: keep client and employer names out.

Free-form tickets (no frontmatter, no sections) are accepted too; the format above is the
recommendation, not a gate.

## Related

- `triage` skill (`/triage`): processing an inbox.
- chezmoi `docs/decisions.md` D72: the design.
