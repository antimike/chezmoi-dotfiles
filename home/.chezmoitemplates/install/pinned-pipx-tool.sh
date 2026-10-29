{{- /*
Install one of MH's own pipx tools at a pinned release tag, without touching a developer checkout.
Included by run_onchange_install-<tool>.sh.tmpl with a dict:
  name       label for messages (e.g. "bd-track")
  package    pipx venv / package name
  repo_url   git URL to install from when there is no clone
  ref        pinned tag (vX.Y.Z); the installed version must be at least this
  clone_dir  developer checkout, relative to $HOME
  requires   space-separated commands checked first (git, pipx, jq are always checked)

Order:
  1. Installed version >= pin: nothing to do (an editable install from the clone counts).
  2. Clone exists: never checkout, reset or switch branches in it. If the pinned tag is in the
     checkout's history, install the checkout as it is with the project's `just install-dev`
     (editable); if not, the checkout is older than the pin: fail and say so (pull it first).
  3. No clone: pipx install from git at the tag (not editable).
Exits 1 on failure so the next apply retries (D46).
*/ -}}
set -eu

NAME={{ .name | quote }}
PACKAGE={{ .package | quote }}
REF={{ .ref | quote }}
REPO_URL={{ .repo_url | quote }}
CLONE_DIR={{ .clone_dir | quote }}

say() { echo "$NAME installer: $*" >&2; }
fail() { say "$*"; exit 1; }

for tool in git pipx jq {{ .requires }}; do
  command -v "$tool" >/dev/null 2>&1 || fail "$tool not found on PATH"
done

installed_version() {
  pipx list --json 2>/dev/null |
    jq -r --arg p "$PACKAGE" '.venvs[$p].metadata.main_package.package_version // empty'
}

# True if version $1 >= version $2.
version_ge() {
  [ "$(printf '%s\n%s\n' "$1" "$2" | sort -V | head -n 1)" = "$2" ]
}

want=${REF#v}
have=$(installed_version)
if [ -n "$have" ] && version_ge "$have" "$want"; then
  say "$have installed (pin $REF); nothing to do"
  exit 0
fi

if [ -d "$CLONE_DIR/.git" ]; then
  git -C "$CLONE_DIR" fetch --tags --quiet || say "git fetch failed; using the tags already in $CLONE_DIR"
  git -C "$CLONE_DIR" rev-parse -q --verify "refs/tags/$REF^{commit}" >/dev/null ||
    fail "tag $REF not found in $CLONE_DIR"
  git -C "$CLONE_DIR" merge-base --is-ancestor "$REF" HEAD ||
    fail "$CLONE_DIR ($(git -C "$CLONE_DIR" describe --tags --always)) is older than $REF; update it (e.g. git -C $CLONE_DIR pull), then run chezmoi apply again"
  command -v just >/dev/null 2>&1 || fail "just not found on PATH"
  say "installing the checkout in $CLONE_DIR ($(git -C "$CLONE_DIR" describe --tags --always), editable)"
  just --justfile "$CLONE_DIR/justfile" --working-directory "$CLONE_DIR" install-dev
else
  say "installing $REF from $REPO_URL"
  # pipx install --force fails on re-runs when pipx creates venvs with uv: uninstall first.
  pipx uninstall "$PACKAGE" >/dev/null 2>&1 || true
  pipx install "git+$REPO_URL@$REF"
fi

have=$(installed_version)
if [ -z "$have" ] || ! version_ge "$have" "$want"; then
  fail "installed version is '${have:-none}', pin is $REF"
fi
say "$have installed"
