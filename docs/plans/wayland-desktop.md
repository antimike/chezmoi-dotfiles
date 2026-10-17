---
summary: Wayland desktop plan for zbook: multi-compositor trial (SwayFX full port; niri, Hyprland, Wayfire minimal) under uwsm, shared helper units, daily-driver features, greeter
status: planning; order of work proposed 2026-10-17, awaiting MH's agreement; no desktop config changed yet
updated: 2026-10-17
---

# Wayland desktop plan

Desktop work on zbook, separate from the Claude Code migration ([../log/migration-steps.md](../log/migration-steps.md)).
Theming (theme bundles, wallpapers, palette generation, pickers for fonts and themes) is a separate, longer-running
project: [theming.md](theming.md). Loose items: [ricing-backlog.md](ricing-backlog.md).

**Priority (MH, 2026-10-17):** make SwayFX a usable daily driver first. Theming comes after, as time allows.

## Current state of zbook (checked 2026-10-17)

- Fedora 44, GNOME on Wayland. **GDM** is the active display manager; `lightdm` is installed but unused.
- i3 and polybar are installed but unused. The polybar config and the i3 helper scripts the i3 config calls
  (`~/.config/i3/bin/set-pulseaudio-volume.bash`, `adjust-brightness.bash`, `xss-lock`, kitty's `open-notes.bash`) are
  not in chezmoi or on this machine; they are in MH's **`antimike/i3-config-mbp`** repo (below).
- Already in chezmoi for Wayland: the clipboard stack (`clipboard-stack.target` running `cliphist@text`,
  `cliphist@image` and `wl-clip-persist`; the clipse installer), started explicitly by a Wayland session, never by GNOME.
- Already installed: `dunst`, `rofi` 2.0 (Wayland-native), `kitty` 0.47, `cliphist`, `wl-clipboard`, `brightnessctl`,
  `xdg-desktop-portal-gtk`, `gnome-keyring`, `pinentry-gnome3`, `pam-u2f`.
- Secure Boot is on and swap is zram only (8G). Both matter for hibernation (below).
- Existing X11/i3 session units (`xsession.target`, `xsettingsd`, xss-dimmer, wallpaper timer, redshift, polybar,
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
  `WLR_DRM_DEVICES` list. Fix: a udev rule creating colon-free symlinks (e.g. `/dev/dri/igpu`, `/dev/dri/dgpu`).
- Set the variables in the uwsm environment so every compositor gets them.

## Compositors

| Compositor | Role in the trial | Fedora 44 | Notes |
|---|---|---|---|
| **SwayFX** | **Full i3 port; daily driver** | COPR (pin it; note it in the decision log) | Sway fork: i3 config syntax and i3 IPC (so `i3altlayout` and i3ipc scripts keep working), plus blur, rounded corners, shadows, inactive dimming. Risk: trails upstream Sway (1.11 in Fedora). Plain `sway` stays available as a fallback using the same config, minus the SwayFX-only lines. |
| **niri** | Minimal config | Official (26.04) | Scrolling tiling, KDL config, own IPC (`niri msg`), XWayland through `xwayland-satellite` (packaged). Stable, animated. |
| **Hyprland** | Minimal config | COPR | Most eye candy; frequent breaking config changes; i3-style manual tiling only through the `hy3` plugin, which must match the exact Hyprland version. |
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
  `run_onchange_install-wl-clip-persist.sh.tmpl`. Not in Fedora's repos.
- **Overlap:** with uwsm, do not use `sway-systemd` or start `niri.service` directly; one session model for all four.
- **Shared helpers:** a hand-written `wayland-wm-session.target` (`BindsTo=graphical-session.target`, no `[Install]`).
  Every compositor's config starts it. Shared units (bar, notifications, idle, gamma, outputs, wallpaper, clipboard)
  use `PartOf=`/`WantedBy=wayland-wm-session.target`. GNOME also starts `graphical-session.target`, which is why
  helpers cannot hang off that directly. This keeps the existing rule: **scope units by session, not by host.**
  `clipboard-stack.target` joins it (`Wants=` from the new target).
- Portals: `xdg-desktop-portal-wlr` for screen sharing and screenshots on wlroots compositors; `xdg-desktop-portal-gtk`
  (installed) for file pickers. niri and Hyprland want their own portal backends (`-gnome` and `-hyprland`); check each
  in its minimal config.

## Shared helper components (choices and trade-offs)

All work across the four compositors unless noted (they use standard Wayland protocols such as layer-shell). Fedora
versions checked 2026-10-08 and 2026-10-17.

| Need | Recommendation | Alternatives | Trade-off |
|---|---|---|---|
| Bar + tray | **waybar** 0.15 (tray is a built-in module: no stalonetray) | ironbar, eww, quickshell (none packaged) | waybar has sway, hyprland, niri and river modules, CSS styling and a tray; the others are more programmable but heavier to maintain. Rebuild the polybar modules (workspaces, clock, battery, network, volume, weather) here. |
| Notifications | **dunst** (keep, D29) | **SwayNotificationCenter** 0.12.6 (packaged), mako | dunst keeps your config and `dunstctl` bindings; history only via `history-pop`. swaync adds a notification-center panel (a real notification log, Do Not Disturb, waybar integration) at the cost of a new config. Revisit if the "notification log" item needs more than history-pop. |
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

| i3 config item | Change for Sway |
|---|---|
| `set_from_resource $fg/$bg` (pywal via Xresources) | `include` a generated colors file. Interim: pywal's `~/.cache/wal/colors-sway`; long term the theming cache ([theming.md](theming.md)). |
| `for_window [class="..."]` rules (Firefox sharing indicator, `dropdown`, `Nm-connection-editor`, `Shadow`) | `app_id` for native Wayland windows; `class` still works for XWayland. Find values with `swaymsg -t get_tree`. `window_role` rules (PictureInPicture) need a `title` match. |
| `i3-input -F ... -P prompt` (7 bindings: screenshot filename, marks, swap/move to mark, rename workspace) | One small prompt wrapper (`rofi -dmenu -p`) that runs `swaymsg "<template with %s>"`; replace all 7. |
| `i3-nagbar` (exit confirm), `i3-msg exit` | `swaynag`, `swaymsg exit` (under uwsm: `uwsm stop`). |
| `exec_always ... xss-lock`, `loginctl lock-session` | swayidle + swaylock; `loginctl lock-session` keeps working once swayidle handles the `lock` event. |
| `$refresh_i3status` on media keys | waybar signal (`pkill -SIGRTMIN+N waybar`), or drop if the module polls. |
| `~/bin/screenshot` (`maim` + `xclip`) | Rewrite with `grim` + `slurp` + `wl-copy`; same arguments (`desktop`, `window [name]`). |
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
- **Keybinding manifest (generate, never parse; MH wants no drift).** **One `keybindings` data tree for every app**
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

## Steps (proposed order, 2026-10-17; awaiting MH)

0. **Safety first:** the [display-session recovery runbook](../runbooks/display-session-recovery.md) checks (console
   login, etckeeper snapshot); udev symlinks for the GPUs.
1. **Packages and sessions:** install SwayFX (COPR), niri, Hyprland (COPR), Wayfire, uwsm (meson installer), portals,
   polkit agent. Each session appears in GDM; GNOME unaffected.
2. **Session plumbing:** `wayland-wm-session.target`; minimal SwayFX config that starts it under uwsm; clipboard stack
   joins it. Verify that logging into GNOME afterwards leaves no helper units running.
3. **Shared fragment split** (i3 + SwayFX), i3 output byte-identical.
4. **Lock, idle, power** (swaylock, swayidle, logind), before any daily use.
5. **Devices, audio, keys:** design review then build, per [devices-and-audio.md](devices-and-audio.md) (audio
   stack and media control, kanshi profiles, Bluetooth, removable drives, Wi-Fi); `input` blocks;
   volume/brightness/keyboard-backlight keys with OSD; gammastep.
6. **Mining pass** over i3-config-mbp, i3wm-configuration and arcolinux-i3wm (scripts worth porting), then the
   **X-specific config items:** `app_id` rules, screenshot rewrite, `i3-input` wrapper, exit/nag, dropdown terminal,
   opacity keys.
7. **waybar** with tray (the polybar replacement).
8. **Pickers:** password picker (with the sensitive-clipboard check), clipboard picker.
9. **Keybinding manifest** (start it in step 3, when the shared fragment is split), then which-key leader menus and the
   cheat sheet rendered from it.
10. **Minimal configs** for niri, Hyprland, Wayfire, reusing the helper target; trial period; pick the main compositor.
11. **Greeter**, following the [display-session recovery runbook](../runbooks/display-session-recovery.md)
    (test each DM with `systemctl start` before enabling it).

Theming ([theming.md](theming.md)) starts after step 7 at the earliest.

## Open questions

1. Which physical sockets are `DP-4..6` (the NVIDIA-wired ports)?
2. Keep the i3/X11 units long-term, or retire them once the Wayland session is established? (They are inert; no urgency.)
3. Notifications: is dunst's `history-pop` enough for "notification log", or switch to SwayNotificationCenter?
