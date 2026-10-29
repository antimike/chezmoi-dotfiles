---
summary: Backlog of non-essential zbook improvements (ricing, security, resume) with done/open state
status: living checklist
updated: 2026-10-25
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
- [ ] **hyprpm plugins: hyprbars (riced profile), hy3 deferred** (MH, 2026-10-23; branch `wayland/hy3-hyprbars`,
  2026-10-25; built and nested-tested, **MH's work and riced login tests pending**). `hyprland-devel` in the package map;
  `.chezmoidata/hyprland.yaml` lists the repos (`hyprpm.repos`) and the plugins per profile (`hyprpm.plugins`);
  `run_after_hyprpm-plugins.sh.tmpl` builds the repos, never `enable`s (a stamp: line 1 the Hyprland version, then the
  commit + the repo list; builds only from a Hyprland session running the installed binary, with sudo at a terminal;
  otherwise prints why and exits 0). `~/.config/hypr/plugins.lua` (run by `hyprland.lua`) loads the profile's plugins
  with `hl.plugin.load` when the stamp's version is `hl.version()`, else skips them with one notification per version
  and boot (nested-tested: work loads none; riced with no, a stale and a matching stamp). **Promote a plugin to work
  sessions**: add `work` to its `profiles`, `chezmoi apply`, `hyprctl reload`. hyprpm order matters: `update` first
  (headers; `add` refuses without them), then `add` (asks [Y/n]); `update` and `enable` load enabled plugins into the
  running session at once (so nothing is enabled). hy3 was added by hand during the trial: `hyprpm remove
  https://github.com/outfoxxed/hy3` stops its rebuilds. Hyprland 0.56.2 reloads the config after every plugin load and unload
  (`PluginSystem.cpp:135,193`), so a config guarded on `hl.plugin.<name>` follows the plugin. Tested in
  `tools/hypr-nested` (nested Hyprland in a limited systemd scope):
  - **hy3 deferred**: hyprpm maps 0.56.2 to `db28808` (one commit before the `hl0.56.0.1` tag; fine), but **any hy3
    dispatcher that fails corrupts its tree, and the next window close aborts Hyprland** (uncaught `runtime_error` in
    `Hy3Node::collapseParents`; 7 of 7 reproductions). Repro: three windows, `make_group("v")` on the third, a fourth
    window, `move_focus("l")`, `change_group("toggletab")`, `change_focus("raise")`, then `change_group("h"|"v"|"tab"|
    "toggletab"|"opposite")` or `make_group("opposite")` (each returns `Err: …non-group Hy3Node` or `…uninitialized
    Hy3Node data`), then close any window. `untab` and `make_group("h"|"v"|"tab")` after `raise` were fine, as were all
    of them with a window focused, plugin unloads and dwindle/hy3 swaps on a clean tree. Upstream master after the pin
    has no fix (only API chases). MH: little need for manual tiling with two large monitors. Re-test after an upstream
    fix; filing the issue upstream is MH's call.
  - **hyprbars**: loads alongside hy3 and survives reloads; riced profile, floating windows only (MH): window rule
    `match = { float = false }, ["hyprbars:no_bar"] = true`; i3 palette (`unfocused_bg` at 90%, `fg`), close and
    maximize buttons, double click tiles the window; screenshot-checked, button commands run against a nested instance.
    (An earlier `bar_color` set by `hyprctl eval` at runtime did not take; set in the config file it does.)
    **No tooltips** on the buttons (MH asked, 2026-10-25): hyprbars has none (a button is a command, colours, size and
    icon; hover only redraws the icon). Adding one is ~100-150 lines of C++ in the plugin; not as a fork (rebased on
    every Hyprland release, like hy3's risk), only as an upstream PR to `hyprwm/hyprland-plugins` (MH's call). Left as is.
- [ ] **Hyprland effects and plugins: the riced session** (MH, 2026-10-25; evaluation by Claude from the repos'
  source and docs, nothing built yet unless marked). MH's examples (images, unmanaged, repo root): Hypr-DarkWindow's
  README screenshot, hyprliquid's desktop and power-menu shots, hyprglass dark/light, hypr-edgehover's demo video.
  - **Two login entries (D66; built)**: "Hyprland (work)" (`hyprland-uwsm`, overriding the COPR's "Hyprland (uwsm-managed)") and "Hyprland (riced)" (`hyprland-riced-uwsm`,
    `.chezmoidata/uwsm.yaml`, same `Exec` as the COPR's entry). Not a second desktop name: five units
    (`ConditionEnvironment=XDG_CURRENT_DESKTOP=Hyprland`, exact match) and `lock-screen` test it exactly. GDM sets
    `DESKTOP_SESSION` to the entry's id, which reaches Hyprland through uwsm; `~/.config/uwsm/env-hyprland` maps it to
    `HYPR_PROFILE` (`riced`/`work`). The non-uwsm "Hyprland", "Sway", "Niri" and "Wayfire" entries are hidden (`hideSessions`: copies
    with `NoDisplay=true` in `/usr/local`, which GDM loads after `/usr/share`; not `Hidden=true`, which uwsm refuses,
    and both Hyprland logins start `hyprland.desktop` by reference). Found when MH picked plain "Hyprland": no uwsm, so
    no env files, `uwsm finalize` failed and no helpers (bar) started. `hyprland.lua` branches on it: built-in effects (blur, shadows, animations,
    opacity; all off today), waybar/wlogout styles, and the plugins (`plugins.lua`, above). hyprpm only builds.
    Hyprland checks only the plugin API version on load, so `plugins.lua` refuses builds for another version itself
    (`hl.version()` has the version only, no commit).
  - **Built-in effects, first pass, and the riced GPU: done 2026-10-27 (D69)** (branch `ricing/effects`): blur (size 6,
    2 passes, xray off), soft shadows, ~200 ms animations, inactive windows at 0.92, blur behind waybar (namespaces
    `main`/`extra`, the bars' names) and rofi, media opaque; work profile unchanged. Measured per effect with the new
    `tools/hypr-effects-perf` (scene on workspaces 98/99, `hyprctl eval` per setting; rootless per-process engine time
    from DRM fdinfo, `--igt` for `sudo intel_gpu_top`); results in `~/.local/state/hypr-effects-perf/`. Riced renders on
    NVIDIA when docked (D69); MH's riced and work login tests passed 2026-10-27 (riced `dgpu` first, work `igpu` first, effects on, three outputs). Values get tuned with theming. **xray: off (MH, 2026-10-29)**, by look,
    over a wallpaper (hyprpaper, test-set "busy" image): re-measured with `tools/hypr-effects-perf` (`nvidia-docked-wallpaper`),
    the wallpaper costs nothing measurable and xray on was only ~2 points of Hyprland CPU cheaper while scrolling, within one run's noise.
  - **GPU for the riced session**: probably NVIDIA (the T1000; Intel UHD 630 renders today, D60) — MH agrees, but
    **only after perf tests**. A nested Hyprland renders on the parent session's GPU (aquamarine's Wayland backend
    opens the parent's dmabuf main device; `AQ_DRM_DEVICES` is read only by the DRM backend), so nested tests give
    per-effect A/B costs on Intel only. NVIDIA numbers need a real session: the riced login with
    `hyprland_render_gpu: nvidia`, or a throwaway Hyprland on another VT. Tools: `sway-perf` (Hyprland support),
    `intel_gpu_top`, `nvidia-smi`, Hyprland's `debug:overlay`. A nested window fullscreen on the ASUS (not the Dell)
    approximates one 4K output; a full session adds three outputs at once, scanout and cross-GPU copies.
  - **Adopted**: **hyprglass** (glass; over hyprliquid, whose shots only show the look MH wants): 10 function hooks,
    11k lines, active, pins 0.56.2, full Lua, cost controls (`skip_opaque_windows`, self-sample cost noted), per-layer
    `mask_threshold` (glass only where a layer is opaque enough: glassy waybar pills on a clear bar); very fiddly.
    **hyprexpo** (sandwichfarm fork; over Hyprspace, whose newest pin is 0.56.0): 9 hooks, pins 0.56.2, Lua; the
    official hyprexpo left `hyprland-plugins` at the 0.56 pin. **pyprland** (riced first, then the work session with a
    conservative plugin set): a Python daemon over IPC, so it cannot crash Hyprland; pipx; Lua support via its
    `lua_translate` adapter (new). Overlaps our `special:scratchpad`.
  - **Dropped**: **hyprland-easymotion** (MH): it uses the deprecated `addConfigValue`, which Hyprland refuses under a
    Lua config (`PluginAPI.cpp:180`); no 0.56 pin, last commit 2026-06.
  - **Deprioritized**: **HyprWindowShade** (27 hooks; author: "not been stress-tested… only tested on AMD"):
    HyprShade-compatible fragment shaders per window or layer by rule: reading mode/greyscale, pixelate, glitch on
    unfocused windows, CRT-style effects, layer open/close animations (rofi, notifications, bars), jelly wobble on
    move/resize. Novelty effects rather than the clean glass look. **Hypr-DarkWindow** (5 hooks): per-window invert,
    tint and chromakey shaders. MH sees no use; agreed, except two: chromakey (a solid app background made transparent,
    so blur shows through apps with no transparency) and tinting a window class as a warning (e.g. a root terminal).
  - **Maybe**: **hypr-edgehover** (no hooks; event bus; new config API; no pins, builds HEAD): with gaps, the screen
    edge is gap, not window; it forwards hover/click/scroll from the outer gap (and a thin strip over an edge bar) to the
    adjacent window, as if the pointer were just inside it. Fitts's law for scrollbars and tab strips at the edge; the
    demo's drawer is Zen's own auto-hide sidebar, which edgehover lets an edge hover reach.
  - **Not plugins** (from the images): rounded floating bar with the wallpaper showing through: waybar CSS + a layer
    blur rule (low risk, low fiddliness). Power overlay: **wlogout** + CSS + layer blur (low). Control centre (network,
    Bluetooth, music, sliders) and a hover-reveal side drawer: a widget shell (below) or swaync's control centre;
    waybar cannot reveal on hover.
  - **Notifications**: dunst stays for SwayFX and probably the work Hyprland; **swaync** for the riced one (MH prefers
    its look). Both implement the freedesktop spec, so `notify-send` (`-p`, `-r`, `int:value` progress) carries over.
    Port: `dunstctl close` ×3 → `swaync-client --close-latest`; `history-pop` ×3 → no equivalent (the panel,
    `swaync-client -t`); `set-paused`/`is-paused`/`count` (waybar's dunst module) → `swaync-client -d`/`-D`/`-c`, or
    its subscribe mode `-swb`; `x-dunst-stack-tag` ×6 (OSD replace) → check swaync's `x-canonical-private-synchronous`
    (one caller already sends it) and `-r` ids; `sound-name` → swaync scripts; dunstrc rules → JSON + CSS. Moderate:
    ~8 scripts and 3 waybar modules, best behind a small `notify-ctl` shim chosen per session.
  - **Widget shells**: **eww** (Rust; yuck Lisp-like DSL + GTK3 CSS; data from polled or listening scripts; mature,
    slower development). **AGS** (Aylur's GTK Shell; TypeScript/JSX on GJS with the Astal service libraries for
    Hyprland, MPRIS, network, Bluetooth, notifications; GTK3/4; API breaks between major versions). **Quickshell**
    (Qt6/QML, C++ core; built-in Hyprland IPC, PipeWire, MPRIS, tray, notification server, session lock; hot reload;
    the base of most large current rices). Uses here: control centre, hover-reveal drawer, OSD, notification centre (in
    place of swaync), power menu, even the riced bar. If any: Quickshell; it is the largest time sink on this list.
  - **Zen browser**: Firefox (Gecko)-based, MPL-2.0, ~45k stars, active (1.23.4b, 2026-10-21); vertical tabs,
    workspaces, split view, compact mode (hover-reveal sidebar). Not in Fedora's repos (Flathub or tarball). Chromium
    stays the default (D-number not needed: set 2026-10-24; Meet screen sharing, camera and mic tested with it, which
    matters for interviews); try Zen in the riced session.
  - **Order (MH, 2026-10-25; the profile switch is built)**: (1) built-in effects in the riced session (blur, shadows,
    animations, opacity), measured, with the GPU perf tests; (2) **theming steps 1-2** ([theming.md](theming.md), "Where
    it fits"): palette generator, theme cache, one theme end to end with a hyprpaper wallpaper, so the styling below
    uses that palette instead of being done twice; (3) riced styling on that palette: waybar per profile, wlogout, then
    hyprglass (nested triage, nested A/B on the ASUS, real riced logins, the NVIDIA decision), swaync; then hyprexpo,
    pyprland, edgehover, one at a time with nested triage; Quickshell only if still wanted.
- [x] **Colour temperature in the bar: done 2026-10-26** (MH's live test passed; branch `ricing/sunset-widget`).
  `custom/sunset` on the main bar after the weather (`waybar-module sunset`, signal 12): icon by temperature
  (󰖙 off, 󰖨 >5000, 󰖚 4000-5000, 󰖔 <4000 K), tooltip with the active profile and the next change parsed from
  `hyprsunset.conf`. Scroll: `sunset up|down` (±250 K, 1000-20000), **held across scheduled changes** until a click
  (`sunset schedule`, hyprsunset 0.4.0's `reset temperature|identity` IPC); the held value is in `$XDG_RUNTIME_DIR`
  (ends with the session) with the profile time it was set under, and the module's 60 s refresh re-applies it after a
  profile change (the temperature query is unchanged under identity, so it cannot tell alone). Held = yellow text.
  `tools/sunset-test` (stubbed IPC). Bar-only (no key binds, MH). Still true: `hyprctl hyprsunset identity` with no
  argument is a setter (identity on), not a query; current identity cannot be queried, only the profile. Untested:
  touchpad smooth scrolling (add `smooth-scrolling-threshold` if it jumps).
- [ ] **Dropdown and drawer terminals** (MH, 2026-10-25; riced profile, maybe work later): a guake-style terminal that
  drops from the top with the bar still visible and a small gap below it; then drawers from the sides at several
  opacity/blur levels. First candidate: kitty's own **`kitten quick-access-terminal`** (kitty 0.47.1 is installed): a
  layer-shell panel on a screen edge, shown and hidden by running the kitten again (a bind); per kitty's docs its
  `quick-access-terminal.conf` sets the edge, size in lines/columns, margins (the gap to the bar), opacity and
  hide-on-focus-loss: to verify. Blur through a Hyprland layer rule on its namespace (built-in blur, or hyprglass).
  Alternatives: **pyprland** scratchpads (adopted for riced, D66: animated slide-in from any side, any app), or a
  special workspace with window rules (no slide). Fiddliness: medium (margins against the bar's height per monitor,
  opacity vs readability: `tools/term-contrast`).
- [ ] **Spotify, riced** (MH, 2026-10-25; the player itself is a daily-driver item, [wayland-desktop.md](wayland-desktop.md),
  "Music: Spotify while working"): the same player in both profiles; the riced look comes from widgets reading its
  MPRIS data (cover art, title, controls, progress): waybar's `mpris` module styled per profile, swaync's MPRIS widget,
  or a Quickshell media panel (the hyprliquid screenshot's player is one). spotify_player also draws cover art inside
  kitty. Optional: Spicetify themes, if the official client is chosen.
- **Widget shells and TUIs** (MH's question, 2026-10-25): Quickshell does not turn a TUI into a widget: it cannot show
  ncmpcpp's or calcurse's screen. It draws its own panels (QML on layer-shell surfaces: bars, popups, drawers,
  overlays) and feeds them from the same data the TUI reads: MPRIS over D-Bus for players, `calcurse -Q` (or its data
  files) for appointments, NetworkManager/BlueZ over D-Bus, PipeWire for volume. A "calcurse widget" is a QML panel
  listing `calcurse -Q --days 7`, with a click that opens calcurse in a kitty popup for editing (as the bar's clock does
  today). waybar's custom modules are the same idea in miniature (one line of text and a tooltip).
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
- [x] **hyprpaper** (D63): configured 2026-10-28, every output shows `~/.local/state/wallpaper/current` (a symlink; the unit waits for it); the picker and theme-driven choice come with theming.
- [ ] **Media apps** (MH, 2026-10-24; defaults set by `run_onchange_after_default-apps.sh.tmpl`: swayimg for images,
  mpv for video; all four in the package map):
  - [ ] **mpv keybindings**: review the defaults, then a managed `~/.config/mpv/input.conf` for what should change.
  - [ ] **swayimg keybindings**: a managed `~/.config/swayimg/init.lua` (Lua: `swayimg.viewer.on_key()`,
    `swayimg.gallery.on_key()`, per mode; reference `/usr/share/doc/swayimg/CONFIG.md`, defaults in
    `/usr/share/swayimg/swayimg.lua`). Ideas: vim-style navigation like vimiv, copy to the clipboard, open in satty.
  - [ ] **vimiv keybindings**: review its defaults and edit where they clash with swayimg's or the WM's. vimiv is
    installed but not in the package map: add it if it stays.
  - [ ] **VLC plugins and codecs**: review what is installed (`rpm -qa 'vlc*'`: base/extra/ffmpeg/pipewire/pulseaudio
    plugins and more, none of them in the map) and pick the ones to keep and add. Note `vlc-plugins-freeworld`
    (patent-encumbered codecs) comes from RPM Fusion, which is enabled on zbook but not modelled in the package map
    (only COPRs are), and was at 3.0.22 against vlc 3.0.23 on 2026-10-24; check it still loads.
  - [ ] Default audio app: not decided (Totem for most types, VLC for FLAC today).
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
