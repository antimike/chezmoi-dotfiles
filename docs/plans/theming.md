---
summary: Long-running theming project: switchable theme bundles kept uniform across apps, wallpaper fetching and palette-aware selection, palette generation, fonts, pickers, nvim via lush
status: planned; starts after the SwayFX daily driver (wayland-desktop.md step 7 at the earliest)
updated: 2026-10-17
---

# Theming plan

Second of the two desktop projects (MH, 2026-10-17). The first, a SwayFX daily driver, is
[wayland-desktop.md](wayland-desktop.md) and comes first; this one proceeds as time allows. Loose items:
[ricing-backlog.md](ricing-backlog.md).

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
| SwayFX / Sway | `include ~/.cache/theme/current/sway` | `swaymsg reload` |
| kitty | `include` in `kitty.conf` | `kill -SIGUSR1` (kitty reloads its config) |
| dunst | drop-in under `dunstrc.d` (to check) | `dunstctl reload` |
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
- **Selection:** the existing wallpaper timer (2 h) moves to Wayland (swaybg per output) and picks from a cluster.
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

1. Choose the palette generator (pywal16 / wallust / matugen) on sample wallpapers.
2. Theme cache layout and the include line in each app config; one preset theme end to end.
3. Switcher + theme picker.
4. Wallpaper fetcher service and index; clustering; per-output selection; timer on Wayland; wallpaper picker.
5. Fonts: chezmoi subset + nerd-fonts-installer; font pickers.
6. lush.nvim spec.
7. Greeter theme sync (see the greeter section in [wayland-desktop.md](wayland-desktop.md)).

## Open questions

1. Which sites does the fetcher pull from (licensing for any seeds)? Is the old service's code reusable?
2. Random or deterministic wallpaper selection.
3. Which Nerd Fonts make the chezmoi subset (the i3 data references Iosevka Nerd Font Mono).
