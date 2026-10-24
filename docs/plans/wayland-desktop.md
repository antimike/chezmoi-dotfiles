---
summary: Wayland desktop plan for zbook: multi-compositor trial (SwayFX full port; niri, Hyprland, Wayfire minimal) under uwsm, shared helper units, daily-driver features, greeter
status: steps 0-3 done and merged (2026-10-17); functional daily-driver checklist first (D50, 2026-10-18); uwsm adopted (D38)
updated: 2026-10-23
---

# Wayland desktop plan

Desktop work on zbook, separate from the Claude Code migration ([../log/migration-steps.md](../log/migration-steps.md)).
Theming (theme bundles, wallpapers, palette generation, pickers for fonts and themes) is a separate, longer-running
project: [theming.md](theming.md). Loose items: [ricing-backlog.md](ricing-backlog.md).

**Priority (MH, 2026-10-17):** make SwayFX a usable daily driver first. Theming comes after, as time allows.

## Current state of zbook (checked 2026-10-17)

- Fedora 44, GNOME on Wayland. **GDM** is the active display manager; `lightdm` is installed but unused.
- i3 and polybar are installed but unused. The i3 config is deployed (`~/.config/i3/config`) but **broken**: the helper
  scripts it calls (`~/.config/i3/bin/set-pulseaudio-volume.bash`, `adjust-brightness.bash`, `xss-lock`, kitty's
  `open-notes.bash`) and the polybar config are not in chezmoi or on this machine; they are in MH's
  **`antimike/i3-config-mbp`** repo (below). Under D48 i3 is either fixed or removed (see "Keeping i3 working" below).
- Already in chezmoi for Wayland: the clipboard stack (`clipboard-stack-wayland.target` running `cliphist@text`,
  `cliphist@image` and `wl-clip-persist`; the clipse installer), started explicitly by a Wayland session, never by GNOME.
- Already installed: `dunst`, `rofi` 2.0 (Wayland-native), `kitty` 0.47, `cliphist`, `wl-clipboard`, `brightnessctl`,
  `xdg-desktop-portal-gtk`, `gnome-keyring`, `pinentry-gnome3`, `pam-u2f`.
- Secure Boot is on and swap is zram only (8G). Both matter for hibernation (below).
- Existing X11/i3 session units (`wm-helpers-x11.target`, `xsettingsd`, xss-dimmer, wallpaper timer, redshift, polybar,
  picom, autorandr) stay; they are scoped to the i3 session and inert elsewhere.

## Source repos for the i3 setup (MH, 2026-10-17)

All public `antimike` repos. i3-config-mbp, i3wm-configuration and arcolinux-i3wm are cloned to `~/Source/antimike/`
(2026-10-17, submodules not initialized). Surveyed by file list only; read each script before porting.

| Repo | Last push | What it holds | Use here |
|---|---|---|---|
| **i3-config-mbp** | 2023-07 | The i3 config's home: `bin/` (volume, brightness, screenshot, `open-notes`, xss-lock/dimmer, polybar launchers, `set-background`, `set-lockscreen`, `set-lightdm-background`, `system-tray.sh` = stalonetray), `bin/widgets/` (fzf `font-picker`, kitty `theme-picker`, `rofi-wifi`, `rofi-mediaplayer`), `bin/utils/` (`sort-images-by-color`, `generate-color-profile.py`), `dotfiles/polybar.conf`, xkb layouts (not relevant on zbook, MH), systemd units (the source of chezmoi's X11 units) | **Primary port source.** Scripts get Wayland rewrites (`xdotool`, `xclip`, `maim` are X11). |
| i3-python | 2022-03 | i3ipc and playerctl examples (`player-manager.py`, `notify.py`) | Mine for the media-player tooling. |
| i3altlayout | 2021-04 | Fork of deadc0de6/i3altlayout (i3ipc auto-split) | Test on SwayFX; not needed on niri/Hyprland. Submodule of i3-config-mbp. |
| i3-wpd | 2020-11 | Fork of jomiq/i3-wpd (X11 wallpaper daemon) | Superseded by [theming.md](theming.md); check for ideas only. Submodule of i3-config-mbp. |
| i3wm-configuration, arcolinux-i3wm | 2021-09 (last commits) | Forks of others' dotfiles, mined for ideas | Reference, but **mining pass wanted** (MH): list their scripts and pick what is worth porting. |
| i3lock-fancy | 2021-09 | Fork of an X11 locker | Not needed (swaylock/gtklock). |

## GPUs: compositors on the Intel iGPU, NVIDIA kept for compute

Checked 2026-10-17. Intel UHD 630 (`0000:00:02.0`, currently `card1`) and NVIDIA Quadro T1000 Mobile (`0000:01:00.0`,
`card0`; proprietary 595.80 via akmod, `nvidia-drm.modeset=1`). `nvidia-smi` reports runtime D3 power-down "Not
supported", so the NVIDIA card stays powered (P8, about 1 W idle) whatever the compositor does.

- **Feasible (MH asked; "IBM" read as Intel):** the compositors render on Intel; NVIDIA stays free for CUDA and is used
  by GUI apps only on request (PRIME offload: `__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia`, or
  `switcherooctl launch`).
- **Port wiring:** the laptop panel, `HDMI-A-1..3` and `DP-1..3` are on Intel; **`DP-4..6` are on NVIDIA**. Which
  physical sockets those are is unknown (test by plugging a monitor in). A monitor on an NVIDIA port only works if the
  compositor also opens the NVIDIA device (Intel as primary renderer, NVIDIA for scanout); that makes Sway/SwayFX need
  `--unsupported-gpu`.
- **How, per compositor:** wlroots-based (SwayFX, Wayfire): `WLR_DRM_DEVICES`, Intel first; Hyprland:
  `AQ_DRM_DEVICES`; niri: `render-drm-device` in its config. **Pitfall:** `card0`/`card1` numbering can swap between
  boots, and the stable `/dev/dri/by-path/pci-0000:00:02.0-card` contains colons, which break the colon-separated
  `WLR_DRM_DEVICES` list. Fix: a udev rule creating colon-free symlinks `/dev/dri/igpu` and `/dev/dri/dgpu`. **Done
  2026-10-17** (`run_onchange_install-udev-dri-symlinks.sh.tmpl`): the rule matches the kernel driver (`i915|xe`,
  `nvidia|nouveau`), not PCI addresses, so it is not zbook-specific; it cannot separate an AMD iGPU from an AMD dGPU.
- Set the variables in the uwsm environment so every compositor gets them.

## Compositors

| Compositor | Role in the trial | Fedora 44 | Notes |
|---|---|---|---|
| **SwayFX** | **Full i3 port; daily driver** | COPR `swayfx/swayfx` (D45) | Sway fork: i3 config syntax and i3 IPC (so `i3altlayout` and i3ipc scripts keep working), plus blur, rounded corners, shadows, inactive dimming. Risk: trails upstream Sway (1.11 in Fedora). **The COPR package conflicts with Fedora's `sway`** (it ships `/usr/bin/sway` and provides `sway`), so the two cannot be installed side by side; the fallback is `sudo dnf swap swayfx sway` with the same config, minus the SwayFX-only lines. |
| **niri** | Minimal config | Official (26.04) | Scrolling tiling, KDL config, own IPC (`niri msg`), XWayland through `xwayland-satellite` (packaged). Stable, animated. |
| **Hyprland** | Minimal config | COPR `sdegler/hyprland` (D45) | Most eye candy; frequent breaking config changes; i3-style manual tiling only through the `hy3` plugin, which must match the exact Hyprland version. |
| **Wayfire** | Minimal config | Official (0.10.1) | Effects-heavy (cube, wobbly); tiling through the `simple-tile` plugin that ships in the `wayfire` package. Basic auto-tiling only: an eye-candy reference more than a contender. |

Considered and set aside: river (0.4 split window management into separate clients; that ecosystem is still thin),
scroll (Sway fork with scrolling layout; not packaged), miracle-wm, COSMIC (a full DE), labwc (stacking).

**Minimal config** means: terminal, launcher, the ~10 most-used bindings, outputs, and the shared helper target. No port
of the i3 config. A runner-up can stay installed after the trial if its config stays minimal.

## Session plumbing: uwsm plus one shared helper target

