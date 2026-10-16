# fzf environment. The OMZ fzf plugin used to set FZF_DEFAULT_COMMAND; BOCO's fzf
# files do not, so it is set here. ^T and fzf's file pickers use it.
if (( $+commands[fd] )); then
  export FZF_DEFAULT_COMMAND='fd --type f --hidden --exclude .git'
fi
