---
name: trim-claude-config
description: Audit length of Claude-context-injected files (CLAUDE.md, MEMORY.md, and similar) and surface trim recommendations. TRIGGER on `/trim-claude-config`, "trim my CLAUDE.md", "audit my Claude config files", or when a user-invoked trim is requested. Use --project / --global flags (additive) to scope; prompt for scope if neither flag is given.
author: Michael Haynes
scope: global
tags: [meta, claude-config, hygiene, docs]
timestamps:
  - action: created
    at: 2026-06-04T04:00:00-05:00
    actor: Michael Haynes
---

# trim-claude-config

Audit the **length** of every Claude-related file that is auto-injected into Claude's context — at the project level, global level, or both — and surface a list of trim recommendations the user can approve and execute.

## When to invoke

- User runs `/trim-claude-config` (with or without `--project` / `--global`).
- User asks to "trim", "audit", or "shrink" their Claude config files.
- **Opportunistic suggestion** (do NOT proactively examine): if, in the course of normal session work, you Read an auto-injected Claude config file and notice it is over the soft cap defined below, suggest the user run `/trim-claude-config` once and move on.

Do NOT use this skill to evaluate arbitrary project source files — its scope is Claude-context-injected config only.

## Arguments

- `--project` — audit project-local Claude files in the current working directory's project (`./CLAUDE.md`, `./.claude/**/*.md` if auto-injected, project-scoped `MEMORY.md` under `~/.claude/projects/<slug>/memory/`).
- `--global` — audit global Claude files (`~/.claude/CLAUDE.md`, anything under `~/.claude/skills/`, `~/.claude/commands/`, `~/.claude/agents/` that is loaded into every session).
- Flags are **additive**, not mutually exclusive. Both → audit both categories in one pass.
- Neither flag → prompt the user: "Audit project, global, or both?"

## Scope: what counts as "auto-injected"

Audit these by default:

- `~/.claude/CLAUDE.md` (global, always loaded)
- `<project>/CLAUDE.md` (project, always loaded when CWD is the project root)
- `~/.claude/projects/<project-slug>/memory/MEMORY.md` (auto-memory index, always loaded)
- Any file the project's `CLAUDE.md` links from the loaded chain as "always-on" content

Skills, commands, and agents are **on-demand** loaded — exclude them from the default audit unless the user explicitly asks. Auto-memory topic files (`feedback-*.md`, `project-*.md`, etc.) are also on-demand and excluded by default; only the `MEMORY.md` index is in-scope.

## Length guidelines (soft caps)

Heuristics, not hard rules. Cross either threshold → eligible for trim review.

| File class                         | Lines (soft cap) | Chars (soft cap) | Rationale                                                            |
|------------------------------------|------------------|------------------|----------------------------------------------------------------------|
| `CLAUDE.md` (global or project)    | 250              | 12 000           | Loaded into every session — every line is rent on the context budget |
| `MEMORY.md` index                  | 200              | 8 000            | Already enforced by global CLAUDE.md; keep the index tight           |
| Other always-on chained files      | 150              | 6 000            | If it's pulled in transitively, it should be even tighter            |

These thresholds are deliberately generous. A file at 110% of the cap is a *candidate* for review, not a problem; a file at 200% is a problem.

## Procedure

1. **Resolve scope** from flags (or prompt).
2. **Quick-pass length audit.** For each in-scope file, capture `wc -l` and `wc -c`. Do NOT read contents yet. List every file with `lines / chars (cap: L / C) → status` where status is `ok` or `over by N%`.
3. **Stop early if nothing exceeds.** Print the audit table and exit with "All audited files within soft caps."
4. **Per over-cap file**, read its contents and identify trim opportunities, organized by category:
   - **Paraphrase** — restate verbosely-phrased rules concisely without losing specificity.
   - **Extract** — move detail to a dedicated file (auto-memory topic file, `docs/<topic>.md`, or a skill) and leave a one-line pointer.
   - **Archive/remove** — stale sections, instructions superseded by newer guidance, dated transition notes whose expiry has passed.
   - **Other** — duplication across files, dead links, redundant emphasis.
5. **Present the recommendation list**, organized by file, with an estimated line-delta per item (e.g. `-12 lines: extract "bd-timew migration note" to a dated archive file`). Order by impact within each file.
6. **Iterate.** Accept user edits — drop items, re-scope items, add ones you missed.
7. **Execute approved edits.** For each:
   - Edit the chezmoi source (`~/.local/share/chezmoi/home/dot_claude/...`) when the target is chezmoi-managed.
   - Edit the live file directly when it is not (auto-memory `MEMORY.md` index files are NOT chezmoi-managed and live under `~/.claude/projects/<slug>/memory/`).
8. **Verify + commit + push + apply** for any chezmoi-managed edits. Standard protocol: `chezmoi diff` clean against the targets, conventional commit in the chezmoi repo with `Co-Authored-By` trailer, `git push`, `chezmoi apply --force <target>` for each target touched.

## Invariants

- **No proactive examination.** Outside an explicit `/trim-claude-config` invocation, this skill is opportunistic-suggestion-only.
- **No silent edits.** Always present recommendations and obtain approval before executing.
- **Cap is a heuristic.** If the user wants to keep a file long because it earns its weight, that is the user's call. Do not push back beyond surfacing the cap.
- **Don't trim by deleting context.** Paraphrase or extract; deleting load-bearing detail is worse than the length problem.
