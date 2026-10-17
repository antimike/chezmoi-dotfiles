---
summary: Plan for a Sway (Wayland) session beside GNOME on zbook, mapping the i3/X11 setup and preserving the i3 config via a shared template fragment
status: planned, no steps done
updated: 2026-10-15
---

# Sway session plan

Desktop-environment work on zbook, separate from the Claude Code migration (see [../log/migration-steps.md](../log/migration-steps.md)).
Scratch backlog: [ricing-backlog.md](ricing-backlog.md).

**Current state of zbook:** Fedora 44, GNOME on Wayland (`XDG_SESSION_TYPE=wayland`, `XDG_CURRENT_DESKTOP=GNOME`). i3 and polybar are installed but unused on this machine.

**Dotfiles:** chezmoi (`~/.local/share/chezmoi`, remote `antimike/chezmoi-dotfiles`). It already contains a set of X11/i3 session units: `xsession.target`, `xsettingsd.service`, the xss-dimmer, the wallpaper timer and redshift. Their install lists are in `.chezmoidata/systemd.yaml` and per-unit settings in `.chezmoitemplates/systemd/*.yaml`.

---

## Sway session

### Goal

Add a Sway session alongside GNOME, chosen at the login screen. Its helper programs run as systemd user units scoped to the Sway session, following the same pattern as the existing i3/X11 units.

### Design principle: scope units by session, not by host

Because GNOME and Sway will coexist on one machine, **don't exclude units per host** in chezmoi. Instead:

- Deploy all unit files.
- Each unit has `PartOf=` and `WantedBy=` set to its session's target, so it starts and stops with that session and never runs under GNOME.
- The existing X11 units already behave this way. For example, `xsettingsd.service` has no `[Install]` section and only runs when the i3 session's target starts it, so it's inert on a GNOME-only machine.

### Session plumbing

- **`sway-systemd`** (Fedora package, 0.4.1 in F44) provides `sway-session.target`, tied to `graphical-session.target`. It passes Sway's environment (`WAYLAND_DISPLAY`, `SWAYSOCK`, `XDG_CURRENT_DESKTOP`, …) to systemd and handles XDG autostart. Before writing anything by hand, check that it's still the recommended approach.
- **Without the package**, the equivalent in the Sway config is:
  ```
  exec "systemctl --user import-environment DISPLAY WAYLAND_DISPLAY SWAYSOCK XDG_CURRENT_DESKTOP; systemctl --user start sway-session.target"
  ```
  plus a hand-written `sway-session.target` with `BindsTo=graphical-session.target`.
- **Portals:** `xdg-desktop-portal-wlr` (0.8.4) for screen sharing and screenshots under wlroots.

### Mapping the existing X11/i3 pieces to Sway

All packages listed are available in Fedora 44 (versions checked 2026-10-08).

| Current X11 / i3 piece | Sway counterpart | Notes |
|---|---|---|
| `xsession.target` | `sway-session.target` (via `sway-systemd`) | Sway units use `PartOf=`/`WantedBy=sway-session.target`. |
| `xsettingsd.service` | `gsettings` in the Sway config; optionally `xsettingsd` (1.0.2) for XWayland apps | Native Wayland GTK apps read `org.gnome.desktop.interface` (gtk-theme, icon-theme, cursor-theme, font-name) via `gsettings`, e.g. `exec_always gsettings set org.gnome.desktop.interface gtk-theme …`. xsettingsd only helps legacy apps running through XWayland. The current unit's reload logic (`Xft.dpi`, `i3-msg restart`, polybar) doesn't carry over: Wayland scales per output (`output * scale`), and Sway reloads with `swaymsg reload`. |
| polybar | **waybar** (0.15.0) | polybar is X11-only. |
| `xss-dimmer` / screen locker | **swayidle** (1.9.0) + **swaylock** (1.8.6) | swayidle handles dimming, locking and DPMS via timeouts. |
| Wallpaper timer (pywal + feh/hsetroot) | Same timer; **swaybg** (1.2.2) in place of feh/hsetroot | pywal works unchanged. Only the "set background" command changes. |
| redshift | **wlsunset** (0.4.0) or **gammastep** (2.0.11) | gammastep is the redshift fork with Wayland support; wlsunset is a smaller native tool. |
| xrandr output setup | **kanshi** (1.9.0) | Output profiles that switch automatically with what's plugged in. |
| Notification daemon (GNOME provides one today) | **mako** (1.11.0) or **dunst** (1.13.2, supports Wayland) | Needed under Sway for `notify-send` to work. The chezmoi `notifier` variable stays `notify-send` either way; dunst/mako are daemons, `notify-send` is the client. |

