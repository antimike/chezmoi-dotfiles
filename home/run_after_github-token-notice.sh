#!/bin/sh
# run_after_github-token-notice.sh — remind to give this host its own GitHub token.
#
# github-token (~/.local/bin) reads tokens/github/<host> from pass and falls back to
# tokens/github/default. This checks the store for the per-host .gpg file without
# decrypting anything; while it is missing, every apply prints how to create it.
# Silent once it exists. Never fails the apply.

store="${PASSWORD_STORE_DIR:-$HOME/.password-store}"
[ -d "$store" ] || exit 0

host="$(hostname -s 2>/dev/null || hostname)"
host="${host%%.*}"
[ -f "$store/tokens/github/$host.gpg" ] && exit 0

say() { echo "github-token notice: $*" >&2; }

if [ -f "$store/tokens/github/default.gpg" ]; then
  say "no tokens/github/$host in pass; .envrc files use tokens/github/default meanwhile."
else
  say "neither tokens/github/$host nor tokens/github/default is in pass; github-token fails."
fi
say "create a token (github-token --new opens the page), then: pass insert tokens/github/$host"
exit 0