- **uwsm** (Universal Wayland Session Manager, github.com/Vladimir-csp/uwsm) launches each compositor as systemd units
  (`wayland-wm@.service`, `wayland-session@.target`, bound to `graphical-session.target`), imports the environment and
  shuts down cleanly. It officially supports sway, wayfire, hyprland and niri. `uwsm app -- <cmd>` runs each app in its
  own unit under `app-graphical.slice`, which gives per-app resource control (the general form of the old
  "process cap" note).
- **Install:** Python, but built with **meson**, not pip. Dependencies are packaged (`python3-dbus`, `python3-pyxdg`;
  optional `whiptail`, `inotify-tools`, `libnotify`). The `wayland-sessions/*.desktop` entries GDM reads must be in a
  system directory, so it is a sudo install to `/usr/local`, via a pinned tag+commit installer in the style of
  `run_onchange_install-wl-clip-persist.sh.tmpl`. Not in Fedora's repos. The Hyprland COPR ships an older uwsm (0.24.3
  on 2026-10-17; upstream 0.27.1): do not install that one.
- **Overlap:** with uwsm, do not use `sway-systemd` or start `niri.service` directly; one session model for all four.
- **"Helpers"** means the systemd user services that run per-session background programs for whichever compositor is
  running (clipboard history now; bar, notifications, idle, night light, outputs, wallpaper, polkit agent later). The
  target only groups them; scripts run from keybindings are not helpers. Naming: `wm-helpers-<scope>.target` (D47).
- **Shared helpers:** a hand-written `wm-helpers-wayland.target` (`BindsTo=graphical-session.target`, no `[Install]`).
  Every compositor's config starts it. Shared units (bar, notifications, idle, gamma, outputs, wallpaper, clipboard)
  use `PartOf=`/`WantedBy=wm-helpers-wayland.target`. GNOME also starts `graphical-session.target`, which is why
  helpers cannot hang off that directly. This keeps the existing rule: **scope units by session, not by host.**
  `clipboard-stack-wayland.target` joins it (`Wants=` from the new target).
- Portals: `xdg-desktop-portal-wlr` for screen sharing and screenshots on wlroots compositors; `xdg-desktop-portal-gtk`
  (installed) for file pickers. niri and Hyprland want their own portal backends (`-gnome` and `-hyprland`); check each
  in its minimal config.

## Shared helper components (choices and trade-offs)

All work across the four compositors unless noted (they use standard Wayland protocols such as layer-shell). Fedora
versions checked 2026-10-08 and 2026-10-17.

| Need | Recommendation | Alternatives | Trade-off |
|---|---|---|---|
| Bar + tray | **waybar** 0.15 (tray is a built-in module: no stalonetray) | ironbar, eww, quickshell (none packaged) | waybar has sway, hyprland, niri and river modules, CSS styling and a tray; the others are more programmable but heavier to maintain. Rebuild the polybar modules (workspaces, clock, battery, network, volume, weather) here. |
| Notifications | **dunst** 1.13.2 (installed; D29 confirmed by MH 2026-10-17) | SwayNotificationCenter 0.12.6, mako | dunst: global keybindings act on the current popup (`dunstctl action`, `dunstctl context` opens a rofi menu of its actions and links, `close`, `close-all`, `history-pop`); works in i3 and SwayFX, so the shared fragment keeps one set of bindings; runtime-toggled rules (`dunstctl rule`) and graded pause levels; theming through `dunstctl reload <files>` with a generated file. History: a rofi/fuzzel **history browser** (step 8). Waybar status: a custom module on `dunstctl count history` / `is-paused`. swaync was considered: a clickable panel with widgets and inline reply, but Wayland-only, and its README documents no command to act on the latest popup from a keybinding. |
| Lock screen | **swaylock** 1.8.6 | gtklock 4.0 (packaged, CSS-themed), swaylock-effects (blur/clock; not packaged), hyprlock (COPR) | swaylock is minimal and robust; gtklock looks better and stays packaged. Both use ext-session-lock, so either works across compositors. |
| Idle / DPMS | **swayidle** 1.9 | hypridle (COPR) | swayidle drives dim, lock and output power off from timeouts, plus `before-sleep` lock. |
| Launcher, dmenu prompts | **rofi** 2.0 (keep) | fuzzel 1.14, wofi | rofi keeps all existing themes and modi. fuzzel is faster and simpler; keep it in mind for prompts. |
| Night light | **gammastep** (D29) | wlsunset | Needs the wlr gamma-control protocol; check Hyprland (has its own `hyprsunset`) and niri in their minimal configs. |
| Outputs | **kanshi** 1.9 | wdisplays (GUI), `wlr-randr` | niri configures outputs itself; kanshi may be unnecessary there. |
| Wallpaper | **swaybg** 1.2.2 | swww (transitions; not packaged) | Wallpaper selection and palettes belong to [theming.md](theming.md); here only "set the background per output". |
| Volume/brightness OSD | **wob** 0.15 | swayosd (not packaged), dunst progress notifications | wob is a tiny bar fed from a pipe; dunst's progress hint needs nothing new. |
| Polkit agent | **mate-polkit** 1.28 (GTK3; MH agreed, provided it can be themed: it follows the GTK3 theme) | lxpolkit, xfce-polkit (GTK, minimal), polkit-kde / lxqt-policykit (Qt), hyprpolkitagent (COPR); polkit-gnome is not in F44 | **Missing from the old plan:** without an agent, GUI apps cannot ask for admin rights outside GNOME (GNOME Shell has its own). mate-polkit is maintained, GTK (matches the theming), and shows PAM messages such as a pam-u2f touch prompt. Runs as a helper unit. |
| Keyring / pinentry | gnome-keyring + pinentry-gnome3 (installed) | | Check that both work outside GNOME (pinentry for `pass` and the YubiKey). |
| Logout menu | swaynag (built in) | wlogout, nwg-bar (packaged) | Optional eye candy. |

## SwayFX: porting the i3 config

**Feasibility: high.** Sway/SwayFX read i3 config syntax and speak the i3 IPC protocol, so most of
`home/private_dot_config/i3/config.tmpl` (driven by the `.i3.*` chezmoi data) carries over: bindings, modes, workspaces,
`workspace_layout tabbed`, marks, `focus_follows_mouse`, floating rules and the gaps settings.

**One source of truth for i3 and SwayFX.** Split `config.tmpl` into a shared fragment (`home/.chezmoitemplates/wm/common`)
plus thin `i3/config.tmpl` and `sway/config.tmpl` wrappers that add WM-specific lines (SwayFX effects go in the sway
wrapper). Keep the i3 output byte-identical (compare `chezmoi cat` before and after the split).

