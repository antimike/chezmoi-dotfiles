# Chezmoi systemd-user timer patterns

Reference for adding systemd-user service + timer units under Chezmoi management. In this repo, the in-tree example pair is `private_dot_config/private_systemd/private_user/wallpaper.service.tmpl` + `private_wallpaper.timer.tmpl`. The conventions below were codified on the BOCO dotfiles (examples: `timew-autostop` / `timew-nudge` units under `home/dot_config/systemd/user/` in `~/Source/chezmoi-boco`, a reference-only clone).

This doc codifies the conventions so new timers (e.g., `/reminder`, `/timebox`, other periodic housekeeping units) follow the same shape.

## File layout

```
private_dot_config/private_systemd/private_user/
  <name>.service.tmpl        # what to run
  <name>.timer.tmpl          # when to run it
dot_local/bin/
  executable_<name>.tmpl     # the actual script invoked by the service
run_onchange_after_reload-systemd-user.sh.tmpl
                             # reloads + enables timers after any change
                             # (NOT YET in this repo; port from chezmoi-boco)
```

## Template guards on dependencies

Every file should refuse to render on machines missing its runtime deps. Unit files guard on both the binary being invoked **and** its upstream tool if any:

```gotmpl
{{ if and (lookPath "bd-track") (lookPath "<name>") -}}
[Unit]
Description=...
...
{{- end }}
```

Scripts guard on the top-level tool:

```gotmpl
{{ if lookPath "bd-track" -}}
#!/usr/bin/env bash
...
{{- end }}
```

If a guard fails, Chezmoi renders an empty file — which Chezmoi then treats as "unmanaged on this host" and skips. Don't add runtime `command -v` checks for dependencies that the template already guarded; only use runtime checks for truly optional components.

Path-valued data (`.filesystem.*` is home-relative in this repo) must be anchored before `stat`/`realpath`, or it resolves against chezmoi's working directory: `{{ if not (osIsAbs $p) }}{{ $p = joinPath .chezmoi.homeDir $p }}{{ end }}` (see `private_xsettingsd.service.tmpl`).

## `%h` over `{{ .chezmoi.homeDir }}` in unit files

Use systemd's `%h` specifier for home-dir paths in unit files rather than baking `{{ .chezmoi.homeDir }}` at Chezmoi apply time:

```gotmpl
ExecStart=%h{{ trimPrefix .chezmoi.homeDir (lookPath "<name>") }}
```

`%h` resolves at systemctl activation time. If the rendered unit is copied between users (or if `$HOME` changes), behavior stays correct. The `trimPrefix` makes `lookPath`'s absolute result home-relative so it composes with `%h`. Scripts themselves can use `$HOME` normally — the `%h` preference is specific to unit files.

## Desktop notifications

Desktop notifications differ by platform: `wsl-notify-send` on WSL, `notify-send` on native Linux. Don't branch inside every script:

- **Claude tooling and anything that wants one interface:** call `~/.claude/scripts/notify [--urgent] [--scenario …] [--sound …] <title> [body]`. It is rendered per host from the `.notifier` data variable and translates flags for that notifier.
- **Plain chezmoi-rendered scripts** can use `.notifier` directly:

```gotmpl
if command -v {{ .notifier }} >/dev/null 2>&1; then
    {{ .notifier }} "title" "message"
fi
```

`.notifier` (in `.chezmoi.yml.tmpl`) resolves by inspecting `.chezmoi.kernel.osrelease` and checking whether the WSL-specific wrapper source exists. The runtime `command -v` guard covers the corner case where the resolved tool isn't actually installed on the target. Units run from systemd reach the session's notification daemon (verified on GNOME/Wayland via a transient `systemd-run --user` unit).

## The reload script (to be ported)

On the BOCO dotfiles, `home/run_onchange_after_reload-systemd-user.sh.tmpl` reloads systemd and enables all timers after any change to files under the unit directory. It uses the `run_onchange_after_` prefix plus a hash-comments block at the top to make Chezmoi retrigger it when any source file changes:

```gotmpl
{{ range (glob (joinPath .chezmoi.sourceDir "private_dot_config/private_systemd/private_user/*")) -}}
# hash: {{ . }}: {{ include . | sha256sum }}
{{ end }}
```

The script is idempotent (`systemctl enable --now` is safe on already-enabled timers). **This repo doesn't have it yet**; until it's ported, enable new timers by hand (`systemctl --user daemon-reload && systemctl --user enable --now <name>.timer`).

**Known gap (BOCO version):** the reload script doesn't disable timers that were removed from source. If you delete a `.timer.tmpl` file, the enabled symlink in `~/.config/systemd/user/timers.target.wants/` will persist until manually removed with `systemctl --user disable <name>.timer`.

## Checklist for adding a new timer

1. Script at `dot_local/bin/executable_<name>.tmpl` with a `lookPath` template guard on the top-level tool it invokes. Scripts must be idempotent — they may fire before dependent state exists.
2. Service unit at `private_dot_config/private_systemd/private_user/<name>.service.tmpl`:
   - Guard on both the upstream tool and the script itself
   - `Type=oneshot` for periodic runs
   - `ExecStart=%h<home-relative-path>` using `trimPrefix` against `lookPath`
   - `Documentation=file://%h/.local/share/chezmoi/home/dot_local/bin/executable_<name>.tmpl` pointing at the source
3. Timer unit at `private_dot_config/private_systemd/private_user/<name>.timer.tmpl`:
   - Guard matches the service guard
   - `OnCalendar=...` or `OnBootSec=...` schedule
   - `Persistent=true` if the timer should fire on next login after a missed scheduled time
   - `WantedBy=timers.target` in `[Install]`
4. Run `chezmoi apply`, then reload and enable (by hand until the reload script is ported; see above).
5. Verify: `systemctl --user list-timers | grep <name>`.
6. Commit in the Chezmoi repo with a conventional message scoped `systemd` or the domain of the timer.

## Lingering (`enable_user_lingering`)

`loginctl enable-linger $USER` lets user timers fire without an active login session — required for housekeeping that should run regardless of whether the user is logged in. The per-host flag `enable_user_lingering` in `.chezmoi.yml.tmpl` tracks which machines should have it. (On the BOCO dotfiles this role was played by `enable_systemd_session_services`; in this repo that flag means something else — it selects the systemd-managed i3 session in `~/.xsession`.) The BOCO reload script tried `sudo loginctl enable-linger` on flagged hosts where lingering was not yet set, printing a hint rather than failing if sudo was unavailable.

## Related

- In-repo example: `private_dot_config/private_systemd/private_user/wallpaper.service.tmpl` + `private_wallpaper.timer.tmpl`
- BOCO examples and reload script (reference only): `~/Source/chezmoi-boco/home/dot_config/systemd/user/timew-{autostop,nudge}.{service,timer}.tmpl`, `~/Source/chezmoi-boco/home/run_onchange_after_reload-systemd-user.sh.tmpl`
- `.chezmoi.yml.tmpl` — hosts `.notifier`, `.enable_user_lingering`, and other cross-cutting data variables
- General Chezmoi patterns (`~/.local/bin` discipline, etc.): auto-memory `feedback-chezmoi-patterns.md` — to be migrated to `~/.claude/references/chezmoi-patterns.md` when the Chezmoi skill lands