### chezmoi structure

- Add Sway entries to `.chezmoidata/systemd.yaml`: install lists, using the `dnf:` / `pipx:` keys already in use.
- Add `.chezmoitemplates/systemd/<unit>.yaml` per-unit settings, mirroring the X11 ones.
- Render unit templates from absolute paths. Anchor home-relative `.filesystem.*` values with `joinPath .chezmoi.homeDir` behind an `osIsAbs` guard, as done for `xsettingsd.service` in chezmoi commit `dcbb3d4`. Otherwise `stat` and `realpath` resolve against chezmoi's working directory.
- Templates that run commands at render time must use `.chezmoitemplates/safe-output.sh` (chezmoi commit `31644a7`), so a broken tool can't abort `chezmoi apply`.
- Package installs go through chezmoi `run_onchange_` installers (a Fedora package list), consistent with the tooling plan in [migration-steps.md](../log/migration-steps.md) (step 6).

### Steps (not yet scheduled)

- [ ] 1.1 Install `sway`, `sway-systemd`, `xdg-desktop-portal-wlr` via a chezmoi Fedora package installer. Confirm a Sway entry appears at the login screen next to GNOME.
- [ ] 1.2 Minimal Sway config in chezmoi (`private_dot_config/sway/config.tmpl`): start the session target, `gsettings` theming, output scale.
- [ ] 1.3 Units scoped to the Sway session, one commit each: waybar, mako or dunst, swayidle (+ swaylock), kanshi, wlsunset or gammastep, wallpaper (swaybg + existing pywal timer).
- [ ] 1.4 Decide on xsettingsd under Sway (only if XWayland apps look wrong).
- [ ] 1.5 Verify that switching between GNOME and Sway at the login screen leaves no Sway units running under GNOME (`systemctl --user list-units --state=active`).
- [ ] 1.6 (after Phase 0a of the chezmoi restructure) Split the i3 config into a shared fragment plus `i3`/`sway` wrappers; verify the i3 output is unchanged.
- [ ] 1.7 Port the X-specific i3 items in the table above, one commit each: `app_id` rules, `i3-input` prompt wrapper, `grim`/`slurp` screenshot, swayidle/swaylock, input settings, then waybar.

### i3 config to Sway: preserving the existing setup (added 2026-10-15)

**Feasibility: high.** Sway reads i3 config syntax and speaks the i3 IPC protocol, so most of `private_dot_config/i3/config.tmpl` (355 lines, driven by the `.i3.*` chezmoi data) carries over: bindings, modes, workspaces, `workspace_layout tabbed`, marks, `focus_follows_mouse`, floating rules and the built-in gaps (inner/outer/top/left/right, `smart_gaps`, `smart_borders`, `hide_edge_borders`). Sway has gaps natively, so i3-gaps is not needed. The work is in the X-specific pieces, listed below. Packages checked in Fedora 44: `rofi` 2.0.0 (native Wayland), `dunst` 1.13.2, `waybar` 0.15.0, `swaylock` 1.8.6, `grim` 1.5.0, `slurp` 1.5.0, `wl-clipboard` 2.2.1, `wtype` 0.4, `fuzzel` 1.14.0.

