# Shared by the run_onchange_install-*.sh.tmpl installers: they pull it in with
# includeTemplate (passing the root context) right after `set -eu`. Do not write
# template delimiters in this comment; it is itself rendered. Defines install_completion, which asks a freshly
# installed tool for its zsh completion script and writes it into the managed
# completions directory.
#
# Why the installer and not a render-time `output` template: chezmoi renders
# templates before it runs install scripts, so on a first `chezmoi apply` the
# tool is not on PATH yet and the completion would render empty until the next
# apply. Here it exists on the first apply. The files are generated and
# unmanaged; zsh sees a new one only after `rm ~/.zcompdump*`.
#
# Usage: install_completion <tool> <binary> <args...>
#   install_completion cheat "$INSTALL_PATH" --completion zsh
# Call it on every run, including the "already installed" early exit, so a host
# that has the binary but no completion still gets one. It never fails the
# install: a generator that errors, or output that is not a zsh completion,
# only produces a warning.
install_completion() {
  comp_tool=$1
  comp_bin=$2
  shift 2
  comp_dir={{ joinPath .chezmoi.homeDir ".local" "share" "zsh" "completions" | quote }}

  if [ ! -x "$comp_bin" ]; then
    return 0
  fi
  mkdir -p "$comp_dir"
  comp_tmp=$(mktemp "$comp_dir/.$comp_tool.XXXXXX")
  if "$comp_bin" "$@" > "$comp_tmp" 2>/dev/null \
      && head -n 1 "$comp_tmp" | grep -q '^#compdef'; then
    mv "$comp_tmp" "$comp_dir/_$comp_tool"
    echo "$comp_tool installer: wrote $comp_dir/_$comp_tool" >&2
  else
    rm -f "$comp_tmp"
    echo "$comp_tool installer: no usable zsh completion from '$comp_bin $*'; skipping" >&2
  fi
  return 0
}
