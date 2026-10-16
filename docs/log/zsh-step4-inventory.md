---
summary: Step 4 (zsh switch-over) sub-step 1: live-shell baseline, option mapping, who sources what, and the keep/drop decision per piece
status: current
updated: 2026-10-16
---

# zsh switch-over: inventory (sub-step 1)

Plan: [../plans/boco-merge.md](../plans/boco-merge.md) (Phase 0, "zsh switch-over"). Taken before any template change, on `main` at `10a7675`.
Raw baseline files (not in the repo): `~/.local/state/claude-migration-backups/zsh-step4/` (`env-*`, `alias`, `functions`, `fpath`, `path`, `options`, `bindkey-all`, `zstyle`, `widgets`, `timing`, `zshrc.live`, `zshenv.live`).

## Live-shell baseline

- Interactive startup (`zsh -i -c exit`): first run 0.50 s (cold), then 0.144-0.147 s (4 runs).
- The baseline is **not stderr-clean**: every run prints a p10k `gitstatus failed to initialize` error and `(anon):setopt:7: can't change option: monitor`. These come from running `-i -c` without a TTY, not from the config. Pass criterion for the new config is therefore "same stderr as baseline", not "empty".
- 171 exported variables, 18 aliases (no `bat` alias), 1761 functions, 413 widgets, 2009 completion entries, 5 `fpath` entries, 391 lines of `bindkey` across all keymaps.
- `~/.zshrc` and `~/.zshenv` are managed and match the source (`chezmoi diff` empty). There is no `~/.zprofile`.

## BOCO is not a drop-in

| Issue | Detail | Resolution |
|---|---|---|
| Data schema | BOCO: `.zsh.theme` is a string, no `.zsh.histfile`. Here: `.zsh.theme.{name,opts}` and a `.zsh.histfile` block | BOCO schema; delete the histfile block and `theme.opts` |
| `.filesystem.tmpDir` | used by BOCO `zshenv`, **not defined** in `.chezmoi.yml.tmpl` | add `tmpDir: /tmp` to `filesystem` |
| `alias bat=batcat` | Debian binary name; breaks `bat` on Fedora | drop |
| `alias claude-mem=...` | hard-coded path under another user's home; claude-mem is held | drop |
| `BROWSER` WSL block | tests the OS inline, `powershell.exe`/`cmd.exe` branches | `is-wsl` helper; WSL branches are Phase 6 |
| `SSH_AUTH_SOCK` + `gpgconf --launch gpg-agent` | **only here**, in `zshenv`; YubiKey SSH auth depends on it | keep in the merged `zshenv` |
| `ZCOMP_CACHE` directory | BOCO exports the path but **never creates it**; here `ensure_resource` runs `mkdir -p` | add `mkdir -p "$ZCOMP_CACHE"` to the merged `zshrc` |
| History size | BOCO `HISTSIZE=999999999`, `SAVEHIST=$HISTSIZE`; here 100000 / 5000 | BOCO wins (flag: a much larger history file) |
| Completion `rehash` | BOCO `false`; here `true` (new executables completed immediately) | **Gate on `is-wsl`: `false` on WSL hosts, `true` elsewhere** (MH, 2026-10-16). BOCO set `false` in `76a997a` (2026-04-09) for latency; on WSL2 a `$PATH` rescan crosses into the Windows filesystem. Here a full rescan plus table rebuild measures 2.0-3.0 ms (31 `PATH` entries, 3731 commands). Done in the `zstyle.zsh` change (sub-step 3) |

## Options: nothing is lost

BOCO `opts.zsh` = this repo's `set_options.zsh` (identical, line for line) + the history options + `HISTFILE`/`HISTSIZE`/`SAVEHIST`/`HISTCONTROL` + `no_beep`/`unset beep`/`unset nomatch`. Every option in `set_options.zsh`, the `.zsh.histfile.opts` data and `.zsh.theme.opts` (`promptsubst`, already also set in `zshrc`) exists in BOCO's file. The only behavioural change is the history size above.

## Who sources the here-only pieces

