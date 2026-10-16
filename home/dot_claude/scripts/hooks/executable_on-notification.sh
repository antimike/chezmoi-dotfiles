#!/usr/bin/env bash
# on-notification.sh — Claude Code Notification hook.
#
# Reads a hook event JSON payload on stdin. If a notification config sentinel
# exists for the current session at
#   ~/.local/state/claude/notifications/<session-id>.jq
# evaluates it as a jq expression against the payload, then pipes the result
# to ~/.claude/scripts/notify via --config - (host-portable adapter). Sentinels are absent by default; sessions
# opt in via `claude-notify enable`.
#
# Failures are silent (exit 0) so the harness's notification UX isn't
# interrupted by hook errors.

set -uo pipefail  # no -e: best-effort, no aborts on missing pieces

payload=$(cat)
session_id=$(jq -r '.session_id // empty' <<<"$payload" 2>/dev/null)
[ -z "$session_id" ] && exit 0

sentinel="$HOME/.local/state/claude/notifications/${session_id}.jq"
[ ! -f "$sentinel" ] && exit 0

config=$(jq -f "$sentinel" <<<"$payload" 2>/dev/null)
[ -z "$config" ] && exit 0

notifier="$HOME/.claude/scripts/notify"
[ -x "$notifier" ] || exit 0

"$notifier" --config - <<<"$config" 2>/dev/null || true
