---
summary: Backlog of non-essential zbook improvements (ricing, security, resume) with done/open state
status: living checklist
updated: 2026-10-23
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
- [ ] Wake from suspend with the Keychron, MX Keys and MX Master (MH, 2026-10-23). Today only the power button, the
  lid and the ACPI sleep button wake zbook (deep/S3): `power/wakeup` is disabled on every USB hub, and the
  Bluetooth keyboard and mouse go through the internal USB Bluetooth controller. Likely a udev rule setting
  `power/wakeup=enabled` on the Keychron and the Bluetooth controller (and its hub path); Bluetooth wake in S3 may
  not work at all. Check battery drain overnight.

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
- [x] **Kitty colours: done 2026-10-24** (branch `ricing/kitty-colors`). Cause of the black zsh comments, as diagnosed
  2026-10-23: fsh's `comment = black,bold` on `#0D1926`, kitty does not brighten bold. Found by `tools/term-contrast`
  (checks the palette, fsh, zsh-autosuggestions, `LS_COLORS`, `less`, git and p10k against a kitty palette): `color8
  #262626` also hid autosuggestions, and the selection colours were Crayon Pony Fish's (`#140607` on `#2a1a1c`). Fixed:
  one palette, `current-theme.conf` = kitty's built-in Blazer (what was visible) with `color8 #647384` (3.65:1) and
  Blazer's selection; the Gogh `colors.conf`, the `theme.conf` link into a stale `dexpota/kitty-themes` clone and the
  vendored themes kitten are removed; fsh comments use colour 8 (`~/.config/zsh/fsh-styles.zsh`); pywal's include moved
  after the theme so a generated palette wins. Side fix: curly quotes in the `LS_COLORS` completion zstyle.
  **Open:** (1) trapd00r `LS_COLORS` has 12 colour pairs below 3:1 on this background (fixed 256-colour dims such as
  `ca` 17, archive parts 239, `.iso`/`.img` 124); they fail on any dark theme, so the fix is a palette-aware generator
  (`vivid`) in [theming.md](theming.md), not a per-entry patch. (2) Run `term-contrast --theme <name>` on any theme
  before adopting it. (3) The rest of the kitty assessment (the full merge-and-debug pass).
- [ ] Investigate browser options
- [ ] **hy3 and hyprbars via hyprpm, after the NVIDIA upgrade** (MH, 2026-10-23). hy3 (i3-style manual tiling) has an
  `hl0.56.0.1` tag with Lua dispatchers (`hl.plugin.hy3`); hyprbars gives per-window title bars (a window rule turns them
  off). Needs `hyprland-devel` (COPR, same 0.56.2) and a `hyprpm update` after every Hyprland update; not the COPR's
  `hyprland-plugin-*` packages (0.53 builds). Check first that hyprpm maps 0.56.2 to hy3's tag.
- [ ] **Solaar** (MH, 2026-10-23): install through the package manifest; configure the Logitech Bluetooth keyboards (the
  MX Keys S's screenshot key could be diverted to Print), and feed device battery levels to the bar.
- [ ] **Clipboard picker with image thumbnails in rofi** (MH, 2026-10-24): rofi dmenu rows take an icon
  (`label\0icon\x1f/path.png`); decode image entries (`cliphist decode <id>`) into a cache by entry ID and size
  `element-icon` large in the theme. fuzzel knows the same protocol but sizes icons to the text line. After the rofi theme
  is settled (theming). About 30 lines in `clipboard-history`.
- [ ] **hyprshutdown**: check that it works under uwsm before using it for `$mod+Shift+e` (D63).
- [x] **hyprlock: built 2026-10-24** (branch `wayland/hyprlock`; **MH's live lock/unlock test pending**). `lock-screen`
  picks hyprlock under Hyprland (`XDG_CURRENT_DESKTOP`), swaylock elsewhere; it returns on hyprlock's `onLockLocked` log
  line (so `swayidle -w` still holds suspend until locked) and falls back to swaylock if hyprlock dies first. Guards from
  testing: `flock` (two concurrent locks raced), and a hyprlock left over after an unlock is killed (0.9.6 hangs on a
  futex after "Unlocked, exiting!" on a headless sway; **watch whether real Hyprland does it too**). Config: blurred
  screenshot, clock, date, Blazer colours. `tools/lock-screen-test` covers it; recovery in
  [../runbooks/display-session-recovery.md](../runbooks/display-session-recovery.md).
- [ ] **hyprpaper** for the wallpaper picker (D63; installed, not configured).
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