**Keeping i3 working (D48, D49).** The repo must not ship a broken i3 config, so the port fixes i3 along the way. i3
stays for MH's old MacBook Pro (a possible future X11 host); zbook is the test bed until then. Rules:
- Helper scripts both WMs need (volume, brightness, keyboard backlight, OSD, notes launcher, screenshot) are ported
  **once** to `~/.local/bin` and work in X11 and Wayland sessions, like `clip` (check `$WAYLAND_DISPLAY` only where the
  tools differ; `wpctl`, `brightnessctl` and `dunstctl` do not). The shared fragment calls them, so i3 and SwayFX use the
  same paths; nothing new goes into `~/.config/i3/bin/`. They must not assume zbook's hardware: backlight and
  keyboard-backlight device names (Apple's differ) come from host data or detection.
- i3-only helpers found in the mining pass (step 6) are ported for i3 or dropped together with their bindings; none stay
  referenced but missing.
- i3's done check is an **i3 login test** on zbook (none yet), run once the steps above have touched its config.

| i3 config item | Change for Sway |
|---|---|
| `set_from_resource $fg/$bg` (pywal via Xresources) | `include` a generated colors file. Interim: pywal's `~/.cache/wal/colors-sway`; long term the theming cache ([theming.md](theming.md)). |
| `for_window [class="..."]` rules (Firefox sharing indicator, `dropdown`, `Nm-connection-editor`, `Shadow`) | `app_id` for native Wayland windows; `class` still works for XWayland. Find values with `swaymsg -t get_tree`. `window_role` rules (PictureInPicture) need a `title` match. |
| `i3-input -F ... -P prompt` (7 bindings: screenshot filename, marks, swap/move to mark, rename workspace) | One small prompt wrapper (`rofi -dmenu -p`) that runs `swaymsg "<template with %s>"`; replace all 7. |
| `i3-nagbar` (exit confirm), `i3-msg exit` | `swaynag`, `swaymsg exit` (under uwsm: `uwsm stop`). |
| `exec_always ... xss-lock`, `loginctl lock-session` | swayidle + swaylock; `loginctl lock-session` keeps working once swayidle handles the `lock` event. |
| `$refresh_i3status` on media keys | waybar signal (`pkill -SIGRTMIN+N waybar`), or drop if the module polls. |
| `~/bin/screenshot` (`maim` + `xclip`) | **Done 2026-10-22:** rewritten as `~/.local/bin/screenshot` (`grim` + `slurp` + `wl-copy`, `maim` + `xclip` on X11); `window [NAME \| --ask]`, `desktop`. `--ask` (rofi) replaced the screenshot `i3-input` prompt. |
| Volume keys (`set-pulseaudio-volume.bash`) and brightness / keyboard backlight keys (`adjust-brightness.bash`) | Scripts are in i3-config-mbp; port or replace with `wpctl`/`pactl` and `brightnessctl` (`-d '*kbd_backlight*'` for the keyboard), feeding the OSD. Also fixes an existing bug: line 80 defines `$audio_intput`, but the mic-mute binding uses `$audio_input`. |
| `dunstctl` bindings, `notify-send` | Unchanged. |
| `rofi` launchers, `kitty`, `playerctl`, `cmus` | Unchanged. |
| `i3altlayout` (python, i3ipc) | Probably works through `SWAYSOCK`. Test. |
| `betterlockscreen`, `i3-wpd` | X-only; swaylock replaces the locker. Decide about `i3-wpd` when inspecting it. |
| Input (keyboard layout, repeat, touchpad) | Sway `input` blocks replace `setxkbmap`/`xset`/`xinput`; port each item from `.xsession`. |
| `exec_always ~/.xsession` | Drop for Sway; its jobs move to units or `input`/`output` blocks. |
| polybar | **Largest item**; rebuilt as waybar (config to be located first). |

## Daily-driver features (from MH's notes, 2026-10-17)

- **Lock screen, idle, power:** swayidle timeouts (dim, lock, screen off), `before-sleep` lock, logind lid and
  power-button behavior. MH to give preferred timings at that step.
- **Hibernation: blocked (checked 2026-10-17).** Secure Boot puts the kernel in lockdown `integrity` mode, which
  disables hibernation (`/sys/power/disk` reads `[disabled]`; `/sys/power/state` offers only `freeze mem`), and zram
  swap could not hold an image anyway. Options: suspend only (recommended); or a disk swap file plus disabling Secure
  Boot (not recommended).
- **Keyboard backlight and volume/brightness keys:** `brightnessctl` + `wpctl`, with an OSD (table above).
- **Password picker (own script, MH 2026-10-17; passmenu rejected on looks and function):** rofi or fuzzel lists the
  entries under `~/.password-store` (`*.gpg`, path minus extension); actions: copy password, copy OTP (`pass otp`),
  type it (`wtype`, never touches the clipboard), copy another field (e.g. `user:`).
  - **Defence in depth:** the picker never calls `pass -c`. It runs `pass show <entry>` (the real binary, by absolute
    path) and pipes the first line straight into `wl-copy --sensitive`. The secret never sits in a shell variable,
    argv or a temp file. CLI use of `pass -c` stays covered by the `~/.local/bin/pass` wrapper (2026-10-16,
    [../open-items.md](../open-items.md)).
  - **Clearing:** after `PASSWORD_STORE_CLIP_TIME` (45 s), clear the clipboard only if it still holds the secret
    (compare a hash of `wl-paste -n` with one taken at copy time), so a newer copy is not wiped.
  - **To test in the Sway session (clipboard stack is still untested end to end):** that cliphist skips the copy, and
    that `wl-clip-persist` does not bring back a cleared password (it re-offers the last selection when its source
    goes away, which is its purpose). If it does, the picker keeps `wl-copy` serving until the clear, or the
    wl-clip-persist options exclude sensitive offers.
  - `rofi-pass` is X11-only; `tessen` is not packaged; upstream `passmenu` was rejected.
- **Clipboard picker:** backend and an fzf picker exist (`clipboard-history`, `clipboard-history-audit`); add a rofi
  front end or run `clipboard-history` in a floating kitty, and bind it.
- **Dropdown terminal:** kitty with `--class dropdown` exists (`kitty/bin/launch_session`); under Sway use `app_id`
  `dropdown` plus the scratchpad (`scratchpad show` toggle) and a size/position rule.
- **Keybindings:** opacity up/down (`opacity plus 0.05` / `minus`), dismiss notification and notification history
  (existing `dunstctl` bindings).
- **Keybinding helper (which-key):** `wlr-which-key` (github.com/MaxVerevkin/wlr-which-key): a which-key.nvim-style
  popup with nested submenus, each entry running a command; YAML config with font, color, border and corner-radius
  theming. Needs layer-shell (all four compositors; verify on niri and Hyprland). Install with
  `cargo install --locked`, pinned.
- **Keybinding manifest (generate, never parse; MH wants no drift).** *Parked by D50 (2026-10-18); a Lua redesign is
  discussed in [keybinding-manifest.md](keybinding-manifest.md).* **One `keybindings` data tree for every app**
  (MH, 2026-10-17): compositors, wlr-which-key, zsh (folding in the D33 draft), kitty, nvim, with a section per app.
  It can be split into several files under `home/.chezmoidata/` (check that chezmoi deep-merges nested keys across
  data files; otherwise one file). Per section, a mode:
  - `generate`: chezmoi renders the app's bindings from it (compositors, wlr-which-key, zsh, kitty);
  - `catalog`: the app keeps its own definitions and the manifest only lists them, for the cheat sheet and conflict
    checks. **nvim is `catalog`**: LazyVim binds keys inside plugin specs (`keys = {...}`, lazy-loading on them), so
    generating nvim keymaps would fight the framework. A headless audit compares the catalog with nvim's real maps.
  For the compositors the manifest is the only place bindings are defined. chezmoi renders from it: each
  compositor's binding section (sway `bindsym`, niri `binds {}`, Hyprland `bind =`, Wayfire `[command]`), the
  wlr-which-key YAML, and the data behind the rofi cheat sheet. Each entry has a chord *or* a leader-menu path, a
  description, and an action:
  - `exec:` commands are the same in every compositor;
  - WM-native actions (focus, move, layout) use logical names with a per-compositor translation table. Only the core
    set is translated for the minimal compositors; an entry without a translation for a compositor is skipped there
    (and listed by the render check).
  - A render-time check rejects duplicate chords per compositor and mode, as in D33's zsh keybinding manifest; the same
    pattern, so share the design.
  - The cheat sheet reads the rendered manifest, not the compositor configs; optional runtime audit for SwayFX:
    compare against `swaymsg -t get_config`.
  - Starting point: `.i3.keys` in `home/.chezmoidata/i3.yaml` already drives the i3 config's named keys, modes and
    program bindings.
  Parsing compositor configs into YAML (the reverse direction) was rejected: variables, `include`, modes and four
  syntaxes make it fragile, and parsed bindings have no descriptions.
- **i3 syntax as the manifest's language (MH's idea, adopted in part).** Chords use i3 notation (`$mod+Shift+h`) and
  WM actions are written as i3/Sway command strings (`focus left`, `move container to workspace 3`). SwayFX and i3
  then need no translation at all, and the existing config seeds the manifest directly. The translation table for the
  other compositors is keyed by those command strings (`focus left` → niri `focus-column-left`, Hyprland
  `movefocus, l`). What a parser cannot remove is that table: the hard part is semantics, not syntax (niri's columns,
  Hyprland's dwindle layout and Wayfire's plugins have no 1:1 mapping for `layout tabbed`, marks or `split`).
  `derjoachim/i3-config-parser` (Go, a single-file CLI from 2020 that prints a cheat sheet; no modes, no library API,
  no tests) is not usable as that layer. For seeding, a one-off script over the rendered config (`chezmoi cat
  ~/.config/i3/config`, `bindsym` lines inside and outside `mode` blocks) is simpler.
- **Mode hints:** waybar's `sway/mode` shows the active mode for free; a popup of a mode's keys (driven by
  `swaymsg -t subscribe` mode events and the manifest) comes later.

## Greeter (last step)

Keep GDM through the trial (reliable, installed, lists every `wayland-sessions` entry). Then:

