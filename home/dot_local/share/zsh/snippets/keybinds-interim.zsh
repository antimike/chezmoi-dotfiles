# Interim key bindings until the keybinding manifest replaces them (D33).
# Loaded by the local-snippets glob after zsh-vim-mode, so these win.

# ^N / ^P in insert mode: step through history one entry at a time.
# (BOCO's plugin list makes them prefix searches.)
bindkey -M viins '^N' down-history
bindkey -M viins '^P' up-history

# Bindings lost when OMZ vi-mode and key-bindings were dropped.
bindkey -M vicmd '^[[3~' delete-char                 # Delete
bindkey -M vicmd '^[[Z' reverse-menu-complete        # Shift-Tab
bindkey -M viins '^[[3;5~' kill-word                 # Ctrl-Delete
bindkey -M vicmd '^[[3;5~' kill-word
bindkey -M vicmd 'vv' edit-command-line              # edit the command line in $EDITOR

# Not a key binding, but kept here with the other interim fixes: pass ANSI colours
# through less. zcolors' LESS theme has no -R.
[[ " $LESS " == *" -R "* ]] || export LESS="-R${LESS:+ $LESS}"
