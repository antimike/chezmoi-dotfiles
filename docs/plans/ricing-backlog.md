---
summary: Backlog of non-essential zbook improvements (ricing, security, resume) with done/open state
status: living checklist
updated: 2026-10-18
---

# Backlog (aesthetic and quality-of-life work)

Merged from MH's scratch notes; "[x]" = done as part of the Claude Code migration ([../log/migration-steps.md](../log/migration-steps.md)).
Desktop work has two plans: [wayland-desktop.md](wayland-desktop.md) (compositors, SwayFX daily driver; first) and
[theming.md](theming.md) (themes, wallpapers, fonts, pickers; later).

## Side quests (parked by D50, 2026-10-18)
- [ ] Keybinding manifest in Lua, lazy.nvim-style units: [keybinding-manifest.md](keybinding-manifest.md)
- [ ] Try [`swindings`](https://github.com/sondalex/swindings) (maybe fork); the cheat sheet stays the main lookup tool
- [ ] Package map refactor (D32): [../open-items.md](../open-items.md#detail-package-map-refactor)
- [ ] Minimal niri, Hyprland, Wayfire configs (try the generated defaults first)

## Claude tooling
- [x] Editor preferences (vi mode), skills, home-rolled tooling (`bd-track`), beads install (dolt, uv, bun, bd)
- [x] Migrate Claude projects to new repos; review and migrate project memory
- [ ] Plugins: evaluate claude-mem and other memory plugins (deferred; see [../open-items.md](../open-items.md))
- [ ] Assess whether beads is still the best tool, and recent changes affecting configuration
- [ ] `claude-sandbox` repo: clone and set up (`claude-config` is done)

## Ricing
- [ ] Background images and colorschemes: [theming.md](theming.md)
- [x] Neovim config migration ([boco-merge.md](boco-merge.md), Phase 2, merged 2026-10-17)
- [ ] Wayland-compatible i3 replacement: SwayFX plus a compositor trial ([wayland-desktop.md](wayland-desktop.md))
- [ ] Status bar / tray, notification daemon, lock, idle: [wayland-desktop.md](wayland-desktop.md) (shared helper components)
- [ ] Kitty config update and assessment
- [ ] Investigate browser options
- [ ] Nix config derivations (exploration notes exist in the reference clone's `docs/`)

## Hardware checks
- [ ] Find which physical sockets are `DP-4..6`, the external ports wired to the NVIDIA card (plug a monitor into each
  port, then `for c in /sys/class/drm/card*-*; do echo $c $(cat $c/status); done`). Decides whether compositors need
  the NVIDIA device ([wayland-desktop.md](wayland-desktop.md), "GPUs"). MH, at the desk.

## Permissions and security
- [ ] Passwordless `sudo` and touch authorization with the YubiKey (`pam-u2f`, installed but not in any PAM stack yet; MH wants it, 2026-10-17). Do it as its own step, not with a display-manager change ([../runbooks/display-session-recovery.md](../runbooks/display-session-recovery.md)); polkit prompts then accept a touch too.
- [ ] New SSH keys for GitHub and other services (GitHub already works via the YubiKey; others open)
- [ ] Review contents of GPG backups; see also [../runbooks/gpg-and-signing.md](../runbooks/gpg-and-signing.md)

## Chezmoi
- [x] Migration branch work merged to `main` (D26 in [../decisions.md](../decisions.md))
- [ ] Templatize all machine-specific logic ([boco-merge.md](boco-merge.md) Guards)

## Resume
- [x] Resume repos cloned and pushed
- [ ] Assess and begin building out the new resume

## Folded from MH's ricing notes (2026-10-17)

Where each item of MH's untracked `ricing.md` went, for review against the original. "Done" and "changed" flag items
that were already handled or that differ from the old plan.

| Note | Now in | State |
|---|---|---|
| background images, pywal | [theming.md](theming.md) "Wallpapers", "Palette generation" | pywal's maintenance status flagged; generator to be compared |
| lush? (nvim) | [theming.md](theming.md) "nvim" | inverted variant dropped as a default (contrast handled by the generator) |
| sleep timeout / power settings | [wayland-desktop.md](wayland-desktop.md) "Daily-driver features" | timings from MH at that step |
| password picker | same | own rofi/fuzzel script that bypasses `pass -c` (D40); the `~/.local/bin/pass` wrapper still guards CLI use |
| clipboard picker | same | **mostly done**: clipboard stack + `clipboard-history` fzf picker; rofi front end and binding open |
| i3 -> Sway | [wayland-desktop.md](wayland-desktop.md) | **changed:** SwayFX full port, plus a niri/Hyprland/Wayfire trial |
| compositor? | same, "Compositors" | **resolved:** the compositor is the WM under Wayland; picom goes away |
| dunst (alternatives?) | same, helper table, open question 3 | **conflict:** D29 chose dunst; SwayNotificationCenter noted as the alternative |
| passwordless sudo via YubiKey | "Permissions and security" above | unchanged (`pam-u2f` already installed) |
| greeter (lightdm?) | [wayland-desktop.md](wayland-desktop.md) "Greeter" | GDM kept through the trial; lightdm installed but unused |
| keybind helper (rofi?) | same, "Daily-driver features" | `wlr-which-key` leader menus + a rofi cheat sheet |
| polybar replacement, system tray | same, waybar | polybar config is in `antimike/i3-config-mbp`; waybar's tray module replaces stalonetray |
| icon config / styling | [theming.md](theming.md) "Core pattern" | |
| redshift replacement | [wayland-desktop.md](wayland-desktop.md) helper table | gammastep (D29) |
| dropdown terminal | same, "Daily-driver features" | kitty `--class dropdown` launcher already exists |
| keybinds: opacity, notifications, volume/brightness | same | scripts in `antimike/i3-config-mbp`; `$audio_intput` typo in the i3 config |
| lock screen | same | swaylock (gtklock as the prettier alternative) |
| keyboard backlight | same | `brightnessctl` |
| hibernation? | same | **blocked** by Secure Boot lockdown (checked) |
| fonts | [theming.md](theming.md) "Fonts" | |
| process cap, lockfile script, blink.cmp vs nvim-cmp, luarocks, `:MasonToolsInstall`, `:checkhealth mason`, `magick loadable` | [boco-merge.md](boco-merge.md) Phase 2 | **done** (MH confirmed obsolete); the general per-app cap returns as uwsm's app slices |