**Approach: one source of truth for both WMs.** Do not fork the config. Split `config.tmpl` into a shared fragment (`.chezmoitemplates/wm/common`: keys, modes, workspaces, gaps, floating rules, all driven by the existing `.i3.*` data) plus thin `i3/config.tmpl` and `sway/config.tmpl` wrappers that include it and add WM-specific lines. Keep the i3 output byte-identical (compare `chezmoi cat` before and after the split).

| i3 config item | Change for Sway |
|---|---|
| `set_from_resource $fg/$bg` (pywal via Xresources) | `include` the file pywal writes for Sway (`~/.cache/wal/colors-sway`), or `set $fg/$bg` from a generated include. |
| `for_window [class="..."]` rules (Firefox sharing indicator, `dropdown`, `Nm-connection-editor`, `Shadow`) | Use `app_id` for native Wayland windows; `class` still works for XWayland apps. Find real values with `swaymsg -t get_tree`. `window_role` rules (PictureInPicture) need a `title` match instead. |
| `i3-input -F ... -P prompt` (7 bindings: screenshot filename, marks, swap/move to mark, rename workspace) | No Sway equivalent. Write one small prompt wrapper (`rofi -dmenu -p` or `fuzzel --dmenu`) that runs `swaymsg "<template with %s>"`; replace all 7 bindings with it. |
| `i3-nagbar` (exit confirm), `i3-msg exit` | `swaynag`, `swaymsg exit`. |
| `exec_always ... xss-lock` | `swayidle` + `swaylock` (units in 1.3). |
| `$refresh_i3status` (`killall -SIGUSR1 i3status`) on media keys | waybar signal (`pkill -SIGRTMIN+N waybar`) or drop if the media module polls. |
| `~/bin/screenshot` (`maim` + `xclip`) | Rewrite with `grim` + `slurp` + `wl-copy`; same arguments (`desktop`, `window [name]`) so the bindings stay as they are. |
| `dunstctl` bindings, `notify-send` | Unchanged: dunst runs on Wayland. |
| `rofi` launchers, `kitty`, `playerctl`, brightness script, `cmus` | Unchanged (rofi 2.0 is Wayland-native; check the brightness script for `xbacklight`/`xrandr`). |
| `i3altlayout` (python script) | Probably works: `i3ipc` also talks to Sway via `SWAYSOCK`. Test. |
| `betterlockscreen`, `i3-wpd` | X-only; `swaylock` replaces the locker. Decide about `i3-wpd` when inspecting it. |
| Input (keyboard layout, repeat, touchpad) | Sway `input` blocks replace `setxkbmap`/`xset`/`xinput`; check the session script (`.xsession`) for what it set and port each item. |
| polybar | **Largest item.** polybar is X11-only; rebuild as waybar modules (workspaces, clock, battery, network, volume, weather) with the same colors via pywal. Note: no `polybar` directory is in `private_dot_config` in chezmoi today; locate the live config first. |

Order of work: 1.1 and 1.2 (session boots), then the shared-fragment split, then the table items above in the order dunst/rofi (no change), screenshot, `i3-input` replacement, idle/lock, waybar last.

**Cross-plan constraints:** new files go in `home/` once the chezmoi restructure (Phase 0a in [boco-merge.md](boco-merge.md)) is done, so do that first or the paths change mid-way. Wayland-specific files do not need a WSL guard; scope by session (units) and by installed tool.

### Open questions

1. ~~mako or dunst?~~ **Recommend dunst**: it is already configured (`private_dot_config/dunst`), runs on Wayland, and keeps the `dunstctl` bindings and your styling unchanged.
2. ~~wlsunset or gammastep?~~ **Recommend gammastep**: a redshift fork that reads the same settings, so the existing redshift config ports directly. wlsunset is simpler but would mean re-expressing the config.
3. Keep the i3/X11 units in chezmoi long-term, or retire them once Sway is established? (Session-scoping keeps them inert, so there is no urgency; the shared config fragment above keeps i3 usable.)
