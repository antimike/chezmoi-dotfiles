#!/bin/sh
# run_after_bd-track-migrate-notice.sh — remind to migrate bd-track's legacy repos.yaml.
#
# bd-track >= 0.7.0 keeps projects in ~/.config/projects.yaml and host settings in
# ~/.config/bd-track/config.yaml; a leftover ~/.config/bd-track/repos.yaml is still read
# alongside them until `bd-track migrate registry --apply` moves it (repos.yaml.migrated).
# The migration moves files the user may want to review, so this never applies it: while
# repos.yaml exists, every apply prints the dry run and the command to run. Silent otherwise.
# Never fails the apply.

# bd-track reads ~/.config, not $XDG_CONFIG_HOME.
legacy="$HOME/.config/bd-track/repos.yaml"
[ -f "$legacy" ] || exit 0

say() { echo "bd-track migrate notice: $*" >&2; }

if ! command -v bd-track >/dev/null 2>&1; then
  say "$legacy exists but bd-track is not on PATH; install it, then run: bd-track migrate registry"
  exit 0
fi

say "$legacy is not migrated yet. Dry run:"
bd-track migrate registry >&2 || say "dry run failed (bd-track older than 0.7.0?)"
say "review the above, then run: bd-track migrate registry --apply"
exit 0
