# nvim-lazy-sync

Regenerate the Neovim [lazy.nvim](https://github.com/folke/lazy.nvim) lockfile
(`lazy-lock.json`, symlinked here to `home/lazyvim-lock.json`) under a process
cap, and verify the merged config actually loads. Built during BOCO merge
Phase 2 (2026-10-17), where reconciling a stale 2023 lockfile up to current
LazyVim surfaced several cascading failures.

## Usage

```sh
uv run tools/nvim-lazy-sync/nvim-lazy-sync.py            # sync + verify in place
uv run tools/nvim-lazy-sync/nvim-lazy-sync.py --clean    # full clean-profile reconcile
uv run tools/nvim-lazy-sync/nvim-lazy-sync.py --verify-only
uv run tools/nvim-lazy-sync/nvim-lazy-sync.py --help
```

`uv` reads the PEP 723 header, so no manual venv or install is needed. The
script exits non-zero and prints the offending `:messages` lines if the config
does not load cleanly; on success it prints the lockfile path.

## What it does

1. **(optional `--clean`)** removes `~/.local/share/nvim/lazy`,
   `~/.local/state/nvim/lazy` and `~/.cache/nvim`, and truncates the lockfile to
   `{}`, so lazy resolves the entire graph fresh. Use this after a big LazyVim
   jump — an in-place `:Lazy sync` keeps stale per-plugin branch pins.
2. runs `nvim --headless "+Lazy! sync" +qa` inside a **systemd transient scope**
   (`systemd-run --user --scope -p TasksMax=N`) with a `timeout`. The cap bounds
   the fork storm from concurrent git clones + treesitter parser compiles; the
   timeout bounds wall-clock. `--no-cap` falls back to a bare `timeout` when
   `systemd-run` is unavailable.
3. runs a **load probe**: opens a Lua and a Python buffer (with short sleeps) to
   force lazy-loaded plugins to initialise, dumps `:messages`, and scans for real
   errors, ignoring cosmetic noise (headless nvim-notify, not-yet-installed LSP
   servers, a missing `ruff` binary).

## Failure signals it catches

- **`too many rounds of missing plugins`** — lazy could not finish installing a
  plugin across 5 rounds. It is an *install-failure* loop, not a spec-reference
  problem. On this host it was **luarocks rock builds failing**: Neovim is LuaJIT
  (Lua 5.1), the system `luarocks` targets Lua 5.4, and `hererocks` (which lazy
  uses to bootstrap a 5.1 rocks tree) was absent, so oxocarbon's dev fennel
  rockspec and image.nvim's `magick` rock never installed. Fix: install
  `hererocks` (pipx) + `ImageMagick-devel` — both are in
  `run_once_install_neovim_deps.sh.tmpl` — or set `rocks = { enabled = false }`
  in `lua/config/lazy.lua`.
- **`Error in <config>/init.lua`** and lazy spec errors — a broken plugin spec or
  a version skew. The treesitter `master`→`main` branch migration surfaced here;
  a `--clean` run fixes the stuck branch pin.

## Notes

- The lockfile is a symlink into this repo, so a successful run leaves the
  regenerated `home/lazyvim-lock.json` staged-ready in the working tree.
- The probe cannot exercise every lazy-loaded plugin; it covers the common
  trigger filetypes. Open the real editor for a final human check.