| Piece | Sourced by | Decision |
|---|---|---|
| `set_options.zsh`, `opts` (+ `.zsh.histfile`, `.zsh.theme.opts`) | `dot_zshrc.tmpl` lines 62, 72, 79 | superseded by BOCO `opts.zsh`; remove |
| `exports.yaml`, `export` (resource branch), `ensure_resource` | `dot_zshrc.tmpl` exports loop; only user of `resource:` is `exports.yaml` (zinit clone, `ZCOMP_CACHE` mkdir) | remove; zinit is already a `.chezmoiexternal` in both repos; keep the `mkdir` (above) |
| `plugins.d/0012.local.yaml` | plugin loop | same effect as BOCO's inline `local-snippets` block; take BOCO's, with `completions` path |
| `plugins.d/0070.asdf.yaml` | plugin loop | inert (`mise` is installed); remove (MH, 2026-10-16) |
| `plugins.d/0115.fzf.yaml` | plugin loop | remove; BOCO `0015.fzf.yaml` + `fzf --zsh` arrive in Phase 1 (MH: fzf unused for now) |
| `profile.zsh` | nothing (`zshrc` has the block inline) | remove with `.zsh.profile_startup`; BOCO toggles with `~/.zsh-profile-startup` |
| `voidmobile` block in `zshrc` | hostname test, never true here | remove (MH, 2026-10-16) |
| `widgets/command-prefixes.zsh`, `widgets/twf.zsh` | only the `voidmobile` block | **park in `docs/parked/zsh-widgets/`** (MH, 2026-10-16). They bind Alt-h (vi keymaps) and `^T`; `^T` collides with fzf's `^T`, `twf` is not installed, and `.toggle-command-prefix` is defined nowhere |
| `snippets/{chezmoi,funky,memo,pyenv}.zsh.tmpl`, `functions/usage` | `snippets/*.zsh` glob / autoload | here-only, no conflict; **keep** (confirm) |
| `snippets/{mise,direnv}.zsh.tmpl`, `functions/pyproj` | same | keep-ours list |

## Switch-over results (2026-10-16, scratch pty render, clean environment)

`zshenv` switch: shell state identical to before. `zshrc` switch (`3b44920`): environment, options, aliases, `fpath`, `zstyle`, widgets and completions identical; warm startup about 0.14 s (was 0.18 s); stderr empty (was three `dephell` realpath errors); 50 fewer zinit-internal functions (loaded before only because of the `dephell` snippet); `^X^R` is `redisplay` instead of `_read_comp` (not traced; rarely used). Cleanup commit: removing `0115.fzf.yaml` dropped `^R`, Tab (fzf-tab), `^T` and `^G*` (80 functions, 46 widgets); MH uses all of them, so BOCO's fzf shell files were pulled forward from Phase 1 the same day. Against the last fzf-working render the only differences are additions (`^X^L`, fzf's completion helpers, `FZF_DEFAULT_COMMAND`). `fzf --zsh` rebinds Tab to `fzf-completion` in the insert keymap, so Tab is re-bound to `fzf-tab-complete` in `fzf.yaml`. Corrections to the first draft of this file: the BOCO `compinit` line quotes its glob qualifier, so its dump is never refreshed (kept unquoted here; `m-20` is days, not hours); BOCO's `filesystem` values are absolute while this repo's are relative, so the template is anchored with `$HOME`.

## Plugin decisions (MH, 2026-10-16)

Full list with what each plugin provided: [../zsh-plugins.md](../zsh-plugins.md). BOCO's plugin lists are adopted except `0030.direnv` (this repo's file is a fallback that builds direnv only when it is not installed; BOCO's is unconditional and would double-hook with the kept `snippets/direnv.zsh.tmpl`) and `0080.marker` (inert in both). Keeping OMZ `lib/key-bindings.zsh` was tried and reverted: its `bindkey -e` switches the main keymap to emacs and disables vi mode. For a vi-mode user the real binding losses are only vicmd `Delete`, vicmd `Shift-Tab`, `Ctrl-Delete` and vicmd `vv`; they go to the keybinding manifest (D33). The long list of lost bindings in the first scratch render was almost all the emacs keymap.

## Plugin differences (BOCO wins; these change behaviour)

Here-only plugins that BOCO's list does not load: `zsh-learn`, `zsh-git-acp`, `zsh-sed-sub`, `zplugin-crasis`, `zui`, `zi-console`, `zcolors`, OMZ `lib/key-bindings.zsh`, OMZ `fzf`, `autojump` and `vi-mode`. The `0025.vim` plugin loses `wait` and the `bindkey -v '^R' fzf-history-widget` hook and gains `MODE_CURSOR_*` settings; `0050.syntax-highlighting` loses `atinit"zicompinit; zicdreplay"`. `0030.direnv` here is guarded by `lookPath "direnv"`; BOCO's exports `DIRENV_WARN_TIMEOUT=60s`. `0080.marker` is inert in both. Dropping OMZ `key-bindings` and `vi-mode` changes the key bindings, which the `bindkey` baseline will quantify.
