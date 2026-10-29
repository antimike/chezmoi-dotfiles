---
summary: Long-running theming project: switchable theme bundles kept uniform across apps, wallpaper fetching and palette-aware selection, palette generation, fonts, pickers, nvim via lush
status: in progress; library and theme engine moved to the standalone project amontillado (D70, 2026-10-27); v0.1 scaffolded
updated: 2026-10-27
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
(`~/.cache/theme/<profile>/` falling back to `current/`, D39).

**amontillado (D70, 2026-10-27).** The wallpaper library (fetcher, metrics, sidecars, index) and, as its v0.2, the theme
engine (palette format, generator adapters, renderer, reload hooks, cache, contrast checks, per-output selection) are
built as a standalone public project in `~/.local/src/amontillado`, installed with pipx at a pinned tag. Its
`docs/design.md` is the design; this plan keeps the chezmoi side. Revised order: amontillado v0.1 → `amo fetch
--test-set` gives the generator comparison images → tinted-theming evaluation → amontillado v0.2 → the chezmoi include
lines, hyprpaper and one theme end to end → riced styling.

## Goals (MH)

- Switch easily between themes, while every app stays uniform: GTK, waybar, rofi, dunst, kitty, the compositor, nvim.
- Wallpapers per output, from a curated set, chosen automatically (random or deterministic, undecided) or by a picker.
- Colorschemes generated from the chosen wallpapers, optionally.
- Nerd Fonts installed by chezmoi; pickers for fonts per app.
- nvim's colorscheme follows the system palette (lush.nvim).

## Core pattern: chezmoi manages configs, the switcher writes a cache

A runtime switcher must never edit chezmoi-managed files: the next `chezmoi apply` would revert or conflict. So:

- chezmoi manages each app's config, and each config **includes a generated file** from `~/.cache/theme/current/`
  (the same model as pywal's `~/.cache/wal`).
- The switcher writes only that cache, then reloads each app.
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
| GTK3 | `gsettings` (theme, icons, cursor, font) + `gtk.css` | live through gsettings |
| GTK4 / libadwaita | `~/.config/gtk-4.0/gtk.css` color overrides only | app restart |
| nvim | lush spec reads the palette file | autocmd on a signal or file change |

**Limit:** libadwaita apps ignore `gtk-theme`; only colors can be overridden. "Uniform" means GTK3 fully, libadwaita
colors only.

## Palette generation

- **pywal** is what the X11 wallpaper timer uses. Upstream pywal has been unmaintained for years; the installed pipx
  package reports `pywal 3.8.15`, which looks like the pywal16 fork's numbering (to verify).
- Candidates with proper template support: **wallust** (Rust, pywal-compatible templates, contrast checks) and
  **matugen** (packaged in Fedora 44, 3.1.0; Material You tonal palettes). Compare them on a few wallpapers before
  choosing.
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
- **Selection:** the existing wallpaper timer (2 h) moves to Wayland and picks from a cluster: **hyprpaper** per output
  under Hyprland (installed, D63; IPC `hyprctl hyprpaper`), swaybg under SwayFX.
  Random vs deterministic (seeded by date, for example) is undecided.
- **Picker:** rofi with image thumbnails (rofi 2.0 shows them); picking sets the wallpaper and, if wanted,
  regenerates the theme.

## Fonts

- chezmoi installs the **chosen subset** of Nerd Fonts from release archives (pinned version and checksums), via
  chezmoi externals or an installer in the style of the existing pinned ones.
- **nerd-fonts-installer** (github.com/officialrajdeepsingh/nerd-fonts-installer; bash, also an npm package) is
  installed too, pinned, for trying fonts out. It supports non-interactive font arguments, `--nerd-fonts-version`, and
  installs to `~/.local/share/fonts/`. Fonts installed that way are local experiments; promote a keeper to the chezmoi
  list.
- **Font pickers:** kitty already has one built in (`kitten choose-fonts`, kitty 0.36+). For dunst, rofi and waybar:
  `fc-list | rofi -dmenu` writing the font into the theme cache, then reload. Font choice becomes part of the theme
  bundle.

## nvim

A lush.nvim spec that reads the generated palette file (roles, not raw colors) and rebuilds the colorscheme on change.
The existing LazyVim colorscheme stays the fallback when no palette file exists.

## Steps (not scheduled)

Steps 1-4 are re-sequenced by D70 (see "Where it fits"); what moved to amontillado is marked.

1. Choose the palette generator (matugen / wallust; pywal16 dropped as unmaintained) on the `amo fetch --test-set`
   images; check each with `tools/term-contrast` (the kitty Blazer palette is the current hand-made baseline).
   matugen 3.1.0 is installed (2026-10-27); open: can it produce usable ANSI 0-15?
   **Test set fetched 2026-10-28** (amontillado v0.1.0: `amo fetch --test-set --atleast 3840x2160 --ratio 16:9`;
   8 kept of 23 thumbnails), records in `~/.local/share/amontillado/library/`: dark `wallhaven-xed63v`, light
   `wallhaven-739r63`, muted `wallhaven-dp2mol`, saturated `wallhaven-43ey53`, busy `wallhaven-3qz176`, sparse
   `wallhaven-j5wmyp`, monochrome `wallhaven-og3vv9`, multi-hue `wallhaven-8g8zmj` (`amo list` prints the paths).
2. Theme cache layout (**decided**: per profile, D39) and the include line in each app config; one theme end to end,
   including a wallpaper through hyprpaper. The renderer is amontillado v0.2; the include lines stay here.
3. Switcher + theme picker (switcher: amontillado; picker UI: here).
4. Wallpaper fetcher and index: **amontillado v0.1**. Clustering and per-output selection: amontillado later. Timer on
   Wayland and the picker UI: here.
5. Fonts: chezmoi subset + nerd-fonts-installer; font pickers.
6. lush.nvim spec.
7. Greeter theme sync (see the greeter section in [wayland-desktop.md](wayland-desktop.md)).

## Open questions

1. ~~Which sites does the fetcher pull from?~~ Wallhaven (D70). Still open: the CC0 seed for a fresh machine (MH chose
   a committed seed plus MH's own images, 2026-10-27; source to be found, e.g. Wikimedia Commons, shown to MH first).
2. Random or deterministic wallpaper selection.
3. Which Nerd Fonts make the chezmoi subset (the i3 data references Iosevka Nerd Font Mono).