| | Look / customization | Fedora 44 | Notes |
|---|---|---|---|
| GDM | Poor (theming means patching gnome-shell resources) | installed | the baseline |
| **SDDM** 0.21 | High: QML themes, many community themes | official | mature; most eye candy among packaged options |
| greetd + gtkgreet 0.8 | Medium: GTK + CSS | official | minimal and robust |
| **greetd + ReGreet** | Medium-high: GTK4, CSS, background | not packaged (cargo) | popular with tiling setups |
| greetd + tuigreet 0.9 | Low: text mode | official | zero overhead |
| ly 1.4 | Text mode with animations | Fedora updates | light, less mainstream |
| LightDM + web greeter | High: HTML/CSS | LightDM yes, web greeters no | greeter runs on X11 |
| cosmic-greeter 1.10 | Polished | Fedora updates | pulls in COSMIC pieces |

All of them read `wayland-sessions/`. Switching is system-level (`/etc`, `systemctl enable`), outside chezmoi's home
scope: a sudo installer script plus a documented rollback (`systemctl enable --force gdm`). The greeter runs as its own
user, so matching its look to the desktop theme needs a small root-side sync. Shortlist: SDDM or greetd + ReGreet.

## chezmoi structure

- New files go under `home/` (Phase 0a is done).
- Package installs: one installer for the compositor set and Wayland helpers (COPRs enabled with pinned names), until
  the D32 package map lands; then migrate.
- Units: `home/.chezmoidata/systemd.yaml` install lists, `home/.chezmoitemplates/systemd/<unit>.yaml` per-unit settings,
  unit files in `home/private_dot_config/private_systemd/private_user/`, mirroring the X11 ones.
- Render unit templates from absolute paths (`joinPath .chezmoi.homeDir` behind an `osIsAbs` guard, as for
  `xsettingsd.service`). Render-time commands go through `.chezmoitemplates/safe-output.sh`.
- Guards: Wayland-only files key off the `display_server` host data (as the clipboard stack does) and installed tools
  (`lookPath`); no WSL guard needed.

## Functional daily driver (D50, 2026-10-18)

MH needs a working desktop for a job search soon, so this checklist comes before the numbered steps below. Only what
makes SwayFX usable every day; anything not done by the deadline, **Tuesday 2026-10-20** (MH), moves to the backlog. Each item takes the
functional part of its step, not the whole step; scripts from `i3-config-mbp` are ported only when an item needs them.

- [ ] **Screen sharing, camera and microphone in the browser** (Meet, Zoom, Teams): `xdg-desktop-portal-wlr`, then a
      test call. First, because it is the item most likely to fail at the worst moment. **Must also work with an
      external monitor plugged in** (MH, 2026-10-18: that is the interview setup), so this item pulls the external
      monitor item forward. Fallback MH accepts: a GNOME session for meetings and interviews. State 2026-10-18: the
      portal stack is in place (`xdg-desktop-portal-wlr` running, Fedora's `sway-portals.conf` routes ScreenCast and
      Screenshot to it, slurp installed for the output picker); PipeWire sees the camera (V4L2 and libcamera) and both
      mics. Test page (no account needed): https://webrtc.github.io/samples/src/content/getusermedia/getdisplaymedia/.
      Side finding: `xdg-desktop-portal-hyprland` also starts under SwayFX (chosen for GlobalShortcuts and
      InputCapture via the deprecated `UseIn` key); harmless for screen sharing.
- [x] **Lock, idle, power** (step 4; built 2026-10-19, **all MH tests passed 2026-10-19**, including lid close with the
      external monitor connected; merged `23e03b2`).
      MH's choices (2026-10-19): dim 5 min, lock 6, screens off 7, suspend 20 **on battery only**; lid suspends unless
      an external monitor is connected (then clamshell: SwayFX turns `eDP-1` off); power key suspends, long press
      powers off; plain swaylock (looks later, with theming). Pieces: `~/.config/swayidle/config` run by
      `swayidle.service` (`swayidle -w`, under `wm-helpers-wayland.target`); `~/.local/bin/lock-screen` (`swaylock -f`,
      returns once locked, so suspend waits for the lock), `screens-power` (per compositor), `idle-toggle`
      (`$mod+Shift+Escape`: swaps in `swayidle-locking.service`, which keeps only the lock handlers, so a paused chain
      still locks before sleep); `~/.config/swaylock/config`; sway `bindswitch` for the lid and `inhibit_idle
      fullscreen` for all windows; logind drop-in `/etc/systemd/logind.conf.d/50-chezmoi-power.conf` from
      `run_onchange_install-logind-power.sh` (overrides the 2023 `HandleLidSwitch=ignore` in `logind.conf`; applies
      to GNOME too, except while an external monitor is connected). `$mod+Escape` (`loginctl lock-session`) now
      locks. Checked so far: shellcheck, `sway -C`, swayidle running with the config, `idle-toggle` swaps the units
      both ways. Suspend: deep (S3) is the default; `nvidia-suspend`/`-resume` services enabled; driver params
      untouched. **Tests (MH):** lock and unlock; wrong password; idle chain at 5/6/7 min; suspend on lid close
      (panel only) and resume to the lock screen; lid close with the monitor connected (keeps running, panel off,
      reopen restores it); power key; suspend/resume **with the external monitor connected** (NVIDIA in use: the
      riskiest case); `$mod+Shift+Escape` during a call; whether Chromium holds idle off by itself in a Meet call.
- [x] **Volume and brightness keys** with OSD (done and merged 2026-10-21; Keychron mic-key remap left to MH); quick output switching and a Bluetooth headset (functional part of step 5).
      **Keys built 2026-10-21** (branch `wayland/5-volume-brightness`; MH key tests passed; merged): `~/.local/bin/volume`
      (wpctl: up/down capped at 100%, mute, mic-mute) and `~/.local/bin/brightness` (brightnessctl: panel, floor 1%
      of max; keyboard backlight, a no-op here since zbook has none), bound in the shared fragment for i3 and SwayFX
      (5% steps, Shift for 1%). OSD: dunst progress-bar notifications with a stack tag (works under X11 and Wayland,
      nothing new to install), instead of wob (Wayland-only, not installed). Pitfalls: `brightnessctl -n 1%` prints
      device info (optional value must be attached) and `--min-value` takes a raw value, not a percentage.
      MH tests 2026-10-21: all keys work except mic mute (the keyboard's mic-icon key sends nothing sway binds;
      keycode not yet identified). Compared with the i3-config-mbp scripts (`set-pulseaudio-volume.bash`,
      `misc/set-player-volume.bash`, `misc/set-volume.alsa.bash`, `adjust-brightness.bash`): gaps are the
      feedback sound (`canberra-gtk-play -i audio-volume-change`), per-player (MPRIS) volume, and arbitrary
      pactl/brightnessctl arguments; the ALSA script is obsolete under PipeWire; the old icon names
      (`notification-audio-volume-*`, `display-brightness-*-symbolic`) are not in the installed themes.
      **Pitfall found the same day:** with no sway `output` lines, `swaymsg reload` reset the ASUS to its preferred
      4K@60 (black); fixed with `exec_always kanshictl reload`. After the replug only the left half of the ASUS
      drew; a monitor power cycle fixed it. **ASUS 4K@60 solved 2026-10-21:** MH set the monitor's menu to
      "DisplayPort Stream: DisplayPort 1.2"; kanshi now uses 3840x2160@60Hz, scale 1.5. Feedback sound added
      (`canberra-gtk-play -i audio-volume-change`). Keys (`libinput debug-events`, `~/keys.txt`): the laptop's
      mic key sends `KEY_MICMUTE` (works); the Keychron Q3 Pro's mic key sends a Super+C macro, its screenshot key
      `KEY_SYSRQ` (Print, bound to the not-yet-written screenshot script). Plan: remap the Keychron mic key to F20
      in the Keychron Launcher (xkb maps F20 to XF86AudioMicMute; steps in
      [../runbooks/keychron-launcher.md](../runbooks/keychron-launcher.md)); udev rule `70-keychron-hidraw.rules`
      (`run_onchange_install-udev-keychron.sh`, uaccess for vendor 3434) lets Chromium's WebHID open it. Mixers:
      `pavucontrol` and `wiremix` in `packages.yaml` (`pulsemixer` is not in Fedora); an fzf/rofi per-app volume
      picker over `pactl` sink-inputs is later work.
      **Defaults built 2026-10-21** (`~/.config/wireplumber/wireplumber.conf.d/51-device-priorities.conf`): Bluetooth
      outputs priority 3000 (above everything); C270 webcam mic 2500 and camera 1500 (verified: both default). The
      headphone jack (aux speakers) already replaces the built-in speakers by itself (separate sinks on this card).
      A hand-set default (`wpctl set-default`) wins while present; `wpctl clear-default` returns to priorities.
      Chromium reads cameras directly: its default is chosen in `chrome://settings/content/camera`. Headphones: "Birdbox" (a Bose QC35,
      renamed; `BC:87:FA:48:B9:4C`); paired, bonded, trusted, connected 2026-10-21, but no A2DP sink appeared in
      PipeWire (only `bluez_midi`); a disconnect and reconnect then failed ("No matching connection"). Every
      A2DP start then failed: `Acquire ... returned error: org.bluez.Error.NotAuthorized` (AAC, and the SBC switch
      failed too); re-pairing did not help. **Fixed by restarting the whole audio stack together**
      (`systemctl --user restart pipewire pipewire-pulse wireplumber`), then reconnecting: A2DP AAC plays. After a logout/login the headphones were disconnected and a connect first failed with
      "Host is down" (headphones asleep or busy with other devices); a later `bluetoothctl connect` worked and
      playback was fine. bluez does not connect devices at login; the headphones reconnect when switched on. Likely
      cause: Claude restarted WirePlumber alone to load the priority rules, leaving PipeWire with stale Bluetooth
      state. **Pitfall: after a WirePlumber config change, restart all three units, not WirePlumber alone.** The
      priority rule matches every `bluez_output.*`, so no MAC is needed in the config. MX Master 3S and MX Keys S
      connect over LE and the Keychron Q3 Pro over classic Bluetooth, so `ControllerMode = bredr` is ruled out.
      Under SwayFX no Bluetooth agent runs (GNOME has one): pairing an untrusted device asks `bluetoothctl` to
      authorize A2DP (`Authorize service 0000110d`); a tray agent (blueman) could come with the bar.
