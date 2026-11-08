# tools/

Dev scripts for this repo. Not deployed: `tools/` sits outside the chezmoi source root (`home/`).

| Tool | What it does |
|---|---|
| [compare-trees.py](compare-trees.py) | Path-level comparison of two chezmoi source trees (the BOCO survey) |
| [zsh-probe/](zsh-probe/) | Render the zsh files into a scratch home, dump the resulting shell state, and diff two dumps |
| [home-snapshot/](home-snapshot/) | Save paths under `$HOME` and restore them exactly: the escape route for a risky apply |
| [public-scan/](public-scan/) | Pre-commit scan for this public repo: client/employer terms (pattern read from the private repo at run time) and gitleaks |
| [resume-check/](resume-check/) | One line per suspend/resume this boot with the NVIDIA errors each resume logged (the sync-FD resume bug) |
| [pick-path/](pick-path/) | Tests for `~/.local/bin/pick-path` (the shared save-path prompt): `uv run --no-project --with pytest python3 -m pytest tools/pick-path` |
| [term-contrast/](term-contrast/) | Contrast check of shell/CLI colour styles (fsh, autosuggestions, LS_COLORS, less, git, p10k) against a kitty palette |
| [wallpaper-seeds-test/](wallpaper-seeds-test/) | Tests `run_after_wallpaper-seeds.sh` (hyprpaper's default link to the committed seed; seeds added to the amontillado library) with stubbed `amo` and `curl`: link missing/hand-set/dangling, downloads, checksum mismatch, offline, no amo, non-Wayland: `tools/wallpaper-seeds-test/wallpaper-seeds-test` |
| [palette-compare/](palette-compare/) | matugen vs wallust settings on wallpapers as terminal palettes: term-contrast failures, accent contrast, distinctness and ANSI hue fidelity next to the live kitty palette, plus an HTML contact sheet: `tools/palette-compare/palette-compare.py` |
| [lock-screen-test/](lock-screen-test/) | Tests `lock-screen` (hyprlock and swaylock paths, re-lock, leftover hyprlock, concurrent locks) against a throwaway headless sway |
| [waybar-launch-test/](waybar-launch-test/) | Which monitor `waybar-launch` gives the main bar, for each dock/lid layout (stubbed `hyprctl`): `tools/waybar-launch-test/waybar-launch-test` |
| [idle-allowed-test/](idle-allowed-test/) | Tests `idle-allowed` (hypridle's `condition_cmd`, chz-cr5) against stubbed hyprctl, pw-dump and fuser: non-Chromium inhibitors count, Chromium's only with a running audio/capture stream or a fullscreen window, a busy camera counts, a failing hyprctl does not block: `tools/idle-allowed-test/idle-allowed-test` |
| [sunset-test/](sunset-test/) | Tests `sunset` (held colour temperature) and `waybar-module sunset` against a stubbed hyprsunset 0.4.0 IPC: next-change parser, hold across profiles, clamp, schedule, module text, the wake-up just after a scheduled change: `tools/sunset-test/sunset-test` |
| [hypr-effects-perf/](hypr-effects-perf/) | GPU/CPU cost of each Hyprland effect (off, blur, shadow, anim, opacity, all, all-xray) in the running session: Intel busy from RC6 (no root), NVIDIA util/power, Hyprland CPU, for a scroll and a churn phase: `tools/hypr-effects-perf/hypr-effects-perf run LABEL`, `… results` |
| [env-hyprland-test/](env-hyprland-test/) | The GPU order `~/.config/uwsm/env-hyprland` picks per profile, dock state and host keys (D60, D69), rendered and run against a fake `/dev/dri` and `/sys/class/drm`: `tools/env-hyprland-test/env-hyprland-test` |
| [git-retire-branch-test/](git-retire-branch-test/) | Tests `git-retire-branch` (D65: archive/delete finished branches) against a throwaway bare remote |
| [hypr-nested/](hypr-nested/) | A throwaway Hyprland nested in the session, in a resource-limited systemd scope, on a chosen workspace: crash triage of plugins and configs (`start --workspace N`, `ctl …`, `stop`) |
| [package-map-test/](package-map-test/) | The package installer's resolution (D32: targets, `when`, includes, `false`, per-manager names, COPRs) via `--override-data`, nothing installed |
| [bufferbloat-check/](bufferbloat-check/) | Latency under load (idle, download saturated, upload saturated) to the internet and the router hop, with throughput: before/after numbers for SQM |
| [pinned-pipx-test/](pinned-pipx-test/) | The pinned installer for MH's own pipx tools (`bd-track`, `amontillado`; `.chezmoitemplates/install/pinned-pipx-tool.sh`) against a throwaway clone with stubbed pipx/just: pin met, checkout past the tag (editable, branch untouched), checkout older than the tag, tag missing, no checkout: `tools/pinned-pipx-test/pinned-pipx-test` |
| [mani-discover-test/](mani-discover-test/) | `mani-discover`'s naming from the project registry `~/.config/projects.yaml` (D72) against throwaway clones in a fake `$HOME`: remote forms (origin and registry `remote:` as shorthand or full URL, bd-track's matching rule), an invalid remote warned, unnamed and second clones, `path:` pins, missing clones, no registry, mani parses the output: `tools/mani-discover-test/mani-discover-test` |
| [image-preview-test/](image-preview-test/) | The method `image-preview` and ranger's `scope.sh` pick per context (kitty, Windows Terminal/WSL2, foot, plain, override, fzf size, ranger with and without image preview, a shell inside ranger, image vs text routing), with stub chafa/pistol and a pty: `tools/image-preview-test/image-preview-test` |
| [registry-seed-test/](registry-seed-test/) | The project registry's chezmoi seed (`home/private_dot_config/modify_projects.yaml`, chz-vgo) fed live files on stdin: empty file seeded, live wins on conflicts, local projects, bd-track keys and comments kept, missing projects/keys added, seed header, idempotent, pass-through without mikefarah's yq or on invalid YAML: `tools/registry-seed-test/registry-seed-test` |
| [bd-timers-test/](bd-timers-test/) | `bd-timers` (chz-dg6; Super+Ctrl+T, the idle/sleep hooks) with a fake bd-track, rofi and notify-send: toggle pauses all open / resumes all paused / nothing, `pause-all` silent and never failing, the picker pauses or resumes one in its project, Escape, a failing bd-track: `tools/bd-timers-test/bd-timers-test` | after changing `bd-timers` |
| [theme-variant-test/](theme-variant-test/) | `theme-variant` (D78; the timer, Super+Ctrl+D) with fake gsettings, amo and notify-send and a fixed clock: the schedule at both edges, toggle (`default` = light) and its notice, amo gets the variant, no palette / no amo skipped, other amo failures exit 1, times from the conf file: `tools/theme-variant-test/theme-variant-test` | after changing `theme-variant` or `.chezmoidata/theme-variant.yaml` |
| [claude-transcripts-backup-test/](claude-transcripts-backup-test/) | `claude-transcripts-backup` over several backup drives (chz-6w5), in a user + mount namespace with tmpfs "drives" (no root): all mounted drives backed up; unmounted skipped; a failing drive (no repo, wrong password, read-only) fails only itself (exit 1, one notification); nothing mounted a no-op; the systemd credential preferred over `pass` | after changing `claude-transcripts-backup`, its unit or `.chezmoidata/backups.yaml` |
| [sync-repos-test/](sync-repos-test/) | `sync-repos` repo selection from the project registry (D75) against scratch clones and bare remotes: `sync: {enabled: true}` + path pushed; `false`/absent/`sync: {}` untouched; `yes`, a missing path, a scalar `sync` and the old `sync_repo` key reported (exit 1, one notification); empty or missing registry a no-op | after changing `sync-repos` or its `sync` registry keys |
| [ticket-test/](ticket-test/) | `ticket` (D72 inboxes) against a throwaway registry, inbox root and clones: default project by remote (shorthand or full URL; nested paths kept) or pinned path, unknown/missing project refused with close matches, frontmatter and sections, stdin, `$EDITOR` (empty cancels), `--quick` notes, `--list`/`--all`, `--summary` (the SessionStart line): `tools/ticket-test/ticket-test` |
| [zcomp-list/](zcomp-list/) | The candidates zsh completes for a command line, from this tree's `home/dot_local/share/zsh/completions/` in a clean zsh (zpty, `compadd` captured): `tools/zcomp-list/zcomp-list 'ticket -p '` |
| [no-home-paths/](no-home-paths/) | Pre-commit hook (`no-home-paths`): rejects staged files with `/home/$USER/`, `/run/media/$USER/` or `-home-$USER-` (username read at run time); `docs/log/` exempt: `tools/no-home-paths/no-home-paths FILE...` |
| [ticket-picker-test/](ticket-picker-test/) | `ticket-picker` (Super+T) with a scripted fake rofi and notify-send: Enter = quick note, Alt+Enter / empty Enter = editor with the line as title, cancels and an empty editor file nothing, recent projects first: `tools/ticket-picker-test/ticket-picker-test` |

## zsh-probe

```sh
uv run tools/zsh-probe/zsh-probe.py probe before --baseline main   # render a git revision
uv run tools/zsh-probe/zsh-probe.py probe after                    # render the working tree
uv run tools/zsh-probe/zsh-probe.py compare before after --show alias bindkey
uv run tools/zsh-probe/zsh-probe.py live now && uv run tools/zsh-probe/zsh-probe.py compare after now
```

`probe` takes about a minute; `compare` exits 1 if anything differs. `live <label>` dumps your *real* home the same way (read-only; shell history is switched off for the session), so you can `compare` a render against what the real shell actually does. Expect real-home-only differences: mise's PATH and functions, the p10k instant-prompt cache, anything direnv loads from the directory you ran it in, and unmanaged leftovers. Dumps go to `${ZSH_PROBE_DIR:-${XDG_CACHE_HOME:-~/.cache}/zsh-probe}/<label>/probe/`; remove a label's directory when you are done with it.
Needs `uv` (dependencies are declared inline), `chezmoi`, `git` and `zsh`, and your real zinit tree (copied, about 70 MB).
It reads the live chezmoi config but never writes to your real home or chezmoi state.

What the dump holds (one `<name>.txt` each): `env`, `env-zshenv-only` (what `zsh -c` sees), `alias`, `functions`, `fpath`, `path`, `options`, `bindkey` (every keymap), `zstyle`, `widgets`, `comps`, `comps-names`, `params`, `stderr`, plus `timing.txt` and `pty-session.txt` (the raw session, for debugging the harness).

Limits: it records shell *state*, not behaviour. It does not open an fzf picker or press a key. The startup timing is `zsh -i -c exit` (no turbo plugins) and is a smoke test, not a benchmark. Random ids and the scratch path are normalised; if two renders of one tree ever differ, find the new nondeterministic value and add it to `normalise()`.
Why the harness is built the way it is (pty, clean environment, scheduler wait): see the module docstring in `zsh-probe.py`. The planned keybinding audit (D33) should reuse `pty_session()`.

## nvim-lazy-sync

```sh
uv run tools/nvim-lazy-sync/nvim-lazy-sync.py --clean    # full clean-profile reconcile
uv run tools/nvim-lazy-sync/nvim-lazy-sync.py            # sync + verify in place
```

Regenerates the lazy.nvim lockfile (`home/lazyvim-lock.json`, symlinked to `~/.config/nvim/lazy-lock.json`) under a systemd process cap + timeout, then runs a headless load probe that scans `:messages` for real errors ("too many rounds of missing plugins", init.lua errors) while ignoring cosmetic noise. `--clean` wipes the installed plugins/state/cache and truncates the lockfile first, so the whole graph resolves fresh — use it after a big LazyVim jump. Full rationale and the luarocks/hererocks + treesitter-main gotchas are in [nvim-lazy-sync/README.md](nvim-lazy-sync/README.md) and the script's docstring.

## home-snapshot

```sh
tools/home-snapshot/home-snapshot create ~/.local/state/claude-migration-backups/zsh-apply/$(date +%F-%H%M) \
    .zshrc .zshenv .config/chezmoi/chezmoi.yml .local/share/zsh .local/share/zinit/completions .cache/zcomp
# ... apply, test ...
env -i HOME="$HOME" PATH=/usr/bin:/bin bash --noprofile --norc tools/home-snapshot/home-snapshot restore <dir>
```

Paths are relative to `$HOME`. A path that does not exist at `create` time is recorded as absent, and `restore` deletes it again. Restoring replaces whatever is there with the saved copy (files, directories and symlinks), so use it only on paths you are prepared to roll back wholesale. `restore` is plain bash plus `tar`/`rm`, so it works even when zsh or Python is broken. `home-snapshot selftest` checks create/restore against a throwaway home. Run `restore` through `env -i … bash --noprofile --norc` when the thing you changed could break your login shell.

## resume-check

```sh
tools/resume-check/resume-check                       # every suspend since boot
tools/resume-check/resume-check --since 18:20         # only suspends that started after 18:20
tools/resume-check/resume-check --since -1h --details # plus the error lines, dock-awake's log, power-key presses
```

Reads the journal only. Each row is one suspend: when it started and resumed, how many `semsurf` errors (the
nvidia-drm sync-FD error behind the black/hung kitty after resume; [../docs/open-items.md](../docs/open-items.md),
"black text in kitty") and other NVIDIA kernel errors it logged, and `clean` or `ERRORS`. An error is charged to the
suspend whose window, from `PM: suspend entry` to 10 s after `PM: suspend exit`, contains it: the kernel writes its
resume messages before the exit line (checked on the 2026-10-23 resumes). The rendering GPU is printed for the current
session only, since the journal does not record it per resume; note it yourself when you compare sessions. Kernel
messages are per boot, so `--since` before the last boot shows nothing earlier (use `journalctl -b -1 -k` after a
reboot). **It does not see black external screens:** on 2026-10-23 two resumes logged no error but left the
externals black, so look at the screens too.

## public-scan

```sh
tools/public-scan/public-scan             # changed, staged and untracked files vs HEAD, then gitleaks dir .
tools/public-scan/public-scan PATH...     # term grep on these paths only (gitleaks still scans the repo)
```

Run before every commit ([../docs/conventions.md](../docs/conventions.md), "Public vs private"). The term pattern
lives only in the private repo (`~/Source/chezmoi-boco/docs/zbook-migration/client-terms.md`; override with
`PUBLIC_SCAN_TERMS`) and is read at run time, so it never enters a public commit. Skips the untracked `ricing.md`.
Exit 1 on a hit (term or gitleaks), 2 if the pattern file is missing. Red-tested 2026-10-23 with a planted term.


## term-contrast

```sh
tools/term-contrast/term-contrast.py                         # live kitty config, failures only
tools/term-contrast/term-contrast.py --theme Blazer --theme "Tokyo Night" --sources palette,fsh,autosuggest
tools/term-contrast/term-contrast.py --conf ~/.config/kitty/current-theme.conf --all
```

Resolves the palette through kitty itself (`kitty +runpy`, so includes and defaults count as kitty sees them; `--theme` dumps one of kitty's built-in themes), collects the colour styles the shell and CLI tools use, and lists every foreground/background pair below `--min` (WCAG ratio, default 3.0). Exits 1 on any failure. The rule it enforces for a dark theme: colour 8 must be legible on the background (comments and autosuggestions use it), and no text style may use colour 0. Needs `uv`, `kitty` and `zsh`; the `fsh` source sources the plugin from your zinit tree plus `~/.config/zsh/fsh-styles.zsh`. Known noise: trapd00r's `LS_COLORS` uses fixed 256-colour dims that fail on any dark background (`--sources` without `ls` to hide them).

## palette-compare

```sh
tools/palette-compare/palette-compare.py                              # the amo library (amo list), all settings
tools/palette-compare/palette-compare.py ~/Pictures/a.jpg --settings matugen,wallust-ansi
xdg-open ~/.cache/palette-compare/index.html                          # the contact sheet
```

Runs matugen 4.x and wallust 3.x settings (`matugen`, `wallust`, `wallust-k`, `wallust-ansi`; `--help` lists the flags each one passes) on each picture in a throwaway XDG config and cache home with terminal sequences off, so live terminals and `~/.config`/`~/.cache` are untouched. Each result becomes a kitty `.conf` (matugen's base16 mapped to ANSI as base16-shell does) and is scored with term-contrast's own checks (the module is loaded from `tools/term-contrast/`; sources palette, fsh, autosuggest, git, less) plus accent contrast, the smallest OKLab distance between colours 1-6 and how many of them are near the hue their ANSI name promises. Writes `summary.json`, the confs and `index.html` to `--out` (default `~/.cache/palette-compare`). The live kitty palette is the baseline row; it scores 7.9 on distinctness, so the sheet's threshold of 8 is a rough guide. Needs `uv`, `kitty`, `zsh`, `matugen`, `wallust` and (without picture arguments) `amo`. Results of the first run (2026-10-30, chz-8bg.2): [plans/theming.md](../docs/plans/theming.md), step 1.

## git-retire-branch-test

```sh
tools/git-retire-branch-test/git-retire-branch-test
```

Builds a scratch repo and a bare "origin" in a temp dir (global git config ignored) and runs the source copy of `git-retire-branch` against them. Cases: a dry run changes nothing; `--archive` creates and pushes `refs/archive/*`, adds the fetch refspec once, deletes the branch on both sides, also for an unmerged branch; `--delete` removes a merged branch and refuses an unmerged one; refused: the target branch, the checked-out branch, a branch that differs from origin, an archive ref already at another commit; a fresh clone fetches and restores an archive. Takes about 2 s. Red-green checked (removing the unmerged guard fails `delete refuses unmerged`).

## lock-screen-test

```sh
tools/lock-screen-test/lock-screen-test                 # the source copy of lock-screen
tools/lock-screen-test/lock-screen-test ~/.local/bin/lock-screen
```

Each case starts its own headless sway (new Wayland socket, checked with `grim` before any locker runs, so the real session is never locked), runs `lock-screen` with `XDG_CURRENT_DESKTOP` set, and reads "locked" off the screen (a `grim` shot differs from the empty desktop's). Cases: Hyprland lock returns only once confirmed; a second lock is a no-op; `SIGUSR1` unlocks (the recovery path); a hyprlock left over after an unlock does not block the next lock (a stand-in process plays the leftover when hyprlock 0.9.6's exit hang does not happen on its own); two concurrent locks share one hyprlock; other desktops get swaylock. Takes about 15 s. Needs sway, grim, ImageMagick, hyprlock and swaylock.

## bufferbloat-check

```sh
tools/bufferbloat-check/bufferbloat-check                    # idle, download, upload; 30 s each
tools/bufferbloat-check/bufferbloat-check --duration 60 --phases up --streams 4
```

Pings the target (default 1.1.1.1) and the default gateway at 5/s for each phase while 2 (`--streams`) transfer
loops to Cloudflare's speed endpoints keep the link saturated, then prints a Markdown row per phase for
[../docs/runbooks/home-network.md](../docs/runbooks/home-network.md) ("Video calls and bufferbloat"). Throughput comes
from the default-route interface's byte counters (rx for idle/download, tx for upload). A gateway average that stays
near idle while the target climbs puts the queue beyond the router. Each loop runs in its own process group and is
killed with it on exit or Ctrl-C (checked 2026-10-25). Moves a few hundred MB a run; keep it off metered links.
