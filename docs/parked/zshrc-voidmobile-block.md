---
summary: The hostname-gated voidmobile block removed from dot_zshrc.tmpl, kept verbatim for reference
status: parked
updated: 2026-10-16
---

# Parked: the `voidmobile` block from `dot_zshrc.tmpl`

Removed from the template on 2026-10-16 (BOCO zsh switch-over; MH: "park it"). It rendered only when `.chezmoi.hostname` was `voidmobile`, the older machine MH still owns. Other templates still treat that host specially: `.chezmoi.yml.tmpl` (`enable_systemd_session_services`), `dot_Xresources.tmpl`, `executable_dot_xsession.tmpl`.

What it did: moved `ZDOTDIR` to `~/.config/zsh`; loaded `snippets/`, `env/`, `alias/` and `widgets/` from that old, pre-chezmoi layout (those directories are **not** in this repo; its equivalents live under `~/.local/share/zsh`); and defined the bare-repo dotfiles alias `config`. `ZDOTDIR` set inside `.zshrc` comes too late to relocate `.zshrc` itself.

If `voidmobile` is brought onto this repo's zsh layout, delete this file. If it must keep the old layout, restore the block below inside the user-configuration section of `dot_zshrc.tmpl`.

```
{{ if eq .chezmoi.hostname "voidmobile" }}
export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-${HOME}/.config}"
export ZDOTDIR="${XDG_CONFIG_HOME}/zsh"
export CACHEDIR="$HOME/.local/share"
[[ -d "$CACHEDIR" ]] || mkdir -p "$CACHEDIR"


zinit wait lucid light-mode as"null" multisrc'*.zsh' for \
    ${ZDOTDIR}/snippets

# Load in light-mode: no reporting (this speeds up the process considerably)
zinit wait lucid light-mode for \
    multisrc'{env,alias,widgets}/*.zsh' \
        _local/config

alias config='/usr/bin/git --git-dir=$HOME/.dotfiles/ --work-tree=$HOME'
{{ end }}
```
