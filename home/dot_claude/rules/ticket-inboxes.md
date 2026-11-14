# Ticket inboxes (cross-project requests)

Every project in the registry `~/.config/projects.yaml` has an inbox at `~/.local/state/triage/<project>/` (`triage/` open tickets, `triage/inbox.md` quick notes, `done/` handled). To hand something to another project, file a ticket with the `ticket` command and **never touch that project's repo or beads** (the `triage-file` skill has the format). A project processes its own inbox with `/triage` (the `triage` skill): MH decides each ticket; accepted ones become beads or docs. Design: chezmoi D72.
