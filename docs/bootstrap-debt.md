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

## Known gaps

- [x] `.chezmoi.yml.tmpl` could not generate a config from nothing: the `wallpaper` block read `.filesystem.*` from the *existing* config's data instead of the `$filesystem` dict defined at the top, so `chezmoi init` on a new machine failed (`map has no entry for key "filesystem"`). Fixed 2026-10-16; checked by running `chezmoi init --config <new path>` with no prior config (output equals the live config).
- `tofi` is in the Debian list but not in Fedora's repos; nothing uses it yet.
- `neovim` floats on `latest` in `.tool-versions` (MH choice); run `mise upgrade neovim` to bump.
- `java` is pinned to the `23-loom+2-48.0.0` early-access build that `latest`
  resolved to. Replace with a real LTS if java is still needed.
- `~/.tool-versions` pins `golang 1.21.4` while `~/.config/mise/config.toml`
  pins `go 1.21.7`; `.tool-versions` wins inside `$HOME`. Reconcile.
- `yq` is a mise/standalone binary in `~/.local/bin`, not a managed install.
