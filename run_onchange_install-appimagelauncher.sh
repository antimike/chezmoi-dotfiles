{{ if not (lookPath AppImageLauncher) -}}
#!/bin/env bash
# Install AppImageLauncher

declare -a INSTALL
{{ if eq .osid "linux-fedora" }}
INSTALL=(sudo dnf install -y)
EXT=rpm
URL=https://github.com/TheAssassin/AppImageLauncher/releases/download/v2.2.0/appimagelauncher-2.2.0-travis995.0f91801.x86_64.rpm
{{ else if eq .osid "linux-debian" }}
INSTALL=(sudo apt install -y)
EXT=deb
URL=https://github.com/TheAssassin/AppImageLauncher/releases/download/v2.2.0/appimagelauncher_2.2.0-travis995.0f91801.bionic_amd64.deb
{{ end }}
DEST=~/Downloads/appimagelauncher.$EXT
curl -o "$DEST" "$URL" &&
    ${INSTALL[@]} "$DEST"
{{ end }}
