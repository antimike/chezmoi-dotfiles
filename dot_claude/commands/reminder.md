---
name: reminder
description: Schedule a desktop notification at a future time or on a recurring interval
argument-hint: "<time> <message>  e.g. 10m \"Drink water\"  |  \"at 2pm\" \"Meeting prep\"  |  \"every 90m\" \"Screen break\""
author: Michael Haynes
scope: global
tags: [notifications, chezmoi, systemd]
timestamps:
  - action: created
    at: 2026-04-21T00:00:00-05:00
    actor: Michael Haynes
comments:
  - "Origin: /reminder slash command + BurntToast upgrade to wsl-notify-send."
  - "Backend: systemd transient timers (--on-active for relative, --on-calendar for absolute, background loop for --every). Notification delivery via ~/.claude/scripts/notify, which renders per host: notify-send on Linux, the wsl-notify-send shim (BurntToast) under WSL."
  - "Recurring reminders (--every) run as persistent systemd units; stop with /reminder --stop <unit> or reminder --stop <unit> from a terminal."
related: [/start, /stop, /status]
---

# /reminder — Schedule a desktop notification

Schedules a desktop notification using a systemd transient timer and delivers it via `~/.claude/scripts/notify` (notify-send on Linux; the wsl-notify-send shim under WSL).

Arguments: `<time-or-cadence> <message> [--scenario ...] [--group ...] [--button ...]`

## Argument shapes

- `/reminder 10m Drink water` — fires once in 10 minutes
- `/reminder 1h30m "Submit timesheet"` — fires once in 90 minutes
- `/reminder "at 2pm" "Meeting prep"` — fires at 2:00 PM today
- `/reminder "at 14:30" "Deploy review"` — fires at 14:30
- `/reminder "every 90m" "Take a screen break"` — recurring every 90 minutes
- `/reminder --list` — show active reminder units
- `/reminder --stop <unit-name>` — cancel a scheduled reminder

Optional notify flags (appended after the message):
- `--scenario reminder|alarm|incomingCall|default`
- `--group <id>` — replacement group; same id replaces rather than stacks
- `--button "label=action"` — action button (dismiss | snooze | url); WSL only, ignored by notify-send

## Instructions

1. **Parse arguments.** The first non-flag token is the time/cadence; everything after it up to a recognized flag is the message.

2. **Resolve the time expression** to one of:
   - `--in <duration>` — for relative times (`10m`, `1h30m`, `90s`). Durations are `Nm`, `Nh`, `Ns` or combinations.
   - `--at <calendar>` — for absolute times. Convert natural language to a systemd OnCalendar spec:
     - `at 2pm` → `14:00`
     - `at 14:30` → `14:30`
     - `tomorrow 9am` → `tomorrow 09:00`
     - Already a valid calendar spec → pass through unchanged.
   - `--every <duration>` — for recurring intervals. Accepts same duration syntax as `--in`.

3. **Handle `--list` and `--stop`.** Pass through to `reminder` directly:
   ```
   reminder --list
   reminder --stop <unit-name>
   ```

4. **Run `reminder`.** Compose the command using the resolved time flag plus any notify flags:
   ```
   reminder --in <secs> [--scenario ...] [--group ...] [--button ...] "<title>" ["<body>"]
   ```
   Use the message as the title. If the message is long enough to split naturally (subject + detail), put the subject as title and the detail as body.

   If `reminder` exits non-zero, surface the error verbatim. Common causes:
   - `systemd-run` not available — no systemd user session (under WSL2: enable systemd in `/etc/wsl.conf`).
   - `~/.claude/scripts/notify` not found — not deployed yet; suggest `chezmoi apply`.

5. **Confirm.** Print a one-line confirmation echoing back what was scheduled and when:
   ```
   Scheduled: "Drink water" in 10m (unit: reminder-1745234567)
   Scheduled: "Meeting prep" at 14:00 (unit: reminder-1745234568)
   Recurring: "Screen break" every 90m (unit: reminder-1745234569) — stop with /reminder --stop reminder-1745234569
   ```

6. **Do not editorialize.** No follow-up suggestions, no asking if the reminder is set up correctly. The `reminder` script output is the source of truth.

## Recurring reminders and the "while work" stop condition

`--every` creates a background loop unit that fires indefinitely until stopped. The "while work" stop condition (pause when timew isn't tracking) is not yet implemented — the loop fires unconditionally. Stop it manually with `reminder --stop <unit>` or `systemctl --user stop <unit>`.
