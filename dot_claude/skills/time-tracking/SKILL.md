---
name: time-tracking
description: Beads + bd-track time-tracking ritual. Use when claiming a bead to work on, switching focus between beads, stopping work for a break, or checking what's currently being tracked. Covers the /start, /stop, /switch, and /status slash commands that wrap the bd-track CLI.
author: Michael Haynes
scope: global
tags: [time-tracking, beads, bd-track, billing]
timestamps:
  - action: created
    at: 2026-04-20T00:35:06-05:00
    actor: Michael Haynes
comments:
  - "Source: Wave 1 time-tracking bundle (2026-04-20). Companion to the /start, /stop, /switch, /status slash commands and the bd-track CLI at ~/.local/bin/bd-track."
  - "Motivation: the time-tracking ritual (claim bead → start timer with correct tuple → stop at break → generate report) was unwritten and error-prone. Codifying it as a skill with TRIGGER language ensures Claude invokes it autonomously when the ritual is in scope."
  - "Projected use: fires when the user invokes any /start, /stop, /switch, /status command or references bd-track / bd-timew. Tuple-resolution rules (Option A sidecar at .beads/bd-track.yaml) documented in auto-memory feedback-time-tracking.md."
---

# Time Tracking

This skill codifies the Beads + bd-track time-tracking workflow. Every unit of billable and non-billable work should be bracketed by a `bd-track` interval tagged with a Beads issue ID and a resolved `(client, case, svc)` tuple.

## The bridge: `bd-track`

`bd-track` (at `~/.local/bin/bd-track`, Chezmoi-managed) is the single source of truth for linking Beads issues to time-tracking intervals. It uses an append-only per-session JSONL event log (no shared global state) and reads the per-workspace sidecar `.beads/bd-track.yaml` to resolve a bead's labels to a NetSuite billing tuple.

**Resolution order** (first wins, merged onto the sidecar's `default:` block):

1. Per-issue `case:<string>` label on the bead (escape hatch — forces `case`).
2. First matching rule in the sidecar's `patterns:` list (regex over the space-joined label string).
3. Sidecar `default:` block.
4. Hardcoded fallback: `svc = "Technology Services"`.

Run `bd-track resolve <id>` to preview the tuple without starting anything.

## Slash commands

| Command | Wraps | When to use |
|---|---|---|
| `/start <bead-id>` | `bd-track start <id>` | Beginning work on a bead. Claims the bead in Beads and starts a tagged `bd-track` interval for this session. |
| `/switch <bead-id>` | `bd-track switch <id>` | Mid-session refocus. Stops the current interval, claims the new bead, starts a new interval. Not transactional — if `start` fails after `stop`, no interval runs; rerun `/start`. |
| `/stop` | `bd-track stop` | Ending work, break, end of day. Does **not** change bead status in Beads — the bead stays claimed (use `bd close <id>` to finish). |
| `/status` | `bd-track status` | Answering "what am I tracking right now in this session?" without leaving Claude. Shows bead ID + title, Beads status, elapsed time, and resolved tuple. For all open intervals across all sessions, run `bd-track active` directly. |

### No-argument handling

`/start` and `/switch` require an argument. If the user invokes either without a bead ID, refuse with short usage text — do not guess a bead from `bd ready` or `bd list --status=in_progress`. Silently starting a timer on the wrong bead corrupts billing data.

### Interpreting `/status` output

```
Tracking: proj-abc  <title>
Status:   in_progress | open | blocked | ...
Elapsed:  1h 23m
Client:   <bucket> | (none)
Case:     <NetSuite case string> | area:<label> | (none)
Svc:      <service item> | none | (none)
```

- `Svc: none` (the string "none") marks a non-billable interval (tooling, meta-work, personal).
- `Svc: (none)` (parenthesised) means the tuple field was unresolved — investigate the sidecar or bead labels.
- `Case: area:<label>` means the resolver fell through to a default that uses the raw Beads area label; this is expected for non-client work buckets.

## Variance and reporting

`bd-track` does not yet ship a dedicated variance subcommand. To compare actual time to an `est-h:N` estimate, use `bd-track report --bead <bead-id>` to list intervals for that bead, then compare to the `est-h:` label via `bd show <bead-id>`. See the follow-up bead for automating this (tracked under Wave 2: variance reporting).

> **Note:** The legacy `timew summary` interface is no longer available. The Timewarrior backend was replaced by an append-only per-session JSONL event log in bd-track 0.5.0.

## Estimate label convention

Three optional dimensions; apply at creation time, retrofit only when touching an issue for other reasons:

- `est-h:N` — hours (whole or half integers, min 0.5). **Only dimension `bd-track` variance reports consult.**
- `est-p:N` — story points (scrum).
- `est-t:S` — t-shirt size: XS / S / M / L / XL.

Query patterns: `bd list --label-pattern='est-h:*'` etc.

## When to invoke this skill autonomously

- Any time the user says "start working on <bead>" or "let's do <bead>".
- Session-start rituals where a bead is being claimed.
- When the user asks "what am I working on?" or equivalent.
- Before a `/clear` or end-of-session: if a timer is running and the user indicates wrapping up, confirm whether to `/stop`.

## References

- `bd-track` source: its own repo (`~/.local/src/bd-track`), installed with pipx; the CLI lands at `~/.local/bin/bd-track`
- Sidecar schema example: `<project>/.beads/bd-track.yaml`
- Full convention + rationale: auto-memory `feedback-time-tracking.md`
- Label taxonomy (Option B prefix-namespaced): auto-memory `reference-beads-label-taxonomy.md`
- Billing-tuple decision record: `bd memories time-tracking-option-a-decision`
