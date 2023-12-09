#!/bin/zsh

# Example of how to call .toggle-command-prefix
# NOTE: `sudo` prefix is already handled by OMZ plugin (bound to Esc-Esc)
function .toggle-sudo () {
	.toggle-command-prefix 'sudo ' 'sudo' \
		'-(S|A|-askpass|h|-help|K|-remove-timestamp|k|-reset-timestamp|l|-list|n|-non-interactive|S|-stdin|V|-version|v|-validate|e|-edit|s|-shell|i|-login|b|-background|E|H|-set-home|P|-preserve-groups|opt_args|(C?|-close-from=|g?|-group=|h?|-host=|p?|-prompt=|r?|-role=|t?|-type=|T?|-command-timeout=|U?|-other-user=|u?|-user=|-preserve-env=)*)' \
		'-(C|-close-from|g|-group|h|-host|p|-prompt|r|-role|t|-type|T|-command-timeout|U|-other-user|u|-user)'
}

function .toggle-run-help () {
        .toggle-command-prefix 'run-help ' 'run-help'
}

zle -N {,.}toggle-run-help
for m in viins vicmd; do
        bindkey -M $m '^[h' toggle-run-help
done