- [x] **Screenshots** (2026-10-22, merged `3a38c79`). Rewrite of i3-config-mbp's `screenshot.bash` as
      `~/.local/bin/screenshot` for both session types (D48): `window` (click a window, boxes from `swaymsg`, or drag
      a region) copies the PNG to the clipboard; `window NAME` / `window --ask` (rofi prompt) also save to
      `~/Pictures/screenshots` (`$SCREENSHOT_DIR`); `desktop` captures every output and saves with a timestamp name.
      Keys moved from the i3-only block to the shared body: Print (also the Keychron's key), `$mod+Print` (`window
      --ask`), `$mod+Shift+Print` (`desktop --ask`). **MH's key check passed 2026-10-22**; follow-up the same day:
      the `--ask` prompt is fuzzel (`--prompt-only`, prefilled with the timestamp name, on the output holding the
      selection; rofi `-filter` on X11), Escape skips saving. The first version's empty rofi box read as a no-op,
      sometimes opened on the other (focused) monitor, was hard to read with the `fancy` theme, and dunst cut off the
      saved file name. Prompt tested with `wtype` (default, custom name, Escape) and `--output` placement on both
      monitors. Tested under SwayFX: `desktop` (3 outputs, 7680x2160), `window` with a stubbed
      `slurp` (clipboard only, NAME with `/`, name clash, Escape leaves the clipboard alone), usage errors; X11 branch
      through Xwayland (`maim`, `xclip` offers `image/png`). `sway -C`, `i3 -C` and a live reload clean.
      Second follow-up (2026-10-22, MH's tests): typed paths were flattened (`a/b` → `a-b`) and saved files were
      mode 600 (mktemp's mode, kept by `cp`); saving now goes through `pick-path` (D54: subfolders, `~/` and absolute
      paths, `.png` added, other extensions and sudo paths refused, overwrite confirmation). MH also reported
      "multiple screenshots" after typing a slash: **not reproduced** (one capture per run with `wtype` input); watch
      for it, possibly the Keychron Mod issue (open item). More keys: the MX Keys S screenshot key sends
      `Super+Shift+S` (firmware macro), bound for that keyboard only (`bindsym --input-device`, SwayFX; elsewhere
      `$mod+Shift+s` stays `sticky toggle`); `$mod+Ctrl+s` for the laptop and any keyboard without Print. Tested:
      pytest (20 cases, mutation check), `wtype` runs of the prompt (subfolder with spaces, absolute, `.jpg` and
      `/usr/share` refused, overwrite no → rename, yes → replaced), `$mod+Ctrl+s` starts slurp, a non-MX keyboard's
      `Super+Shift+S` does not.
      MX key check passed; MH found `$mod+`/`$mod+Shift+` variants useless with one Super key, so: `$mod+Ctrl+Shift+s`
      (`window --ask`) and `$mod+Ctrl+Alt+s` (`desktop --ask`) on every keyboard; on the MX Keys, Ctrl+screenshot key
      arrives as the former and Alt+screenshot key (`$mod+Shift+Alt+s`, MX-only) runs `desktop --ask`. Fn never
      reaches the OS (handled in the keyboard), so Fn+key can only be bound to whatever it sends (trace pending).
      **Left for MH:** Ctrl+ and Alt+ the MX screenshot key; the save prompt by hand.
- [x] **NVIDIA renders docked sessions** (D59, 2026-10-23): `sway-perf` measurements, nm-applet dropped (D58), kanshi `config-nvidia`, lid notice. **MH's docked login passed 2026-10-23 15:50**: kanshi ran `config-nvidia` (`docked-asus-dell`: ASUS 0,0 scale 1.5, Dell 2560,0, panel off), lid open showed the notice and left the layout alone; `sway-perf` nvidia-d59: hands off 11%, mouse 22.7% (max 29%), 0 cursor-plane errors, NVIDIA P5 10.5 W.
- [ ] **Hyprland trial: smooth *and* the panel?** (MH, 2026-10-23). GNOME showed the hardware can drive all three screens smoothly; wlroots cannot light the panel while NVIDIA renders. Start: GDM has uwsm entries for SwayFX, niri and Wayfire only, so add a Hyprland (uwsm) entry (as step 1 did; `run_onchange_install-uwsm.sh.tmpl`); check the COPR's Hyprland is installed; read [runbooks/display-session-recovery.md](../runbooks/display-session-recovery.md) first (GNOME is the way back). Minimal Hyprland config (COPR already enabled, D45) under uwsm, then: panel + both externals at once with NVIDIA rendering (`AQ_DRM_DEVICES` dgpu first; Intel first as the control), hardware cursor, `sway-perf`-style CPU numbers for `Hyprland`, hotplug/undock mid-session. Before the bar, so the bar targets the winner. Expect `hy3` for i3-style tiling only if it passes.
      **Built 2026-10-23** (branch `wayland/hyprland-trial`, not merged): correction to the start note: GDM already
      lists **"Hyprland (uwsm-managed)"** (`/usr/share/wayland-sessions/hyprland-uwsm.desktop` from the COPR's
      `hyprland-uwsm`; `uwsm.yaml` says so), so no new entry. Hyprland is 0.56.2 and its config is **Lua** (hyprlang
      deprecated since 0.55): `~/.config/hypr/hyprland.lua` (kanshi's three-screen layout as `hl.monitor` rules plus a
      catch-all, no blur/shadows/animations so the CPU numbers compare with SwayFX, a small key subset: `$mod+Return`
      kitty, `$mod+o` fuzzel, `$mod+Shift+q`, hjkl focus/move, workspaces, `$mod+Escape` lock, `$mod+Shift+Ctrl+e`
      `uwsm stop`, volume/brightness/Print). It starts `wm-helpers-wayland.target` after `uwsm finalize`;
      `kanshi.service` skips Hyprland (`ConditionEnvironment=!XDG_CURRENT_DESKTOP=Hyprland`, negation tested).
      GPU order comes from `~/.config/uwsm/env` (D59: NVIDIA first when docked); `touch
      ~/.local/state/hyprland-intel-first` before login gives the Intel-first control (`env-hyprland`, tested both
      ways). `sway-perf` now measures `Hyprland` too (sway path re-run under SwayFX: 17.6% / 18.3%); its cursor-plane
      and tray counters are sway log lines, so 0 under Hyprland: judge the cursor by eye. `screens-power` uses the
      Lua dpms dispatcher (stub-tested only). Checked: `Hyprland --verify-config` passes, and it catches unknown keys,
      unknown dispatchers and bad arguments (red test). **Not tested: any Hyprland login.**
      **MH's login test** (docked, lid open; GNOME is the way back, runbook row "Hyprland"):
      1. GDM → "Hyprland (uwsm-managed)". Do all three screens light? (`hyprctl monitors`: modes, scales, positions)
      2. `systemctl --user show-environment | grep -E 'AQ_DRM|XDG_CURRENT'` (expect dgpu first, `Hyprland`);
         `uwsm --version` and `systemctl --user status wm-helpers-wayland.target` (kanshi inactive, condition skipped).
      3. `sway-perf measure hypr-nvidia` from kitty; watch the cursor for lag or flicker.
      4. Unplug the dock mid-session, then replug: does the panel keep going, and do the externals come back?
      5. Log out (`$mod+Shift+Ctrl+e`), `touch ~/.local/state/hyprland-intel-first`, log in, `sway-perf measure
         hypr-intel`, then `rm` the file.
      6. Lock (`$mod+Escape`) and unlock once.
      7. Suspend and resume once with `$mod+Ctrl+Escape` (`dock-awake suspend`; plain `systemctl suspend` is refused
         while docked on AC), then check kitty for black text (open item: black text after resume with NVIDIA
         rendering, seen under SwayFX 2026-10-23). Before it: `dock-awake status` shows the lock held. After it: held
         again. Optional: one short power-key press (Hyprland's XF86PowerOff binding, `locked = true`).

      **Results 2026-10-23 (MH, docked login, monitors plugged in at GDM):**
      1. **Passed, and the panel works while NVIDIA renders**: aquamarine makes `card0` (NVIDIA, renderer
         `Quadro T1000`) primary and drives `card1` (i915) as a secondary backend, copying the panel's frames.
         All three outputs at the plan's modes/scales/positions. SwayFX cannot do this (D59).
      2. Passed: dgpu first in `AQ_DRM_DEVICES`, `XDG_CURRENT_DESKTOP=Hyprland`, uwsm 0.27.0; helper target
         active, kanshi condition-skipped; swayidle, dock-awake (held), wifi-band-watch, clipboard stack, dunst
         running (dunst renders; test notification shown).
      3. `hypr-nvidia` (terminals only, 3 outputs): hands off 0.3% avg / 2.0% max, mouse 21.3% / 39.9%; SwayFX
         `nvidia` (2 outputs): 2.0% / 19.0%. MH: cursor smooth. NVIDIA P5, 9.1 W. A video run was skipped (no
         matched SwayFX baseline: `nvidia-d59`'s conditions were not recorded); do a matched pair if it is close.
      4. Passed: undock kept the panel running and moved the windows onto it (the bar survived); re-dock lit
         both externals in the right layout, workspaces back in place; dock-awake released/held. The ASUS
         flapped once on reconnect (absorbed). Hyprland log: routine commit/GBM fallback errors, plus two
         `eglCreateImageKHR EGL_BAD_MATCH` (dmabuf import) before the undock, no visible effect: watch.
      5. `hypr-intel` (Intel primary, `card1`; terminals only, 3 outputs): hands off 1.5% / 9.0%, mouse
         **14.5% / 22.0%**; NVIDIA 8.0 W. MH: no felt difference from NVIDIA-first. Unlike SwayFX (`intel`:
         42.3%, software cursor), Hyprland has no Intel-first penalty, so D59's reason does not carry over.
         Whether Intel-first is *better* is open (one run each; CPU only, not GPU load). If step 7 shows the
         black text after resume on NVIDIA, Intel-first Hyprland is a candidate fix (decision for MH).
      6. Passed: lock and unlock on all three monitors (Intel-first session).
      7. **Failed: kitty hung after the resume** (NVIDIA first, 18:04:48 suspend via `$mod+Ctrl+Escape`; dock-awake
         released/re-held correctly). Hyprland's "application not responding" for kitty; kernel `nvidia-drm` sync-FD
         `semsurf` error during the resume, the same as before the black text under SwayFX. Not a Hyprland fault
         (open item "black text in kitty"). Next: the Intel-first suspend series (draft D60), then decide.

      Differences found: no bar or workspace indicator (expected; a throwaway waybar from the session
      scratchpad was used); kitty text clipped by the rounded corners, fixed for both compositors
      (`window_padding_width 4`); `follow_mouse = 1` here vs `focus_follows_mouse no` (shared i3/SwayFX data):
      MH likes it, decides after using it; then both configs follow one setting.

      **Intel-first suspend series (2026-10-23, failed):** the NVIDIA resume bug hits Intel-first Hyprland too
      (externals black after every resume, a display freeze on replug; detail in the open item). Outcome: D61 (no
      suspend while docked); D60 kept for other reasons (NVIDIA free for compute, no measured CPU cost, MH prefers
      Hyprland). The trial's main question is answered for Hyprland: smooth and the panel works. Before merging the
      branch: D60's default (open item). Later, ricing: an effects CPU test (open item).

- [ ] **Docked suspend workaround** (after the NVIDIA driver upgrade; MH + Claude, 2026-10-23). Scope: before any
      suspend while docked, disable the external outputs (Hyprland: monitor rules or `hyprctl`; SwayFX: `swaymsg
      output … disable`; kanshi must not re-enable them), so no NVIDIA head is active during sleep; after resume,
      enable them again, either automatically after unlock or by asking MH to replug. It has to cover every path that
      can suspend docked: `dock-awake` (which would then stop refusing), logind (lid with `HandleLidSwitchDocked`,
      power key), swayidle's idle suspend, and the AC-loss grace; likely a logind/systemd sleep hook
      (`/usr/lib/systemd/system-sleep/` or a `Before=sleep.target` user unit), since PrepareForSleep only delays
      with a delay inhibitor. **Risks:** the `semsurf` error is logged inside the kernel's resume, before any
      compositor action, so the bug may hit even with no active heads; re-enabling outputs is a modeset on the same
      NVIDIA path that timed out on replug, so it could trigger the freeze itself; testing it means more wedged
      sessions (have SSH or SysRq ready first, open item). **Open questions:** does the driver upgrade make it
      unnecessary; does an undocked-equivalent state (heads off, cable in) resume cleanly; does Hyprland/aquamarine
      release the NVIDIA card's heads fully when outputs are disabled; how to re-enable without a replug; is
      suspend-then-replug safer than a modeset. Until then: D61.
- [ ] **Minimal bar:** battery, network, volume, clock, tray (waybar or swaybar, no styling; step 7 later).
      **Network picker** (MH, 2026-10-22: the current swaybar is not interactive). **nm-applet test done: dropped (D58, provisional)**; so the picker is `networkmanager_dmenu` (below), unless the GPU experiments bring nm-applet back. Earlier note:
      (open item; router session 2026-10-23: nm-applet's tray animation during reconnects is the prime suspect for
      SwayFX lag). If nm-applet is cleared: `nm-applet --indicator` in the tray (Wi-Fi list, passwords, VPN; no own
      code). If not: no nm-applet; the network module's click opens `networkmanager_dmenu` (config already in
      chezmoi; fuzzel/rofi) or `nmtui` in kitty. A port of i3-config-mbp's `rofi-wifi` is a later option.
- [x] **Wi-Fi band notification** (2026-10-22, merged `e0ab1c1`): `wifi-band-watch` (user service, wanted by
      both `wm-helpers-*` targets) notifies on any association below 5 GHz, roaming included (`iw event`). Tested:
      `--check` silent on 5 GHz, notifies with `WIFI_BAND_MIN_MHZ=6000` (one replaced popup, dunst stack tag), event
      path with a stubbed `iw`, service active. Not tested: a real 2.4 GHz association (the band is locked).
- [x] **kitty errors fixed** (2026-10-19, `924ac7f`; the full BOCO merge stays later). `symbol_map` in `U+` form
      (the `0x` form failed every config parse: error screen in new windows, and `kitten choose-fonts` crashed);
      pywal colors through one `globinclude ../../.cache/wal/colors-kitty.conf` (relative: `globinclude` rejects
      absolute patterns; no error while the file is absent); Source Code Pro (Fedora package) instead of the
      never-installed Nerd Fonts v2 "SauceCodePro ... Complete" names; `Ctrl+Alt+3..6` go to tabs 3-6 (all were on
      `Ctrl+Alt+2`); `Ctrl+Alt+s` is the stack layout only (its shadowed `paste_from_selection` map dropped;
      `Shift+Insert` pastes the selection). The `kitty_grab` (`Alt+Shift+c`) and `kitty_search` (`Ctrl+Shift+/`)
      kittens failed on `kitty.typing` (renamed `kitty.typing_compat` in newer kitty): their unmanaged checkouts in
      `~/.config/kitty/` were fast-forwarded to upstream (`e115f36`, `992c1f3`); open item to manage them. Checked with
      kitty's config parser (no bad lines; the wal include read when present, skipped when absent) and the kittens'
      imports; **MH confirmed 2026-10-19** in a new window: no error screen, `Alt+Shift+c`, `kitten choose-fonts`.
- [ ] **Keybinding cheat sheet:** `swaymsg -t get_config` → fuzzel/rofi, comment convention for descriptions
      ([keybinding-manifest.md](keybinding-manifest.md), "Interim").
- [x] **Keyring unlock prompts** (D51; merged 2026-10-18; **both login paths verified**: the fresh-daemon path on
      2026-10-21 21:33, see below). Symptom:
      Chromium, and GPG/SSH use without the YubiKey, asked to unlock the "system keyring"; GNOME never did. Cause
      (journal, 2026-10-18 boot): GDM's PAM step started gnome-keyring and unlocked the login keyring
      (`gkr-pam: ... unlocked keyring`), but the handoff (`gnome-keyring-daemon --start`) lives in GNOME-only XDG
      autostart entries, skipped under SwayFX (`Skipped due to 'exec-condition'`). By the first Secret Service request
      the PAM daemon was gone (`couldn't access control socket: /run/user/1000/keyring/control`), so D-Bus activated a
      fresh, locked one. That the missing handoff is what kills the PAM daemon is a hypothesis; the login test checks
      it. Fix: `exec gnome-keyring-daemon --start --components=secrets` in `sway/config.tmpl` (rendered only where the
      daemon is installed, before `uwsm finalize`); `no-allow-external-cache` in `gpg-agent.conf`, because
      pinentry-gnome3 looked up cached passphrases in the keyring. **GPG half passed 2026-10-18** (MH: `ssh-add -l`
      without the YubiKey, no prompt). **Login test:** right after a SwayFX login, before opening Chromium, run
      `keyring-check` (managed in `~/.local/bin`): exactly one daemon, PAM's unlock (`gkr-pam: unlocked login keyring`)
      in this login's system journal, no `couldn't access control socket` in the session's journal, login keyring
      unlocked, gpg-agent option set; it then lists the manual checks (Chromium, YubiKey unplugged). Two login paths
      exist, because lingering keeps the user manager (and a daemon in it) alive across logouts: (a) **fresh boot**,
      no daemon at login: PAM starts one (`--login` in its command line) and the sway `exec` must take it over;
      (b) **re-login**, a daemon survives from an earlier session: PAM's open-session step unlocks it (journal:
      `unable to locate daemon control file`, `stashed password`, then `unlocked login keyring`). **Path (b) passed
      2026-10-18** (automatic checks, then MH's manual checks: Chromium, YubiKey unplugged) (16:11 login; daemon from 14:57, D-Bus-activated, no prompt). The first
      `keyring-check` required `--login` and failed that path wrongly; fixed in `f81a443`. **Path (a) passed 2026-10-21** (login at 21:33 with no daemon left:
      `gkr-pam: gnome-keyring-daemon started properly and unlocked keyring`, then the sway `exec` found it,
      `discover_other_daemon: 1`; `keyring-check` learned that message in `c80134c`). No reboot was needed. If it fails there, use the D51
      fallback (`gnome-keyring-daemon.socket`).
      **Text consoles:** nothing unlocks the keyring there. `/etc/pam.d/login` (and the `system-auth`/`postlogin`
      stacks it includes) has no `pam_gnome_keyring`; a console session shares the user's systemd manager and bus, so
      it uses a graphical session's unlocked daemon if one runs, and otherwise a request activates a locked daemon whose
      unlock prompt (gcr-prompter) needs a display, so the request fails. Left as is (Claude's recommendation, 2026-10-18; not yet confirmed by MH): the console is for
      recovery, and with `no-allow-external-cache` GPG/SSH there do not touch the keyring. Adding `pam_gnome_keyring`
      to `login` would not help reliably anyway: `login` also accepts YubiKey auth (`yubikey-sufficient`), which gives
      it no password to unlock with.
- [ ] **External monitors** (D52, D53; **2026-10-21: kanshi profiles built and all MH tests passed**: layout, hotplug of
      each monitor, lid closed with hotplug; merged from `wayland/kanshi-audio`). Monitors: ASUS PB287Q (28" 4K; 4K@60 black over DisplayPort, so **4K@30 at scale 1.5**;
      alternative 2560x1440@60 scale 1) and Dell U2717D (27" 2560x1440@60, scale 1). Layout left to right: panel,
      ASUS, Dell; profiles for all three, each monitor alone with the panel, any other monitor, and the panel alone;
      clamshell via sway `bindswitch` plus `lid-panel-sync` (kanshi `exec`; the panel's slot stays empty). The NVIDIA
      card is now always opened, Intel-first (D53), so hotplug works mid-session. NVIDIA-first left the panel black
      under SwayFX (2026-10-21). Open: the ASUS on the USB-C adapter was not detected at all on 2026-10-21 (only the
      Dell, on mini-DP, showed as connected). History follows.
      MH needs one (planned two);
      it is also the interview setup. Found 2026-10-18: HDMI, an mDP adapter and a USB-C hub all failed under SwayFX
      (only `eDP-1`); with the hub, `/sys/class/drm/card0-DP-6/status` was `connected` on the NVIDIA card (4K mode).
      So every external output is NVIDIA-wired. Fix: `~/.config/uwsm/env` (NVIDIA block on zbook only) adds the NVIDIA
      card at login when one of its connectors is connected; `prefer_nvidia_for_external` (in `.chezmoi.yml.tmpl`,
      **`false` for now**) picks Intel-first (`igpu:dgpu`, frames copied to NVIDIA) or NVIDIA-first (`dgpu:igpu`, the
      panel gets the copy). `--unsupported-gpu` was already in the session entry. Try the other value with
      `chezmoi apply --override-data '{"prefer_nvidia_for_external":true}' ~/.config/uwsm/env`, then re-login.
      **Test, Intel-first then NVIDIA-first:** log in with the monitor connected; `swaymsg -t get_outputs` shows both;
      watch for flicker, cursor glitches, stutter on the copied output (the external monitor with Intel-first, the
      panel with NVIDIA-first); then the screen sharing test above with both outputs. First knob if the cursor misbehaves:
      `WLR_NO_HARDWARE_CURSORS=1`. If SwayFX fails to start, pick GNOME at GDM.
      **2026-10-18, Intel-first login:** both outputs up (`eDP-1`, `DP-5`). Layout and scale in `sway/config.tmpl`,
      matched by make/model/serial (panel left, monitor at scale 1.5 = 2560x1440 logical). The monitor link offers 4K
      only at **30 Hz** (2560x1440 at 60): an HDMI 1.4 limit of the hub/monitor HDMI input, not the GPU. 30 Hz feels
      like stutter, so judge Intel-first vs NVIDIA-first at 60 Hz (the monitor's DisplayPort input via USB-C→DP or
      mDP→DP) or at 2560x1440@60.
      **2026-10-19, DisplayPort (mDP→DP cable, and a USB-C adapter; the port shows up as DP-5 or DP-6):** the monitor
      now offers 4K at 60 Hz, and sway selects it, but the screen stays black (the monitor's own menu does not even
      draw); **4K@30 and 2560x1440@60 work**. GNOME is black at 4K@60 too, on both paths. No kernel messages. Both
      compositors render on Intel and copy to NVIDIA, so the NVIDIA-first test (D52 flag `true`) is next. Other
      suspects: the monitor's DisplayPort setting (DP 1.1 vs 1.2 stream), or a link that cannot sustain HBR2 (4K@60
      needs DP 1.2 speeds on all four lanes).
- [ ] **i3 stops deploying on zbook** (D50 amends D49) until the MacBook work, so D48 holds; the shared fragment stays.

## Steps (order agreed by MH, 2026-10-17)

After steps 0-3, the functional checklist above comes first (D50); the rest of each step is spare-time work.

0. **Safety first:** the [display-session recovery runbook](../runbooks/display-session-recovery.md) checks (console
   login, etckeeper snapshot); udev symlinks for the GPUs. **Done 2026-10-17** (console login works; `/etc` was clean at
   etckeeper `0f391be`; symlinks verified: `igpu` → i915, `dgpu` → nvidia). Found on the way: YubiKey prompts were
   unusable on the console; fixed in `dot_zshrc.tmpl` (`GPG_TTY`, `updatestartuptty` on VTs; runbook card).
1. **Packages and sessions:** install SwayFX (COPR), niri, Hyprland (COPR), Wayfire, uwsm (meson installer), portals,
   polkit agent. Each session appears in GDM; GNOME unaffected. **Done 2026-10-17:** packages from `packagesWayland`
   (COPRs per D45); uwsm 0.27.0 via `run_onchange_install-uwsm.sh.tmpl` (rollback: `uninstall.sh` under
   `~/.local/state/chezmoi-system/uwsm/v0.27.0/`); GDM entries `SwayFX (uwsm)`, `niri (uwsm)`, `Wayfire (uwsm)` in
   `/usr/local/share/wayland-sessions`, plus the COPR's `Hyprland (uwsm-managed)` and the packages' own non-uwsm
   entries. Not yet seen on the GDM screen. Do not log into them before step 2 (no config, no `WLR_DRM_DEVICES`).
2. **Session plumbing:** `wm-helpers-wayland.target`; minimal SwayFX config that starts it under uwsm; clipboard stack
   joins it. Verify that logging into GNOME afterwards leaves no helper units running.
   **Built 2026-10-17** (branch `wayland/2-session-plumbing`, merged as `565b002`): `wm-helpers-wayland.target` (`BindsTo=`/`After=`
   `graphical-session.target`, `Wants=clipboard-stack-wayland.target`, no `[Install]`); `~/.config/uwsm/env` exports
   `WLR_DRM_DEVICES`/`AQ_DRM_DEVICES=/dev/dri/igpu` when the symlink exists; `~/.config/sway/config` (minimal, swaybar
   date placeholder) ends with `uwsm finalize && systemctl --user start --no-block wm-helpers-wayland.target`.
   Checked: `sway -C` and `systemd-analyze --user verify` clean; in GNOME all helper units stay inactive.
   **Login test 2026-10-17 (MH):** checks 1-5 and the picom re-check passed (results under "Step 2 login test"). Found and
   fixed in the session: the picom package's XDG autostart entry ran under SwayFX (uwsm starts
   `xdg-desktop-autostart.target`) and failed; masked by a managed `~/.config/autostart/picom.desktop` (`Hidden=true`).
3. **Shared fragment split** (i3 + SwayFX), i3 output byte-identical. i3 is kept (D49).
   **Built 2026-10-17** (branch `wayland/3-fragment-split`): body in `home/.chezmoitemplates/wm/common`, called with
   `.wm` = `i3` or `sway`; `i3/config.tmpl` and `sway/config.tmpl` are thin wrappers. The split commit (`134ac2a`)
   renders i3 byte-identically; separate fix commits follow (color fallbacks were `<no value>`: unquoted `#` in YAML;
   font without `pango:`; undefined `$minimal_border`; launcher template read the wrong keys, so `passmenu --type`
   lost its options; `$audio_intput` typo). The sway wrapper sets `$fg`/`$bg` from the fallbacks, a no-op
   `$refresh_i3status`, `corner_radius`, swaynag/`uwsm stop` exit keys, the placeholder bar and the uwsm exec.
   Checked: `sway -C` clean (negative control fails as expected), live `swaymsg reload` clean.
   **i3-only blocks** (SwayFX gets them when their step ports them): volume and brightness keys (scripts missing; step
   5); screenshot keys (shared since 2026-10-22) and the 7 `i3-input` prompts (6 left; step 6); the `nop` bindings `new-workspace`, `container-info`,
   `workspace-info`, `kitty_media`, `kitty_notepad` (consumer is `i3-companion` in `i3wm-configuration`, not deployed;
   step 6); startup `i3altlayout`, `~/.xsession`, `xss-lock`, `guake`, kitty launchers (step 6; `xss-lock` → step 4);
   `$mod+Shift+w` (`wallpaper.service` does not exist); `restart` (no Sway equivalent).
   The keybinding manifest (step 9) is not started: the byte-identical check needs the hand-written bindings, so it
   gets its own branch after this merge.
   **MH key check 2026-10-17: passed**, except that tabs were invisible: every `client.*` state used `$bg`/`$fg`, so the
   active tab looked like the rest and a tabbed container read as one title bar (not `smart_borders` or
   `hide_edge_borders`: ruled out with screenshots of two test tabs). Fixed with `inactive_*`/`unfocused_*` colors in
   `.i3.colors` (interim greys, MH approved from a live preview). **Merged to `main` 2026-10-17.**
