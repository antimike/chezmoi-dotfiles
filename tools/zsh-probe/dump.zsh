PD="$HOME/probe"
{ env | sort } > $PD/env.txt
alias > $PD/alias.txt
print -l ${(ok)functions} > $PD/functions.txt
print -l $fpath > $PD/fpath.txt
print -l $path > $PD/path.txt
{ setopt; print ---; unsetopt } > $PD/options.txt
{ for m in ${(ok)keymaps}; do print "## $m"; bindkey -M $m -L; done } > $PD/bindkey.txt
zstyle -L > $PD/zstyle.txt
print -l ${(ok)widgets} > $PD/widgets.txt
print ${#_comps} > $PD/comps.txt
print -l ${(ok)_comps} > $PD/comps-names.txt
zinit zstatus > $PD/zinit-status.txt 2>&1
zinit times > $PD/zinit-times.txt 2>&1
print -l ${(ok)parameters} > $PD/params.txt
