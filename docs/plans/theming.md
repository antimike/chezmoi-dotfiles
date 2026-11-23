---
summary: Long-running theming project: switchable theme bundles kept uniform across apps, wallpaper fetching and palette-aware selection, palette generation, fonts, pickers, nvim via tinted-nvim
status: in progress; library and theme engine in the standalone project amontillado (D70, D73), pinned at v0.9.0; step 2 queued (`theming`, 2026-11-20)
updated: 2026-11-20
---

# Theming plan

Second of the two desktop projects (MH, 2026-10-17). The first, a SwayFX daily driver, is
[wayland-desktop.md](wayland-desktop.md) and comes first; this one proceeds as time allows. Loose items:
[ricing-backlog.md](ricing-backlog.md).

## Where it fits (MH, 2026-10-25)

Order agreed with MH: (1) the riced session's built-in effects and GPU perf tests
([ricing-backlog.md](ricing-backlog.md), "Hyprland effects and plugins"), which do not depend on colours; (2) **steps 1-2
below**: the palette generator, the theme cache and one theme end to end, with a wallpaper through hyprpaper; (3) the
riced styling (waybar, wlogout, then hyprglass, swaync), on that palette. The palette feeds every riced style, so styling
them with hand-picked colours first would mean doing them twice. Main-line position: after SQM/router hardening and the
hyprsunset widget (STATUS.md, next actions).

**Two profiles (D66): decided 2026-10-27.** One palette for now; the cache layout is per profile anyway
(`~/.cache/theme/<profile>/`, with `~/.cache/theme/current` a symlink to the last applied profile, swapped atomically;
D39, D73).

**amontillado (D70, 2026-10-27).** The wallpaper library (fetcher, metrics, sidecars, index) and, as its v0.2, the theme
engine (palette format, generator adapters, renderer, reload hooks, cache, contrast checks, per-output selection) are
built as a standalone public project in `~/.local/src/amontillado`, installed with pipx at a pinned tag. Its
`docs/design.md` is the design; this plan keeps the chezmoi side. Revised order: amontillado v0.1 → `amo fetch
--test-set` gives the generator comparison images → tinted-theming evaluation (done 2026-10-30: tinty not adopted,
amontillado renders its own templates from pinned template sources, D73) → amontillado v0.2 → the chezmoi include
lines, hyprpaper and one theme end to end → riced styling.

## Goals (MH)

- Switch easily between themes, while every app stays uniform: GTK, waybar, rofi, dunst, kitty, the compositor, nvim.
- Wallpapers per output, from a curated set, chosen automatically (random or deterministic, undecided) or by a picker.
- Colorschemes generated from the chosen wallpapers, optionally.
- Nerd Fonts installed by chezmoi; pickers for fonts per app.
- nvim's colorscheme follows the system palette (tinted-nvim; lush.nvim until D73(5) was amended).

## Core pattern: chezmoi manages configs, the switcher writes a cache

A runtime switcher must never edit chezmoi-managed files: the next `chezmoi apply` would revert or conflict. So:

