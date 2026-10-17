# tools/

Dev scripts for this repo. Not deployed: `tools/` sits outside the chezmoi source root (`home/`).

| Tool | What it does |
|---|---|
| [compare-trees.py](compare-trees.py) | Path-level comparison of two chezmoi source trees (the BOCO survey) |
| [zsh-probe/](zsh-probe/) | Render the zsh files into a scratch home, dump the resulting shell state, and diff two dumps |

## zsh-probe

```sh
uv run tools/zsh-probe/zsh-probe.py probe before --baseline main   # render a git revision
uv run tools/zsh-probe/zsh-probe.py probe after                    # render the working tree
uv run tools/zsh-probe/zsh-probe.py compare before after --show alias bindkey
```

`probe` takes about a minute; `compare` exits 1 if anything differs. Dumps go to `${ZSH_PROBE_DIR:-${XDG_CACHE_HOME:-~/.cache}/zsh-probe}/<label>/probe/`; remove a label's directory when you are done with it.
Needs `uv` (dependencies are declared inline), `chezmoi`, `git` and `zsh`, and your real zinit tree (copied, about 70 MB).
It reads the live chezmoi config but never writes to your real home or chezmoi state.

What the dump holds (one `<name>.txt` each): `env`, `env-zshenv-only` (what `zsh -c` sees), `alias`, `functions`, `fpath`, `path`, `options`, `bindkey` (every keymap), `zstyle`, `widgets`, `comps`, `comps-names`, `params`, `stderr`, plus `timing.txt` and `pty-session.txt` (the raw session, for debugging the harness).

Limits: it records shell *state*, not behaviour. It does not open an fzf picker or press a key. The startup timing is `zsh -i -c exit` (no turbo plugins) and is a smoke test, not a benchmark. Random ids and the scratch path are normalised; if two renders of one tree ever differ, find the new nondeterministic value and add it to `normalise()`.
Why the harness is built the way it is (pty, clean environment, scheduler wait): see the module docstring in `zsh-probe.py`. The planned keybinding audit (D33) should reuse `pty_session()`.
