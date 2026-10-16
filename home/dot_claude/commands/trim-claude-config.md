---
name: trim-claude-config
description: Audit length of Claude-context-injected config files (CLAUDE.md, MEMORY.md, …) and surface trim recommendations
argument-hint: "[--project] [--global]"
author: Michael Haynes
scope: global
tags: [meta, claude-config, hygiene]
timestamps:
  - action: created
    at: 2026-06-04T04:00:00-05:00
    actor: Michael Haynes
related: [trim-claude-config (skill)]
---

# /trim-claude-config

Thin wrapper for the `trim-claude-config` skill. Parse `$ARGUMENTS` for `--project` and/or `--global` and invoke the skill with that scope. If neither flag is present, the skill will prompt for the audit scope.

Arguments: $ARGUMENTS

See `~/.claude/skills/trim-claude-config/SKILL.md` for the full procedure.
