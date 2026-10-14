---
name: man
description: Manpage-style browser for this user's custom slash-commands and skills. `/man commands` and `/man skills` print tables (name + argument-hint + description from frontmatter); `/man <name>` prints detailed usage (description, argument hints, examples) for a matching command and/or skill; bare `/man` prints this command's own usage. Covers global (~/.claude) and project (.claude) definitions. TRIGGER on `/man`, "list my commands", "what skills do I have", "how do I use /<name>".
argument-hint: "[commands | skills | <command-or-skill-name>]"
author: Michael Haynes
scope: global
tags: [help, discovery, commands, skills, meta, manpage]
timestamps:
  - action: created
    at: "2026-05-26T00:00:00-05:00"
    actor: Michael Haynes
comments:
  - "Named /man (Linux-manpage reflex), deliberately NOT /help or /usage: both are fixed, non-extensible Claude Code built-ins and the docs do not define custom-vs-built-in precedence, so shadowing either risks the custom command never firing. /man has no built-in collision and adds the rich shapes (tables, per-item detail, fuzzy match) the built-ins and the `/` autocomplete do not provide."
  - "Discovery substrate already exists: the `/` autocomplete shows description + argument-hint, and the built-in `/skills` lists skills. This command's value is the consolidated tables, the `/man <name>` detail view, and the did-you-mean fallback."
related: [auto-session, work-queue, alert-timer]
---

# /man — browse custom commands and skills

## Data sources

Enumerate definitions from four locations (global first, then project; label each entry by origin):

| Kind | Global | Project |
|---|---|---|
| Commands | `~/.claude/commands/*.md` | `<project-root>/.claude/commands/*.md` |
| Skills | `~/.claude/skills/*/SKILL.md` | `<project-root>/.claude/skills/*/SKILL.md` |

`<project-root>` is the current workspace root (the dir containing `.claude/`). If there is no project `.claude/`, only global entries exist.

Each file carries YAML frontmatter. Read these fields:
- **Commands:** `name` (fallback: filename without `.md`), `description`, `argument-hint`.
- **Skills:** `name` (fallback: directory name), `description`. (Skills rarely set `argument-hint`; show it only if present.)

Built-in Claude Code commands (`/help`, `/usage`, `/model`, etc.) are out of scope — they are covered by the built-in `/help` and the `/` autocomplete menu. Say so if the user seems to be looking for one.

Parse frontmatter with a real YAML reader, not a regex (e.g. a short `python3` snippet over the file's frontmatter block), so multi-line/quoted descriptions survive.

**Aliases.** A command file may be a symlink to another command file (created by `/add-command-alias`). Detect symlinks: do not render the alias as a separate duplicate entry. Instead, attribute it to its target and show the alias names alongside the target — e.g. `/session-checkpoint (alias: /chk)`. Resolve the symlink to group it with its target before rendering or matching.

## Shape dispatch

Inspect `$ARGUMENTS`:

- empty → **Self-usage** (Step A)
- exactly `commands` → **List commands** (Step B)
- exactly `skills` → **List skills** (Step C)
- anything else → treat as a name → **Detail / fuzzy** (Step D)

### Step A — Self-usage (bare `/man`)

Print this command's own usage from its frontmatter: the `description`, the `argument-hint`, and the four shapes with one example each:

```
/man commands          list all custom commands
/man skills            list all custom skills
/man <name>            detailed usage for a command and/or skill
/man                   this message
```

### Step B — List commands

Gather all command entries (global + project). Render a table sorted by name, grouped by origin (Global, then Project), each row:

```
/<name>   <argument-hint>
          <description>
```

Use a compact two-line-per-entry layout (name + arg-hint on line 1, description indented on line 2) so long descriptions stay readable in monospace. Note the count per origin. If an entry is missing `description` or `argument-hint`, render `(none)` rather than omitting the field. Collapse symlink aliases into their target's row (`alias: /<name>`), per the Aliases note above — do not emit a duplicate row for the alias.

### Step C — List skills

Same as Step B, over skill entries. Omit the argument-hint column position when a skill has none (most do); show it inline when present.

### Step D — Detail / fuzzy (`/man <name>`)

Normalize `<name>` (strip a leading `/`, lowercase for matching).

1. **Exact matches.** Find every command AND skill whose `name` equals `<name>`. If a command and a skill both match, render **both** sections (clearly headed `Command: /<name>` and `Skill: <name>`) — they are distinct definitions.

   For each match, print:
   - Origin (Global / Project) and source path.
   - `description` (full).
   - `argument-hint` (commands) / any declared arg hints.
   - **Examples:** pull from the file — prefer an `## Examples`/usage section in the body; otherwise synthesize 1-2 from the `argument-hint`. For skills, summarize the "When to fire" / trigger section if present.

2. **No exact match → did-you-mean.** State plainly that no command or skill is named `<name>`, then list the closest candidates across both kinds. Rank by similarity (substring hits first, then small edit distance / shared prefix); show up to ~6, each as `/<name> — <description first clause>` and tagged `(command)` / `(skill)`. Invite the user to re-run `/man <name>` with one of them.

## Invariants

- Read-only. This command never writes, edits, or invokes any command or skill — it only reports their metadata.
- Always cover both global and project locations; never silently restrict to global.
- A name collision (same name as both a command and a skill) yields BOTH detail sections, never an arbitrary pick.
- Prefer the YAML frontmatter as the source of truth for `description`/`argument-hint`; fall back to filename/dirname only for `name`.
