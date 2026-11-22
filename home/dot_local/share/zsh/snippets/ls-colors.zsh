# LS_COLORS from amontillado's theme, re-exported at the next prompt after a theme change
# (chz-n6i; replaces the zinit trapd00r/LS_COLORS plugin).
#
# amo renders vivid.yml into each theme generation (apps.vivid in amontillado's config.yaml)
# and swaps ~/.cache/theme/current's profile link atomically per apply, so resolving that link
# once per prompt (the :A modifier, no fork) is enough to notice a change. On a change the hook
# runs `vivid generate` on the new generation's vivid.yml, caches the string per generation (new
# shells read the cache instead of running vivid), and re-exports LS_COLORS and completion's
# list-colors. Fallbacks: vivid's built-in `ansi` theme (ANSI 0-15, follows the terminal
# palette) when the generation has no vivid.yml, then coreutils' dircolors default without vivid.

typeset -g _ls_colors_seen=

_ls_colors_refresh() {
  emulate -L zsh
  local cache_root=${XDG_CACHE_HOME:-$HOME/.cache}
  local gen=$cache_root/theme/current
  gen=${gen:A}
  [[ $gen == "$_ls_colors_seen" ]] && return
  _ls_colors_seen=$gen

  # One cache file per generation: <profile>.<generation>; older ones of the profile pruned.
  local dir=$cache_root/zsh/ls-colors
  local cache=$dir/${gen:h:t}.${gen:t}
  local colors=
  if [[ -r $gen/vivid.yml && -r $cache ]]; then
    IFS= read -r colors < $cache
  elif [[ -r $gen/vivid.yml ]] && (( $+commands[vivid] )) \
      && colors=$(vivid generate $gen/vivid.yml 2>/dev/null) && [[ -n $colors ]]; then
    if mkdir -p $dir 2>/dev/null; then
      rm -f -- $dir/${gen:h:t}.*(N)
      print -r -- $colors >| $cache.$$ && mv -f -- $cache.$$ $cache
    fi
  elif (( $+commands[vivid] )); then
    colors=$(vivid generate ansi 2>/dev/null)
  elif (( $+commands[dircolors] )); then
    colors=${${${(f)"$(dircolors -b)"}[1]#LS_COLORS=\'}%\';}
  fi
  [[ -n $colors ]] || return
  export LS_COLORS=$colors
  zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"
}

autoload -Uz add-zsh-hook
add-zsh-hook precmd _ls_colors_refresh
# This snippet loads in turbo mode, after the first prompt's precmd: run once now.
_ls_colors_refresh
