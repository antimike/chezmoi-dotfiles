# Bootstrap debt

Things installed or configured by hand that chezmoi should eventually own.
Tick an item once a `run_` script or managed file reproduces it from scratch.

## Installed by hand

- [ ] `sudo dnf install git-crypt rlwrap pass-otp cargo luarocks`: covered by
      `run_onchange_install-packages.sh.tmpl`; delete this line once it has run
      on a clean host.
- [x] `gitleaks`, `restic`: now in `.chezmoidata/packages.yaml`.
- [x] `~/.local/bin/bd` and `dolt`: now `run_onchange_install-{beads,dolt}.sh.tmpl`.
- [ ] `bd-track`: installed by hand via `just install-dev`; becomes
      `run_onchange_install-bd-track.sh.tmpl` once the `v0.5.0` tag exists upstream.

## Known gaps

- `tofi` is in the Debian list but not in Fedora's repos; nothing uses it yet.
- `neovim` is pinned to 0.9.4 (what `stable` resolved to in 2024); LazyVim
  likely wants a newer release. Bump deliberately.
- `java` is pinned to the `23-loom+2-48.0.0` early-access build that `latest`
  resolved to. Replace with a real LTS if java is still needed.
- `~/.tool-versions` pins `golang 1.21.4` while `~/.config/mise/config.toml`
  pins `go 1.21.7`; `.tool-versions` wins inside `$HOME`. Reconcile.
- `yq` is a mise/standalone binary in `~/.local/bin`, not a managed install.
