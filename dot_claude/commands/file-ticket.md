---
name: file-ticket
description: File a bug/feature/task against another project's beads without cd-ing into it or tripping BEADS_DIR contamination. Registry at ~/.claude/file-ticket-registry.yaml maps short project names to root dirs.
argument-hint: "<project> [--title <title>] [--type bug|feature|task] [--priority 0-4] [--description <text>]"
author: Michael Haynes
scope: global
tags: [beads, cross-project, ticketing]
timestamps:
  - action: created
    at: 2026-06-04T00:00:00-05:00
    actor: Michael Haynes
    note: "bd-timew-mm0: cross-project ticket inbox. Rides the 4g4 chezmoi pass. Uses env -u BEADS_DIR pattern to safely run bd create in another project's dir without contamination."
related: [/start, /show]
---

# /file-ticket — File a ticket against another project

File a Beads issue against any registered project without `cd`-ing into it,
without tripping `BEADS_DIR` contamination, and without knowing the project's
billing-tuple config.

Arguments: $ARGUMENTS

## Registry

The project registry lives at `~/.claude/file-ticket-registry.yaml`. Shape:

```yaml
projects:
  bd-track: ~/.local/src/bd-track          # the bd-track dev repo
  chezmoi: ~/.local/share/chezmoi          # dotfiles
  myproj: ~/Source/myproj                  # add your projects here
```

Short names are arbitrary; they're just what you type after `/file-ticket`.

## Instructions

### Step 1 — Parse arguments

Recognized forms:
- Positional: first non-flag token is the project name
- `--title <text>` — ticket title (required; prompt if absent)
- `--type bug|feature|task` — issue type (default: `task`)
- `--priority 0-4` — priority (default: `2`)
- `--description <text>` — short description (optional; prompt if absent)
- `--dry-run` — print the resolved `bd create` command without running it

If no project name → print:

```
/file-ticket: missing project name
usage: /file-ticket <project> [--title <title>] [--type bug|feature|task]
                               [--priority 0-4] [--description <text>]
       /file-ticket list          # show registered projects
```

If the argument is `list` → print the registry contents and stop.

### Step 2 — Load the registry

Read `~/.claude/file-ticket-registry.yaml` via the Read tool. Parse the
`projects:` map. Expand `~` in paths.

If the file does not exist or is empty, print:

```
/file-ticket: registry not found at ~/.claude/file-ticket-registry.yaml
Create it with:
  projects:
    <project-name>: <absolute-path-to-project-root>
```

and stop.

If the requested project name is not in the registry, print the known names
and stop.

### Step 3 — Resolve title and description

If `--title` was not supplied, ask on one line:

```
Title (required):
```

If `--description` was not supplied, ask on one line:

```
Description (optional — enter to skip):
```

An empty description is fine; it just omits `--description` from the bd create call.

### Step 4 — Build and run the bd create command

Construct:

```bash
env -u BEADS_DIR -u BEADS_DOLT_PASSWORD \
  bash -c 'cd <project-root> && bd create \
    --title <title> \
    --type <type> \
    --priority <priority> \
    [--description <description>]'
```

Key safety rule: always prefix with `env -u BEADS_DIR -u BEADS_DOLT_PASSWORD`.
This strips any contaminated environment variables that a parent shell's
`.envrc` may have injected (see global CLAUDE.md "BEADS_DIR contamination"
gotcha). Without this, `bd` may silently resolve against the wrong project.

Under `--dry-run`: print the command verbatim and stop; do not execute.

### Step 5 — Report

If the bd create command succeeds, report:

```
Filed <new-id> in <project> (<project-root>)
  Title: <title>
  Type:  <type>  Priority: P<priority>
```

If it fails (non-zero exit), surface the full stderr verbatim. Common causes:
- Project root has no `.beads/` directory (`bd init` not run there)
- `bd` not on PATH (check `which bd`)
- Invalid type or priority value

## Caveats

- This command files tickets against whichever branch the target project's
  beads are currently on. It does not `bd dolt push` afterward; that's the
  recipient project's responsibility.
- Once bead consolidation lands (bd-timew-cjq), all projects will share
  `~/.beads` and cross-project filing will be near-trivial. This command
  remains useful as the ergonomic front door regardless.
- If the target project uses `BEADS_DIR` itself (unusual), the `env -u`
  prefix will strip that too. In that case the operator should use a direct
  `bd create` in the target project's session.

## Related

- `/show` — show a bead by ID (reads from current project)
- `bd-timew-cjq` bead — beads consolidation spike (will simplify this further)