- chezmoi manages each app's config, and each config **includes a generated file** from `~/.cache/theme/current/`
  (the same model as pywal's `~/.cache/wal`), or from a fixed profile's directory.
- The switcher (`amo theme apply`) writes only that cache, then reloads each app. `current` is a symlink swapped
  atomically (D73), so a **file watcher must watch `~/.cache/theme/` itself**: a watch on a file under `current/`
  keeps pointing at the old profile's file after the swap.
- A **theme** is a bundle: palette, fonts, icon theme, GTK theme, cursor. Two sources: **generated** (from a wallpaper)
  or **preset** (hand-made, ignores the wallpaper).

| App | Include mechanism | Reload |
|---|---|---|
| Hyprland (daily driver, D62) | `hyprland.lua` reads a generated Lua table (`dofile`, in `pcall` as `plugins.lua` is) for borders, hyprbars, group colours | `hyprctl reload` |
| hyprlock | `source = ~/.cache/theme/current/hyprlock.conf` (hyprlang; to check) | read at each lock |
| SwayFX / Sway (fallback) | `include ~/.cache/theme/current/sway` | `swaymsg reload` |
| kitty | `include` in `kitty.conf` | `kill -SIGUSR1` (kitty reloads its config) |
| dunst | drop-in under `dunstrc.d` (to check) | `dunstctl reload` |
| swaync (riced, planned) | `@import` in `style.css` | `swaync-client -rs` |
| wlogout (planned) | `@import` in `style.css` | read at each launch |
| waybar | `@import` in `style.css` | `SIGUSR2` |
| rofi | `@import` in the theme | read at each launch |
| GTK3 | `gsettings` (theme, icons, cursor, font); colours in a theme dir (adw-gtk3 style, `@import`ing the generated file) or in `~/.config/gtk-3.0/gtk.css` | gsettings keys live; a `gtk-theme` toggle re-reads the named theme's files and their `@import`s; user `gtk.css` only at app start |
| GTK4 / libadwaita | `~/.config/gtk-4.0/gtk.css` color overrides only | `gtk.css` at app start; `color-scheme` and `accent-color` live via gsettings and the settings portal |
| nvim | tinted-nvim scheme from `current/palette.lua` (D73, amended) | fs_event watcher on `~/.cache/theme/` (not on the file) |

**Limit:** libadwaita apps ignore `gtk-theme`; only colors can be overridden. "Uniform" means GTK3 fully, libadwaita
colors only.

**GTK reload (chz-q1k; from amontillado's reading of the gtk3 3.24.52, gtk4 4.22.4 and libadwaita 1.9.1 source, not
yet tested in a running app):** GTK3 and GTK4 load the user `gtk.css` once per process (a static provider with no file
monitor), so rewriting it changes nothing in running apps. A `gtk-theme` toggle re-reads only the named theme's files,
which is why wpgtk and flatcolor put the colours in a theme dir; a live GTK3 plan has to do the same. libadwaita uses
its own resource stylesheet (dropped if `GTK_THEME` is set), applies user `gtk-4.0/gtk.css` at start only, and follows
`color-scheme` and `accent-color` live through the settings portal (the accent is rounded to a named colour by OKLCH
hue). **Decided by MH 2026-11-20:** GTK3 goes live through a theme dir + toggle (the plain `libadwaita` template, shipped
in amontillado v0.3.0, in an adw-gtk3-style theme dir that `@import`s it; a `gtk-theme` flip on reload; chz-q1k). GTK4
uses `libadwaita-vars` (standalone text colours set by the palette, not the scheme; restart to pick up) **and** keeps
the gsettings `color-scheme` hook on that app (`prefer-$AMO_VARIANT`; a no-op under `theme.variant: system`, it covers
manual `--variant` applies, GtkSourceView and per-scheme assets; chz-ht9). **GTK3 built 2026-11-21 (chz-q1k, D82):** theme dirs
`~/.local/share/themes/amontillado-{dark,light}` (adw-gtk3 + amontillado's `libadwaita.css`, plus an override: adw-gtk3
writes white text on the accent, unreadable on a dark variant's light accent), switched by `gtk3-theme-reload`; a running
GTK3 window recoloured dark → light → dark under Hyprland, suggested-action text 11.72:1 (dark), 4.88:1 (light). **GTK4 built 2026-11-21 (chz-ht9):** the `libadwaita-vars`
app, `~/.config/gtk-4.0/gtk.css` a chezmoi link to its render; text colours checked at 6.6:1 or more (dark) and
4.58:1 or more (light) on window, view and card backgrounds. Checked 2026-11-02 under Hyprland
(portals `hyprland;gtk`): the portal relays `color-scheme` but answers "setting not found" for `accent-color`
(xdg-desktop-portal-gtk 1.15.3 does not serve it; the gnome backend does but is not preferred), so the accent needs
the gnome backend for `org.freedesktop.impl.portal.Settings` or stays restart-only.

**Dark/light by the clock (D78, chz-2hj, 2026-11-07):** `theme-variant` (`~/.local/bin`) sets `color-scheme` in
gsettings and runs `amo theme apply --variant <v>`; `theme-variant.timer` switches at 7:00 (light) and 20:00 (dark),
the times in `.chezmoidata/theme-variant.yaml` (shared with hyprsunset's daytime profile; change both together);
amontillado's own config takes `theme.variant: system` (v0.5.0; MH 2026-11-20, chz-8bg.4), which settles the open point
at the end of this paragraph;
`$mod+w` then `d` (the wallpaper submap; `$mod+Ctrl+d` before chz-1yx, still in SwayFX) toggles until the next switch;
when the variant actually changes, `wallpaper next --<v>` picks new pictures of that variant and themes from the
primary's (chz-1yx). Verified live 2026-11-07: the portal's `org.freedesktop.appearance
color-scheme` follows (1 dark, 2 light). The amo step is skipped until the profile has a palette (chz-8bg.4); then
amontillado's own `theme.variant` must follow the clock too, or a wallpaper change re-renders in `auto` (open, D78).

## Palette generation

- **pywal** is what the X11 wallpaper timer uses. Upstream pywal has been unmaintained for years; the installed pipx
  package reports `pywal 3.8.15`, which looks like the pywal16 fork's numbering (to verify).
- Generators (D73): **matugen >= 4.0 first** (Material You tonal palettes; the base16 backend arrived in 4.0, so
  amontillado refuses Fedora 44's 3.1.0), **wallust** second (Rust, pywal-compatible templates, contrast checks).
  chezmoi pins matugen 4.2.0 and wallust 3.5.1 (chz-8bg.1). **Compared 2026-10-30 (step 1): neither one's raw ANSI
  output is usable**; matugen's base16 backend is pywal-style clustering, not Material, so its accents carry no named
  hue and no contrast. amontillado builds ANSI 0-15 itself (its decision 11, 2026-10-30; step 1 below).
- Templates: amontillado renders them itself (no tinty, no pywal) from optional pinned sources: built-in
  variables-only templates, tinted-theming repos, matugen-themes, pywal16 templates, a URL with sha256, a local path;
  `amo theme sync` fetches, `amo theme apply` stays offline. An app can opt into matugen's own rendering
  (`render_with: matugen`). The palette is base24 plus roles, with dark and light variants (`variant` per run or app).
- **"Looks good" and contrast (MH asked for the community's accepted answer).** There is no single standard, but the
  common practice is: pick a generator that **enforces contrast** (matugen's tonal palettes pair foreground and
  background tones by design; wallust can check and adjust contrast) and map its color *roles* onto each app, rather
  than inverting a palette by hand. For a semi-transparent terminal over a busy wallpaper, the usual fix is background
  blur (SwayFX `blur` on kitty) plus a darker background opacity, not a different palette.
- So the earlier idea of an "inverted" lush scheme is **dropped as a default**. It stays an optional experiment once
  the generated palette is in use (hue rotation and light/dark inversion are both easy in lush's HSL).

## Wallpapers

- **Source:** a fetcher service (MH has written one before) downloads from chosen sites periodically into
  `~/.cache/wallpapers/`. Images are **not** managed by chezmoi. Optionally, the cache is its own git-annex (or
  git-lfs) repo, private, as on MH's other machine.
- **Seeds:** a few images may live in the chezmoi repo so a fresh machine has something. The repo is public, so seeds
  must be freely licensed (CC0 / public domain) and small.
- **Palette-compatible sets per output (MH, 2026-10-17).** Generating one scheme from several unrelated images gives a
  muddy brown-grey average. Plan:
  1. At fetch time, compute features for each image (dominant colors in a perceptual space such as OKLCH or CIELAB:
     mean hue, chroma, lightness, warm/cool balance) and store them in an index next to the cache.
  2. Group images into compatible clusters (k-means on those features, or simply buckets by hue and warmth).
  3. Choose all outputs' images from one cluster, and **generate the palette from the primary output's image only**,
     not from a composite.
  Tools: Python with Pillow and a small k-means; or reuse the palette generator's own JSON output per image as the
  features.
- **Selection (built 2026-11-20, chz-1yx):** `~/.local/bin/wallpaper` sets a picture per monitor with `amo group`
  (colours going together; least-shown first, so the library is seen before repeats) through hyprpaper's IPC
  (`group.setter` in the amontillado config). The primary is waybar's main monitor (`waybar-launch main`); its picture
  is `~/.local/state/wallpaper/current` and the one the theme follows. New sets come at the dark/light switches
  (`--dark`/`--light`, only on a real change) and on `$mod+w` `n`; no interval timer. Monitor changes keep the
  primary's picture and regroup the rest; `wallpaper restore` re-applies the set after hyprpaper starts. SwayFX: not
  covered (no hyprpaper).
  After a theme apply, amontillado runs its `theme.wallpaper.reload` hook (its config, D73; e.g. a `hyprctl hyprpaper`
  command); which setter that hook calls stays chezmoi's choice.
- **Picker (built 2026-11-20, chz-1yx):** `$mod+w` `p`: rofi with thumbnails (`amo list --format rofi`), filtered by the
  current variant, `Alt+v` cycling dark, light, all; the pick goes on the primary with companions, and themes.

## Fonts

- chezmoi installs the **chosen subset** of Nerd Fonts from release archives (pinned version and checksums), via
  chezmoi externals or an installer in the style of the existing pinned ones.
- **nerd-fonts-installer** (github.com/officialrajdeepsingh/nerd-fonts-installer; bash, also an npm package) is
  installed too, pinned, for trying fonts out. It supports non-interactive font arguments, `--nerd-fonts-version`, and
  installs to `~/.local/share/fonts/`. Fonts installed that way are local experiments; promote a keeper to the chezmoi
  list.
- **Picker family (chz-8bg.9, 2026-11-20):** every picker shares one look (the bar menus'): rofi's default theme is
  `~/.config/rofi/picker.rasi` (`bar-menu` and `wallpaper-picker` import it and change only layout), and fuzzel's
  pickers match through a managed `fuzzel.ini`. Colours live only in `~/.config/rofi/colors.rasi` and
  `~/.config/fuzzel/colors.ini`; chz-8bg.4 has amontillado render both (and chezmoi stop managing them).
- **Font pickers:** kitty already has one built in (`kitten choose-fonts`, kitty 0.36+). For dunst, rofi and waybar:
  `fc-list | rofi -dmenu` writing the font into the theme cache, then reload. Font choice becomes part of the theme
  bundle.

## nvim

amontillado's built-in `nvim` template (`theme.apps.nvim`) writes `~/.cache/theme/current/palette.lua` (base24, roles,
variant; D73). The nvim config's `lua/amo-theme.lua` feeds it to tinted-nvim (v1) as the base24 scheme
`base24-amontillado`, through modules vendored unchanged from amontillado's `docs/examples/nvim/` (`lua/amontillado/`:
`palette`, `tinted`, `watch`), and is LazyVim's `colorscheme` function (chz-8bg.17; MH chose tinted-nvim over a lush
spec, 2026-11-23: D73(5) amended). The watcher watches `~/.cache/theme/` (the `current` symlink is swapped, not the
file rewritten), so every running nvim re-applies after each `amo theme apply`; `background` follows the palette's
`variant`. Our overrides: the accent on the interface (amontillado's module) and the four Diff groups (tinted-nvim's
DiffAdd is background-coloured text on a darkened blue, unreadable here; ours tint the background with the hue and
keep the text colour). Without a palette or tinted-nvim it falls back to gruvbox with one warning, and the watch still
starts, so a first apply switches over. The kitty-scrollback config (ksb-nvim, chz-8bg.18) shares `amo-theme.lua`.
Review tinted-nvim vs lush after use: chz-8bg.19.

## Steps (not scheduled)

Steps 1-4 are re-sequenced by D70 (see "Where it fits"); what moved to amontillado is marked.

1. Compare the palette generators (matugen 4.2.0 / wallust 3.5.1, chz-8bg.1; pywal16 dropped as unmaintained) on the
   `amo fetch --test-set` images; check each with `tools/term-contrast` (the kitty Blazer palette is the current
   hand-made baseline). amontillado already ranks matugen first (D73); the comparison checks ANSI 0-15 quality
   before styling (chz-8bg.2; MH kept it, 2026-10-30).
   **Done 2026-10-30** with `tools/palette-compare` (term-contrast's checks plus accent contrast, distinctness and
   ANSI hue fidelity; results in `~/.cache/palette-compare/`). Blazer baseline: 0 term-contrast failures, accent
   minimum 4.43:1, 6/6 accents on their ANSI hue.
   - **matugen base16** (`--source-color-index 0`, dark): 6-24 failures, accent minimum 1.00 on every picture, 0-2/6
     hues. The `wal` backend clusters picture colours apart from the Material engine (`-t` and `--contrast` leave it
     unchanged); on dark, muted and monochrome pictures the accents collapse into the background. matugen's Material
     roles and tonal palettes are sound.
   - **wallust** default: 2-13 failures, colours unordered (red lands anywhere); `-k`: 2-6 failures, still unordered,
     red turns grey on muted pictures.
   - **wallust `-k -c lchansi -p ansidark16`**: 6/6 hues, but the accents are mostly fixed (yellow, magenta, cyan
     identical on all 8 pictures); colour 8 and red still fail 3:1 on some pictures (xed63v: 2.30, 2.42).
   **Outcome (amontillado decision 11, MH 2026-10-30):** option A by default: amontillado assigns base08-base0F
   (ANSI 1-6, 9-14) from fixed nominal OKLCH hues, chroma from the picture's accent, lightness per variant, then its
   contrast check; the generator supplies only the ramp, accent and secondary. `theme.hues: generator` (`--hues`)
   keeps the generator's own colours (matugen `base16`, or wallust `-k -c lchansi -p ansidark16`). Rejected: matugen
   `custom_colors` with `blend = true` (hues collapse toward the picture's). Recorded in amontillado's
   `docs/design.md`, "Theme engine (v0.2)" > "Generators" ("Named hues") and "Theme engine: decisions" item 11
   (`~/.local/src/amontillado/docs/design.md`; the GitHub copy once amontillado's `main` is pushed). Implemented
   by amo-aqp.20; its calibration run is `palette-compare` on this test set, which first needs to read
   `amo palette` output (chz-98w, deferred until amontillado v0.2.0 is tagged).
   **Built and calibrated (amontillado, reported 2026-11-03, unreleased until v0.2.0):** on the 13 library pictures,
   scored with `palette-compare`'s `score` and `term-contrast`'s sources from a scratch script (amontillado's run,
   not reproduced here yet), option A beats the Blazer baseline. Dark: 0 term-contrast failures, fg/bg 16.6-16.7,
   accent min 5.25-5.29, distinct 8.9-11.0, 6/6 hues. Blazer: 0, 13.89, 4.43, 7.9, 6/6. The light variant has 2
   failures, both fsh styles on 256-colour cube entries (`bg=18`, `fg=113`) that no 16-colour palette sets. matugen
   base16 + adjust, dark: 1-25 failures, 0-2/6 hues. Getting there took a near-black base00/base01 (tones 5/10) and a
   foreground at tone 95 (fsh's bracket highlight and less's prompt want fg at 3:1 on blue). palette-compare will
   import the hue and distinctness metrics from `amontillado.accents` through its uv script header rather than keep
   a copy (MH 2026-11-03, chz-98w).
   **Reproduced here 2026-11-21 (chz-98w, amontillado v0.9.0):** `palette-compare` scores `amo palette` output
   (settings `amo`, `amo-light`, `amo-generator`; base24 mapped to ANSI as chezmoi's kitty template does) and imports
   `amontillado.accents` (pinned in its uv header at chezmoi's amontillado tag). On the 8 test-set pictures: **amo
   dark** 0 failures, fg/bg 16.64-16.73, accent min 5.25-5.28, distinct 8.9-10.8, 6/6 hues on every picture; **amo
   light** 2 failures each (the fsh 256-colour pair above), 16.26-16.37, 4.95-4.97, 9.2-9.5, 6/6; **amo with the
   generator's hues** 0-2 failures, accent 4.95-4.99, but distinct 0.0-5.4 and 0-2/6 hues (the contrast fix saves
   contrast, not hue); raw matugen 6-24 failures, accent 1.00; wallust-ansi 3-7, 6/6 hues. Blazer (now scored from
   `kitty/current-theme.conf`, since the live config follows the theme): 0, 13.89, 4.43, 7.9, 6/6, the same as with
   palette-compare's former own metrics.
   **Test set fetched 2026-10-28** (amontillado v0.1.0: `amo fetch --test-set --atleast 3840x2160 --ratio 16:9`;
   8 kept of 23 thumbnails), records in `~/.local/share/amontillado/library/` by Wallhaven id: dark `xed63v`, light
   `739r63`, muted `dp2mol`, saturated `43ey53`, busy `3qz176`, sparse `j5wmyp`, monochrome `og3vv9`, multi-hue
   `8g8zmj`. Renamed from `wallhaven-<id>` to tag-derived names ending in the id on 2026-11-20 (amontillado v0.9.0
   `amo name --from-tags --force`, chz-089); `amo list` prints the paths.
2. Theme cache layout (**decided**: per profile, D39) and the include line in each app config; one theme end to end,
   including a wallpaper through hyprpaper. The renderer is amontillado v0.2; the include lines stay here.
   **Built 2026-11-20 (chz-8bg.4, amontillado v0.9.0):** `theme.apps` in the managed amontillado config, with
   `theme.variant: system` (D78's `theme-variant` owns the scheme) and no `theme.wallpaper.reload` (it would set one
   picture on every monitor; the `wallpaper` helper sets per-monitor pictures through `group.setter`, chz-1yx).
   Built-in templates for waybar (`gtk` → `colors.css`, `@import`ed through a link next to `style.css`; `SIGUSR2`),
   Hyprland (`hyprland.lua`, `dofile` in `pcall` with Blazer as the fallback; borders and hyprbars; `hyprctl reload`),
   hyprlock (`source =` the cache file) and dunst (a `dunstrc.d/50-theme.conf` link; `dunstctl reload`). Our own
   templates in `~/.config/amontillado/templates/` for kitty (only today's palette keys: colour 0 is `base11`, colour
   7 `base06`; the built-in puts the background in colour 0 and sets the tab bar's colours), rofi (the picker
   variables of chz-8bg.9 with the translucent background) and fuzzel (`colors.ini`). `rofi/colors.rasi` and
   `fuzzel/colors.ini` are now chezmoi symlinks into the cache, so `chezmoi apply` no longer reverts a theme; kitty
   keeps `current-theme.conf` as the fallback under a `globinclude` of the cache file. The preset
   `palettes/blazer.yaml` renders the pre-theming colours (`amo theme apply --palette blazer --no-adjust`; byte-equal
   values for kitty, rofi and fuzzel; with the contrast check the accent, 4.43:1, would move). Hyprland's borders
   and hyprbars and dunst used the i3 palette before; they follow the theme now. `run_onchange_after_theme-render`
   re-renders when the config, the preset or a template changes, and renders Blazer on a fresh machine. The wallpaper
   comes from the `wallpaper` helper, which themes from the primary monitor's picture.
   **amontillado v0.11.0 (chz-lfs, 2026-11-21):** `theme.tone: {light: soft, dark: full}` (MH: light as cream paper
   with dark-grey text; review after a while of use; per app `theme.apps.<app>.tone`, `AMO_TONE` in reload hooks).
   Our kitty template sets `palette_generate semantic` (kitty 0.47: colours 22-255 follow the palette), and
   `apps.vivid` renders `vivid.yml` for LS_COLORS (the zsh hook is chz-n6i). Kitty's dark pin under light-soft,
   `term-contrast` (palette, fsh, autosuggest, less, git, p10k): 2 failures, both text on blue (fsh's paired
   bracket 1.78:1, less's prompt 2.55:1), fixed in `fsh-styles.zsh` (`bg=8`) and `LESS` (`-DPkb`); 0 after.
   vivid's light LS_COLORS: lowest 3.07:1 (dim files).
   **LS_COLORS hook (chz-n6i, 2026-11-21):** the snippet `ls-colors.zsh` (zinit turbo, replaces trapd00r) re-exports
   LS_COLORS and completion's list-colors at the first prompt after `current` points at a new generation (`:A`, no
   fork), from `vivid generate` on its `vivid.yml`, cached per generation in `~/.cache/zsh/ls-colors/`; fallbacks
   vivid's `ansi`, then dircolors. `apps.vivid` is pinned dark with kitty (LS_COLORS draw on kitty's background):
   lift the two together. `term-contrast` (all sources, `--vivid` with each render): 0 failures on 3qz176 dark,
   3qz176 light-soft (pins removed in a scratch config) and Blazer.
   **Pins lifted (chz-8bg.13, 2026-11-22):** kitty and vivid follow the variant. MH checked glow, ls, git log and
   `bd show` in a light-soft kitty: all palette-driven colours read well; bd does not detect the light background,
   so its fixed truecolour tags (`(EPIC)` #d2a6ff, priority #ffb454; 1.4-1.6:1 on cream) are faint. Accepted.
   **Claude Code follows it (2026-11-22):** `"theme": "auto"` (set if absent by `modify_settings.json.tmpl`) picks
   dark/light from kitty's background (OSC 11) and re-queries on a DEC 2031 colour-scheme report. Tested in a scratch
   kitty 0.47.1 (probe: mode 2031 on, OSC 11 polled): a `SIGUSR1` reload that flips the background sends `CSI ?997;2n`
   (light) or `;1n` (dark) at once; a reload without a flip sends nothing. Claude Code 2.1.330 enables mode 2031
   (`THEME_NOTIFY`), so running sessions switch at the next amo apply.
3. Switcher + theme picker (switcher: amontillado; picker UI: here).
4. Wallpaper fetcher and index: **amontillado v0.1**. Clustering and per-output selection: amontillado later. Timer on
   Wayland and the picker UI: here.
5. Fonts: chezmoi subset + nerd-fonts-installer; font pickers.
6. ~~lush.nvim spec reading `palette.lua` (D73).~~ tinted-nvim fed `palette.lua`, live (D73(5) amended; chz-8bg.17).
7. Greeter theme sync (see the greeter section in [wayland-desktop.md](wayland-desktop.md)).

## Open questions

1. ~~Which sites does the fetcher pull from?~~ Wallhaven (D70). Still open: the CC0 seed for a fresh machine (MH chose
   a committed seed plus MH's own images, 2026-10-27; source to be found, e.g. Wikimedia Commons, shown to MH first).
2. Random or deterministic wallpaper selection.
3. Which Nerd Fonts make the chezmoi subset (the i3 data references Iosevka Nerd Font Mono).
