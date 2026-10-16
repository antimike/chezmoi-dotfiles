---
summary: zsh plugins dropped, abandoned or worth investigating: what each provided, why it went, where to look when you miss something
status: living list
updated: 2026-10-16
---

# zsh plugins: dropped, abandoned, to investigate

Plan and measurements: [log/zsh-step4-inventory.md](log/zsh-step4-inventory.md), [plans/boco-merge.md](plans/boco-merge.md) (Phase 0, zsh switch-over).
"Provided" columns are what a scratch-home render showed the plugin adding (aliases, functions, key bindings, environment), not what its README claims.
Add entries here whenever a plugin is dropped; add candidates to section 3 whenever one looks worth a trial.

## 1. Dropped in the BOCO switch-over (2026-10-16, branch `boco-merge/0c-zsh`)

BOCO's plugin lists won where they differ (decision: MH, 2026-10-14). Plugins marked "BOCO" are absent from BOCO's lists.

| Plugin | Provided | Why dropped |
|---|---|---|
| `MenkeTechnologies/zsh-git-acp` | about 120 git aliases and helper functions (`gac`, `gacp`, `gpo`, `gpf*`, `glr*`, `grhm`, `gcom`, ...), bindings `^F^S` and `^S`, `ZPWR_*_BRANCH` variables | BOCO; MH uses none of these aliases (`gp`, `gc`, `gco`, `gl`, `gd`, `gst`, `ga` come from the OMZ `git` plugin, which stays) |
| `MenkeTechnologies/zsh-learn` | a command-history learning database (uses a `mysql` command): aliases `se`, `see`, `re`, `le`, ...; the `ZPWR_*` environment; completion styles; binding `^K` | BOCO; depends on `mysql`; `^K` returns to `kill-line` |
| `MenkeTechnologies/zsh-sed-sub` | `basicSedSub` function, binding `^F^P` | BOCO |
| `zdharma-continuum/zplugin-crasis` | loaded on demand when a command starting with `cras` was typed; purpose not recorded | BOCO |
| `zdharma-continuum/zui`, `z-shell/zi-console` | zinit UI library and console: `ziconsole`, `zpconsole`, bindings `^O^J`, `^O^Z`, `^[Q` (`zi-browse-symbol`) | BOCO |
| OMZ `plugins/fzf` | `FZF_DEFAULT_COMMAND=fd --type f --hidden --exclude .git`, fzf key bindings and completion loader | BOCO replaces it with `fzf --zsh` + `.chezmoidata/fzf.yaml` (Phase 1). **Gap until Phase 1:** `FZF_DEFAULT_COMMAND` is unset; check whether BOCO's `fzf.yaml` sets it |
| OMZ `plugins/autojump` | the `j` command (a wrapper for the `autojump` tool) | BOCO |
| OMZ `plugins/vi-mode` | vi-mode bindings, including `vv` (edit command line) in command mode | MH remembers it interacting badly with other plugins; BOCO relies on `softmoth/zsh-vim-mode` instead |
| `plugins.d/0070.asdf.yaml` | an asdf fallback, active only when `mise` is not installed | inert here (`mise` installed); removed with the switch-over cleanup |
| `plugins.d/0115.fzf.yaml` | fzf-tab, fzf-git.sh and a fetch of fzf's `key-bindings.zsh` from `master` | superseded by BOCO's `0015.fzf.yaml` + `fzf --zsh` in Phase 1; removed with the cleanup |
| `widgets/command-prefixes.zsh`, `widgets/twf.zsh` | `Alt-h` (toggle `run-help`) in vi keymaps; `^T` (`twf` file picker) | loaded only by a hostname block that never ran here; `^T` clashes with fzf; `twf` not installed; `.toggle-command-prefix` is defined nowhere. **Parked** in [parked/zsh-widgets/](parked/zsh-widgets/) |

### Kept despite BOCO (MH, 2026-10-16)

- **`marlonrichert/zcolors`:** `GREP_COLOR(S)`, a fixed `zle_highlight`, a `less` colour theme (`LESS=--use-color -DSkY$DPWb`), and the functions `zcolors`, `lscolor`, `color`. Downsides: `LESS` ends up **without `-R`** (BOCO has `LESS=-R`); the README says LS_COLORS theme values must be 3/4-bit and this `LS_COLORS` uses 8-bit colours, and nothing here runs the `zcolors` function (it only autoloads), so the LS_COLORS-derived completion/command-line theme is not applied; `fast-syntax-highlighting` is not themed by it (the README names `zsh-syntax-highlighting`).
- **`0030.direnv`:** `DIRENV_WARN_TIMEOUT=60s` is exported always; the zinit build of direnv stays behind `not lookPath "direnv"` (BOCO builds unconditionally). Required letting the shared `plugin` template emit export-only entries.

### Tried and rejected

- **OMZ `lib/key-bindings.zsh`** (kept by mistake for one commit, reverted): it begins with `bindkey -e`, which relinks the `main` keymap to emacs and silently turns vi mode off, and overwrites fzf-git and autopair bindings. Do not load it alongside `zsh-vim-mode`.

### Gaps this phase left (covered by `snippets/keybinds-interim.zsh` until the keybinding manifest, D33)

For a vi-mode user the BOCO list loses only these bindings (measured with a clean-environment pty render):
- vicmd `Delete` (`^[[3~`, `delete-char`) and vicmd `Shift-Tab` (`reverse-menu-complete`)
- `Ctrl-Delete` (`^[[3;5~`, `kill-word`) in viins and vicmd
- vicmd `vv` (`edit-command-line`). `edit-command-line` itself stays bound to `^X^E` (viins, vicmd) and `^V` (vicmd) by `zsh-vim-mode`.

Changed, not lost: Up/Down arrows become prefix history search. `^N`/`^P` in insert mode would too, so the interim snippet restores plain `down-history`/`up-history` (vicmd keeps prefix search).

## 2. Abandoned earlier (found in the files; MH to correct)

| Plugin | Evidence |
|---|---|
| `joepvd/zsh-hints` | installed under `~/.local/share/zinit/plugins` but referenced by no plugin file in either repo |
| zinit annexes (`declare-zsh`, `zinit-annex-bin-gem-node`, `zinit-annex-submods`) | behind `.zsh.use_old_annexes`, `false` in both repos |
| `pindexis/marker` | behind `.zsh.use_marker` (BOCO) or `if 0` (here); inert in both |
| `dephell` completion snippet | loaded only if `dephell` is on `PATH` |

## 3. To investigate (MH's list; add here)

_Empty. Add a plugin with one line on what it would replace or add, and why it is worth a trial._

Candidates already implied by the gaps above: a manifest-driven answer for the vicmd keys in section 1 (see D33), and `FZF_DEFAULT_COMMAND` once Phase 1 lands.
