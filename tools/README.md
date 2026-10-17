# tools/

Dev scripts for this repo. Not deployed: `tools/` sits outside the chezmoi source root (`home/`).

| Tool | What it does |
|---|---|
| [compare-trees.py](compare-trees.py) | Path-level comparison of two chezmoi source trees (the BOCO survey) |
| [zsh-probe/](zsh-probe/) | Render the zsh files into a scratch home, dump the resulting shell state, and diff two dumps |
| [home-snapshot/](home-snapshot/) | Save paths under `$HOME` and restore them exactly: the escape route for a risky apply |

## zsh-probe

```sh
uv run tools/zsh-probe/zsh-probe.py probe before --baseline main   # render a git revision
uv run tools/zsh-probe/zsh-probe.py probe after                    # render the working tree
uv run tools/zsh-probe/zsh-probe.py compare before after --show alias bindkey
uv run tools/zsh-probe/zsh-probe.py live now && uv run tools/zsh-probe/zsh-probe.py compare after now
```

`probe` takes about a minute; `compare` exits 1 if anything differs. `live <label>` dumps your *real* home the same way (read-only; shell history is switched off for the session), so you can `compare` a render against what the real shell actually does. Expect real-home-only differences: mise's PATH and functions, the p10k instant-prompt cache, anything direnv loads from the directory you ran it in, and unmanaged leftovers. Dumps go to `${ZSH_PROBE_DIR:-${XDG_CACHE_HOME:-~/.cache}/zsh-probe}/<label>/probe/`; remove a label's directory when you are done with it.
Needs `uv` (dependencies are declared inline), `chezmoi`, `git` and `zsh`, and your real zinit tree (copied, about 70 MB).
It reads the live chezmoi config but never writes to your real home or chezmoi state.

What the dump holds (one `<name>.txt` each): `env`, `env-zshenv-only` (what `zsh -c` sees), `alias`, `functions`, `fpath`, `path`, `options`, `bindkey` (every keymap), `zstyle`, `widgets`, `comps`, `comps-names`, `params`, `stderr`, plus `timing.txt` and `pty-session.txt` (the raw session, for debugging the harness).

Limits: it records shell *state*, not behaviour. It does not open an fzf picker or press a key. The startup timing is `zsh -i -c exit` (no turbo plugins) and is a smoke test, not a benchmark. Random ids and the scratch path are normalised; if two renders of one tree ever differ, find the new nondeterministic value and add it to `normalise()`.
Why the harness is built the way it is (pty, clean environment, scheduler wait): see the module docstring in `zsh-probe.py`. The planned keybinding audit (D33) should reuse `pty_session()`.

## nvim-lazy-sync

```sh
uv run tools/nvim-lazy-sync/nvim-lazy-sync.py --clean    # full clean-profile reconcile
uv run tools/nvim-lazy-sync/nvim-lazy-sync.py            # sync + verify in place
```

Regenerates the lazy.nvim lockfile (`home/lazyvim-lock.json`, symlinked to `~/.config/nvim/lazy-lock.json`) under a systemd process cap + timeout, then runs a headless load probe that scans `:messages` for real errors ("too many rounds of missing plugins", init.lua errors) while ignoring cosmetic noise. `--clean` wipes the installed plugins/state/cache and truncates the lockfile first, so the whole graph resolves fresh — use it after a big LazyVim jump. Full rationale and the luarocks/hererocks + treesitter-main gotchas are in [nvim-lazy-sync/README.md](nvim-lazy-sync/README.md) and the script's docstring.

## home-snapshot

```sh
tools/home-snapshot/home-snapshot create ~/.local/state/claude-migration-backups/zsh-apply/$(date +%F-%H%M) \
    .zshrc .zshenv .config/chezmoi/chezmoi.yml .local/share/zsh .local/share/zinit/completions .cache/zcomp
# ... apply, test ...
env -i HOME="$HOME" PATH=/usr/bin:/bin bash --noprofile --norc tools/home-snapshot/home-snapshot restore <dir>
```

Paths are relative to `$HOME`. A path that does not exist at `create` time is recorded as absent, and `restore` deletes it again. Restoring replaces whatever is there with the saved copy (files, directories and symlinks), so use it only on paths you are prepared to roll back wholesale. `restore` is plain bash plus `tar`/`rm`, so it works even when zsh or Python is broken. `home-snapshot selftest` checks create/restore against a throwaway home. Run `restore` through `env -i … bash --noprofile --norc` when the thing you changed could break your login shell.
