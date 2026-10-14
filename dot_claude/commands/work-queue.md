---
name: work-queue
description: Iterate a bd-track queue scope — peek the head bead, decide if it is autonomously executable, rotate transient blockers to the tail and park operator-required beads, execute + verify + close executable ones (bd-track-tracked), and repeat until the scope is empty, all remaining beads need an operator, or the queue deadlocks. Wraps `bd-track queue` primitives + `/start`/`/stop`. TRIGGER on `/work-queue`, "work the <scope> queue", "run the autonomous pool".
argument-hint: "[<scope>] [--full-auto] [--worktrees] [--max=<n>] [--notify=wsl|ntfy|none] [--ntfy-topic=<t>] [--operator-status=<status>] [--done-status=<status>] [--dry-run]"
author: Michael Haynes
scope: global
tags: [beads, queue, autonomous, bd-track, notifications]
timestamps:
  - action: created
    at: "2026-05-26T00:00:00-05:00"
    actor: Michael Haynes
comments:
  - "Encapsulates the queue-iteration loop used interactively across the 2026-05 autonomous-pool sessions. Distinct from /auto-session: that scaffolds a full sandboxed multi-bead session and loops on `bd ready`; this is a lightweight loop over the curated `.beads/queue.yaml` ordering via `bd-track queue`."
  - "Built on bd-track queue primitives (peek/pop/unshift/push/remove/list) so it never hand-edits queue.yaml. Single-writer for bd-track + bd, same invariant as /auto-session Step 7."
related: [start, stop, status, alert-timer, auto-session]
---

# /work-queue — iterate a bd-track queue scope

Work through an ordered `.beads/queue.yaml` scope: execute the beads that can be done autonomously, rotate the ones transiently blocked, park the ones that need a human, and stop cleanly when there is nothing left to do autonomously.

## Step 1 — Parse arguments

| Arg / flag | Default | Meaning |
|---|---|---|
| positional `<scope>` | `$BD_TIMEW_SCOPE` then `default` | Which queue scope to work. |
| `--full-auto` | off | Remove the per-bead checkpoint: execute → verify → commit → close → pop → stop → advance with no pause. Without it, pause for confirmation before each `bd close`. |
| `--max=<n>` | unlimited | Stop after `n` successful bead closes (safety cap for unattended runs). |
| `--notify=<wsl\|ntfy\|none>` | `wsl` | Per-event notification backend. `none` disables event toasts. |
| `--ntfy-topic=<t>` | — | Required when `--notify=ntfy`. |
| `--operator-status=<status>` | `auto` | Status set on a parked, operator-required bead. `auto` resolves per Step 2b. |
| `--done-status=<status>` | `auto` | Status a finished bead lands in. `auto` resolves per Step 2b (prefer a review status, else hard close). |
| `--worktrees` | off | Worktree-exclusive isolation: every repo touched during a bead is operated on in a dedicated git worktree + branch, never the canonical checkout. See Step 2c. |
| `--dry-run` | off | Walk the queue and print the decision per bead (execute / rotate / park) without mutating beads, bd-track intervals, or running work. |

Reject unknown flags.

## Step 2 — Preflight

1. Confirm `bd-track queue list --scope <scope>` returns a non-empty scope. If empty, print `work-queue: scope '<scope>' is empty` and stop.
2. Confirm no bd-track interval is already open (`bd-track status`). If one is open, stop and tell the user to `/stop` first — this loop is the single writer for bd-track intervals.
3. Resolve the status policy (Step 2b) and, if `--worktrees`, the isolation root (Step 2c).
4. Print the run plan and **require explicit confirmation before the loop starts**: scope, item count, mode (`checkpoint` vs `full-auto`), notify backend, max, **resolved park status**, **resolved done status**, and **isolation** (`worktree` vs `in-place`). Under `--dry-run`, note that nothing will be mutated (and skip the confirmation — dry-run is inherently safe). This is the single up-front gate; do not re-confirm the policy per bead.

### Step 2b — Resolve status policy

Statuses vary per project, so resolve against the live config. List available statuses with `bd statuses` (built-in + custom) or `bd config get status.custom` (custom only). Then:

- **Park status** (`--operator-status`): if set explicitly, use it (error if not a valid status). If `auto`: use the custom status `operator` when it is available in this project; otherwise fall back to the built-in `deferred`. The `needs:operator` label is applied regardless of which status is used.
- **Done status** (`--done-status`): if set explicitly, use it (error if invalid). If `auto`: prefer a dedicated auto-review status if available, in priority order `review-auto` → `review`; if neither exists, fall back to a hard close (status `closed` via `bd close`). Rationale: an autonomously-finished bead should land in a human-review state when the project has one, rather than being silently closed.

