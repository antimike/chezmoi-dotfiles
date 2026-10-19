---
summary: Hand-installed tools and known gaps that chezmoi should eventually own
status: living checklist
updated: 2026-10-16
---

# Bootstrap debt

Things installed or configured by hand that chezmoi should eventually own.
Tick an item once a `run_` script or managed file reproduces it from scratch.

## Installed by hand

- [x] `sudo dnf install git-crypt rlwrap pass-otp cargo luarocks`: installed by
      hand on zbook 2026-10-14 and covered by
      `run_onchange_install-packages.sh.tmpl`; delete this line once that script
      has run on a clean host.
- [x] `gitleaks`, `restic`: now in `.chezmoidata/packages.yaml`.
- [x] `~/.local/bin/bd` and `dolt`: now `run_onchange_install-{beads,dolt}.sh.tmpl`.
- [ ] `bd-track`: installed by hand via `just install-dev`. The installer
      (`run_onchange_install-bd-track.sh.tmpl`, pinned to `v0.5.1`) is in place;
      tick this once it has run on a clean host.
- [ ] Neovim providers, rocks toolchain and CLI helpers (the `~/.venv/neovim`
      pynvim/neovim venv, `gem install neovim`, `npm -g neovim`,
      `latexmk`/`biber`/`chafa`, `hererocks` via pipx, `ImageMagick-devel`,
      `@mermaid-js/mermaid-cli` [mmdc], and `lazygit` via `go install`): owned by
      `run_once_install_neovim_deps.sh.tmpl` (Phase 2, distro-gated). On this host
      MH ran a full `chezmoi apply` 2026-10-17 (venv/gem/npm/dnf providers in);
      mmdc was installed by hand, hererocks + ImageMagick-devel by hand. The mmdc
      and lazygit lines were added afterwards, so they fire on the next apply
      (the script re-runs when its content changes). Tick once a clean host has
      run the whole script.

## Known gaps

- [x] `.chezmoi.yml.tmpl` could not generate a config from nothing: the `wallpaper` block read `.filesystem.*` from the *existing* config's data instead of the `$filesystem` dict defined at the top, so `chezmoi init` on a new machine failed (`map has no entry for key "filesystem"`). Fixed 2026-10-16; checked by running `chezmoi init --config <new path>` with no prior config (output equals the live config).
- Fonts are not provisioned: the Nerd Fonts in `~/.local/share/fonts/` were installed by hand, and kitty's Source Code Pro comes from `adobe-source-code-pro-fonts`, which `packages.yaml` leaves out (fonts are excluded there by policy). A new machine falls back to kitty's default font. Planned fix: [plans/theming.md](plans/theming.md), "Fonts".
- `tofi` is in the Debian list but not in Fedora's repos; nothing uses it yet.
- [x] `neovim` was floating on `latest` in `.tool-versions`; that landed on 0.12.6, which broke lualine (0.12's stricter `vim.tbl_contains(nil)`), tripped a checkhealth E95 and caused intermittent `E5009: Invalid $VIMRUNTIME` from version churn. Pinned to `0.11.7` (2026-10-17). Revisit when the plugin set (lualine especially) supports 0.12; bump by editing `home/dot_tool-versions`.
- `java` is pinned to the `23-loom+2-48.0.0` early-access build that `latest`
  resolved to. Replace with a real LTS if java is still needed.
- `~/.tool-versions` pins `golang 1.21.4` while `~/.config/mise/config.toml`
  pins `go 1.21.7`; `.tool-versions` wins inside `$HOME`. Reconcile.
- `yq` is a mise/standalone binary in `~/.local/bin`, not a managed install.