4. **Lock, idle, power** (swaylock, swayidle, logind), before any daily use.
5. **Devices, audio, keys:** design review then build, per [devices-and-audio.md](devices-and-audio.md) (audio
   stack and media control, kanshi profiles, Bluetooth, removable drives, Wi-Fi); `input` blocks;
   volume/brightness/keyboard-backlight keys with OSD; gammastep. The key scripts go to `~/.local/bin` and work in
   both session types; the i3 bindings switch to them too ("Keeping i3 working").
6. **Mining pass** over i3-config-mbp, i3wm-configuration and arcolinux-i3wm (scripts worth porting), then the
   **X-specific config items:** `app_id` rules, screenshot rewrite, `i3-input` wrapper, exit/nag, dropdown terminal,
   opacity keys. Each script found is ported (to `~/.local/bin`, both session types), ported i3-only, or dropped with
   its bindings. Then the **i3 login test**, if i3 is kept.
7. **waybar** with tray (the polybar replacement).
8. **Pickers:** password picker (with the sensitive-clipboard check), clipboard picker, **notification history browser**
   (`dunstctl history` JSON → `jq` → rofi; Enter = `history-pop <ID>`, a custom key = `history-rm <ID>`; raise
   `history_length`; optional dunst rule script appending to a log file so history survives restarts; check the
   timestamp format, which is probably time since boot). Note: actions on re-shown notifications only work while the sending app runs.