Surface the resolved pair in the Step 2.4 run plan so the user confirms the actual statuses before any bead is touched.

### Step 2c — Worktree isolation (only under `--worktrees`)

Default isolation is **in-place**: beads are implemented and committed in each repo's canonical checkout. Under `--worktrees`, isolation is **worktree-exclusive** — no commits ever land on a canonical checkout during the run.

Convention (matches the project's established pattern):
- Worktree path: `<project-root>/.worktrees/<bead-id>-<slug>/<repo-name>/` (the `.worktrees/` root is git-excluded).
- Branch: `mhaynes/feat/<bead-id>-<slug>` created from the repo's canonical branch HEAD (use `dev/<bead-id>-<slug>/phase-<n>-<slug>` for an explicit phase branch off a long-running accumulator, per the global multi-phase convention).
- `<slug>` derives from the bead title (kebab-case).

Per-bead mechanics (applied in Step 4c when the bead first touches a repo):
- `git -C <canonical-repo> worktree add <worktree-path> -b mhaynes/feat/<bead-id>-<slug>` (or check out an existing branch if resuming).
- All edits, builds, and commits for that bead happen inside the worktree. Refuse to write to the canonical checkout.
- At bead completion: push the branch for pre-authorized repos (never merge to the canonical branch mid-run); leave the worktree in place after the run for review / PR (do not auto-remove — worktrees and their branches are the reviewable artifact). Note any created worktrees in the Step 5 summary so the user can `git worktree remove` them after merge.

If `--worktrees` is set and a bead would touch a repo that is not a git repo, halt and report rather than committing in-place.

## Step 3 — Iterate

Maintain two pieces of loop state:
- `rotated_since_progress` — set of bead IDs rotated to the tail since the last successful close or park. Used for deadlock detection.
- `closed_count` — successful closes this run.

Loop:

### 3a — Peek

`head = bd-track queue peek --scope <scope>`. If the scope is empty → go to Step 5 (clean finish).

### 3b — Classify (the executability gate)

Read `bd show <head>`. Decide one of three outcomes:

1. **Transiently blocked** — `status` is `blocked`, or a dependency is unmet (`bd dep tree <head>` shows an open blocker), AND nothing about the bead requires a human. The blocker may be satisfied by a bead later in this same scope. → **Rotate** (Step 4a).
2. **Operator-required** — either an explicit signal (label `needs:operator`, or `scope:local` + a title beginning `Operator:`, or membership intent for a `*.operator` scope), OR Claude's judgment that the description requires a human, an external approval, another person, or out-of-band access this session cannot perform. → **Park** (Step 4b).
3. **Executable** — none of the above. → **Execute** (Step 4c).

Apply judgment conservatively: when unsure whether a bead needs a human, treat it as operator-required and park it (a wrongly-parked bead is a cheap human glance; a wrongly-attempted one can half-finish work).

### 3c — Deadlock guard

If the chosen outcome is **Rotate** and `head` is already in `rotated_since_progress`, the loop has cycled the entire remaining scope without making progress → go to Step 5 (deadlock finish). Otherwise add `head` to `rotated_since_progress` and proceed.

Any **Execute** (on close) or **Park** clears `rotated_since_progress` (progress was made).

## Step 4 — Outcomes

### 4a — Rotate (transiently blocked)

```
bd-track queue pop  --scope <scope>          # removes head
bd-track queue push --scope <scope> <head>   # appends to tail
```
Log one line: `rotate <head> — blocked by <reason>`. Continue loop.

Under `--dry-run`: print the decision only; do not pop/push.

### 4b — Park (operator-required)

If the bead lacks the durable signal, add it. Then record status + note, and pull it out of the autonomous scope into a parked scope:

Use the **resolved park status** from Step 2b (`operator` if available, else `deferred`; or the explicit `--operator-status`):

```
bd update <head> --add-label needs:operator --status <resolved-park-status>
bd note   <head> "[work-queue <ISO>] parked: needs operator — <one-line reason>"
bd-track queue remove --scope <scope> <head>
bd-track queue push   --scope <scope>.operator <head>
```
Log: `park <head> — needs operator: <reason>`. Clear `rotated_since_progress`. Continue loop.

Notes:
- If a `<scope>.operator` scope does not exist, `bd-track queue push` creates it.

Under `--dry-run`: print the decision only; do not label/transition/move.

### 4c — Execute (autonomously executable)

1. **Claim + start bd-track:** `/start <head>` (claims the bead and starts the interval).
2. **Notify (claim):** unless `--notify=none`, fire a claim toast (Step 6).
3. **Isolation setup (only under `--worktrees`):** before touching any repo for this bead, create/check out its worktree + branch per Step 2c. All subsequent edits/commits for this bead go in the worktree; never the canonical checkout.
4. **Do the work.** Implement the bead per its description and the project conventions. Verify (tests / dry-run / build as appropriate). Commit per the repo's commit discipline (in the worktree under `--worktrees`, else in-place). If during execution the bead turns out to need a human (a blocking decision, missing access), stop work, `/stop`, and treat it as **Park** (4b) instead of closing.
5. **Checkpoint (unless `--full-auto`):** present what was done + verification result, and ask `Finish <head> and advance? (yes / park / stop)`. On `park` → 4b. On `stop` → `/stop`, then Step 5.
6. **Finish + pop + stop:** land the bead in the **resolved done status** from Step 2b:
   ```
   # done status == closed:
   bd close <head>
   # done status == review-auto | review | other:
   bd update <head> --status <resolved-done-status>

   bd-track queue pop --scope <scope>     # head is the bead we just finished
   /stop                                  # release the bd-track interval
   ```
   Under `--worktrees`: push the bead's branch for pre-authorized repos; leave the worktree in place for review/PR.
7. **Notify (complete):** unless `--notify=none`, fire a complete toast (Step 6).
8. `closed_count += 1` (counts finishes, whether closed or moved to review); clear `rotated_since_progress`. If `--max` reached → Step 5. Else continue loop.

Under `--dry-run`: print `would execute <head>` and stop the run (dry-run does not perform work).

## Step 5 — Finish

Stop conditions: scope empty, all remaining parked, deadlock, `--max` reached, or user `stop`.

1. Ensure no bd-track interval is left open (`bd-track status`; `/stop` if needed).
2. Print a summary: finished (with IDs + resolved done status), parked (with IDs + reasons), still-queued (IDs), and the stop reason. Under `--worktrees`, also list every worktree + branch created (path + branch), so the user can review/PR them and `git worktree remove` after merge.
3. Fire a single run-complete notification (Step 6, event `run-complete`) summarizing counts, regardless of `--notify` per-event setting unless `--notify=none`.

## Step 6 — Notifications

Per-event toasts. Title/body by event:

| Event | Title | Body |
|---|---|---|
| `claim` | `work-queue: claimed <id>` | bead title |
| `complete` | `work-queue: closed <id>` | bead title + elapsed |
| `run-complete` | `work-queue: <scope> done` | `closed N, parked M, remaining K — <stop reason>` |

Dispatch by backend:
- `wsl`: `wsl-notify-send "<title>" "<body>"`
- `ntfy`: `curl -s -H "Title: <title>" -d "<body>" "https://ntfy.sh/<topic>"`
- `none`: skip.

### Composing with /alert-timer for step-away runs

Per-event toasts assume you are at the machine. To be pinged when the **whole run** finishes while you are away (phone push, or a single end-of-run toast independent of this session), wrap the queue in a detached `/alert-timer` that polls the scope length:

```
/alert-timer 120s --detached \
  --action="bd-track queue list --scope <scope> | wc -l" \
  --alert-when="eq:0" \
  --backend=ntfy --topic=<your-topic> \
  --alert-message="<scope> queue drained"
```

That reuses the `poll_until` engine and gives the full `/alert-timer` backend surface without duplicating it here.

## Invariants

- This command is the **single writer** for bd-track and bd mutations during the run. Never start a second interval; always `/stop` before finishing.
- Never `bd close` a bead that was not actually completed + verified. When in doubt, park it.
- Deadlock (a full rotation with no progress) is a clean stop, not an error — report the cycle and let the user break it.
- `--dry-run` mutates nothing: no bead updates, no queue pops/pushes, no bd-track intervals, no work.
- Conservative classification: ambiguous "might need a human?" → park, don't attempt.
- Under `--worktrees`, no commit ever lands on a canonical checkout — all bead work happens in a per-bead worktree + branch, and worktrees are kept after the run for review.
- Status policy and isolation mode are resolved and confirmed once in Step 2 before any bead is touched; never silently pick a status the project doesn't have.
