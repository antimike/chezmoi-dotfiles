# shellcheck shell=bash
# rofi-bluetooth prelude: sourced right after the shebang of the pinned rofi-bluetooth
# (~/.local/bin/rofi-bluetooth; the external's filter in
# .chezmoitemplates/externals.d/bar-pickers.yaml adds the `source` line). The upstream script is
# left as it is; these two functions shadow the commands it calls.
#
#   bluetoothctl  strips ANSI codes: bluez 5.86 prints a device that advertises without the LE
#                 discoverable flags in bold grey (client/main.c print_device), which rofi drew
#                 as a tofu box and '[0' (chz-3iv). For a bare `bluetoothctl devices`, a name
#                 that several devices share gets its last MAC octet appended ("MX KEYS S (DF)"),
#                 so the script's `grep "$chosen"` finds one device, not all of them (chz-lx8).
#   rofi          on the main menu (prompt "Bluetooth"), marks the connected devices' rows
#                 active (-a), which picker.rasi draws in the amo accent, like the network
#                 picker's active connection (chz-lx8).
#
# Assumes upstream's main menu lists `bluetoothctl devices` names first, in that order (pinned
# commit 0cca4d4; re-check when bumping the pin).

bluetoothctl() {
  if [[ $# -eq 1 && $1 == devices ]]; then
    command bluetoothctl devices | _rofi_bt_strip | _rofi_bt_unique_names
  else
    command bluetoothctl "$@" | _rofi_bt_strip
  fi
}

rofi() {
  local menu
  menu=$(cat)
  local -a extra=()
  if [[ ${*: -1} == Bluetooth ]]; then
    local rows
    rows=$(_rofi_bt_connected_rows)
    [[ -n $rows ]] && extra=(-a "$rows")
  fi
  printf '%s\n' "$menu" | command rofi "$@" "${extra[@]}"
}

_rofi_bt_strip() { sed 's/\x1b\[[0-9;]*m//g'; }

# "Device <MAC> <name>" lines in; a name seen more than once gets " (<last octet>)".
_rofi_bt_unique_names() {
  awk '{ lines[NR] = $0; name = $0; sub(/^Device [^ ]+ /, "", name); names[NR] = name; seen[name]++ }
       END { for (i = 1; i <= NR; i++) {
               if (seen[names[i]] > 1) { split(lines[i], f, " "); n = split(f[2], o, ":"); print lines[i] " (" o[n] ")" }
               else print lines[i] } }'
}

# Comma-separated 0-based rows of the connected devices in `bluetoothctl devices` order.
_rofi_bt_connected_rows() {
  local connected
  connected=$(command bluetoothctl devices Connected | _rofi_bt_strip | cut -d ' ' -f 2)
  [[ -z $connected ]] && return 0
  bluetoothctl devices | grep '^Device ' | cut -d ' ' -f 2 |
    awk -v c="$connected" 'BEGIN { n = split(c, m, "\n"); for (i = 1; i <= n; i++) on[m[i]] = 1 }
                           on[$0] { r = r (r == "" ? "" : ",") NR - 1 } END { print r }'
}