9. **Keybinding manifest** (start it in step 3, when the shared fragment is split), then which-key leader menus and the
   cheat sheet rendered from it. **Parked side quest (D50)**: [keybinding-manifest.md](keybinding-manifest.md).
10. **Minimal configs** for niri, Hyprland, Wayfire, reusing the helper target; trial period; pick the main compositor.
    **Parked (D50):** no repo work; MH tries them with their generated default configs.
11. **Greeter**, following the [display-session recovery runbook](../runbooks/display-session-recovery.md)
    (test each DM with `systemctl start` before enabling it).

Theming ([theming.md](theming.md)) starts after step 7 at the earliest.

## Step 2 login test

Console fallback first: if the session does not come up, Ctrl+Alt+F3, log in, `journalctl --user -b -u 'wayland-wm@*'`
(see the [recovery runbook](../runbooks/display-session-recovery.md)). In the SwayFX session (`$mod+Return` opens kitty):

1. `systemctl --user is-active wm-helpers-wayland.target clipboard-stack-wayland.target cliphist@text.service wl-clip-persist.service`: all `active`.
2. `systemctl --user show-environment | grep -E 'WAYLAND_DISPLAY|SWAYSOCK|WLR_DRM'`: all three set.
3. `swaymsg -t get_outputs | grep -E '"name"|make'`: the panel is listed (rendering on Intel).
4. Copy text in kitty, then `cliphist list | head -1`: the copy is there.
5. `$mod+Shift+e` → "Yes, exit": back at GDM. Log into GNOME; the command in 1 prints `inactive` for all four.

**Results 2026-10-17 (MH, first SwayFX login):** 1: all four `active`. 2: `WAYLAND_DISPLAY=wayland-1`, `SWAYSOCK` set,
`WLR_DRM_DEVICES=/dev/dri/igpu`. 3: `eDP-1`, LG Display. 4: the copy was the newest `cliphist` entry. GDM listed the uwsm
entries (MH logged in through `SwayFX (uwsm)`). 5 (GNOME, 2026-10-17): all four `inactive`, passed.
picom still failed on the next SwayFX login (23:13): lingering keeps the user manager alive across logins, and
the XDG autostart generator only re-runs on `daemon-reload`. Its unit dated from before the mask was deployed (a
targeted apply does not run `run_after_reload-systemd-user.sh`). `systemctl --user daemon-reload` removed it.
Re-check (MH, 2026-10-17): the next SwayFX login showed no picom error and `journalctl --user -b | grep picom` had nothing after 23:13, passed.

## Open questions

1. ~~Keep the i3/X11 units long-term, or retire them?~~ Keep, and keep them working (D48, D49).
2. Which physical sockets are `DP-4..6` (the NVIDIA-wired ports)? In the backlog until MH is at the desk.
