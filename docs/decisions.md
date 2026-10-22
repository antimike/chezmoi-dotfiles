---
summary: Decision log (D1–D53) for the Claude Code migration, chezmoi merge, desktop and docs; one line per decision
status: current
updated: 2026-10-22
---

# Decisions

Append new decisions at the end; mark replaced ones "superseded by Dn". "MH" is the repo owner. Sensitive specifics
(keys, client names, findings) live in the private repo; see [conventions.md](conventions.md).

## Claude Code migration (D1–D18, 2026-10-08 to 2026-10-14)

| # | Decision |
|---|---|
| D1 | Superseded: clone the employer-era chezmoi repo from GitHub with full history (the drive copy had no unique committed content). |
| D2 | All chezmoi changes for the migration go on one branch off `AddSystemdConfigs`. Merged into `main` and the branch deleted 2026-10-15 (D26). |
| D3 | Keep generic work skills and commands. Do not migrate client-project material, memory or tooling (term list is private). |
| D4 | Migrate personal projects' memory **and** transcripts. |
| D5 | claude-mem stays on hold until evaluated (open item, see [open-items.md](open-items.md)). |
| D6 | Tool installs are managed by chezmoi `run_` scripts; bootstrap-by-hand is allowed meanwhile (tracked in [bootstrap-debt.md](bootstrap-debt.md)). |
| D7 | `bd-track` owns its installer; chezmoi pins a tag and delegates. |
| D8 | User lingering is enabled through chezmoi (`/var/lib/systemd/linger`), not etckeeper. |
| D9 | Notifier is `notify-send`; a per-host adapter (`~/.claude/scripts/notify`) translates the WSL shim's interface. |
| D10 | Files copied from the exFAT drive take permissions from neighbouring files. |
| D11 | Model `opusplan`, `effortLevel: medium`. |
| D12 | Auto-memory is versioned in a private `claude-state` repo. |
| D13 | This repo is authoritative. The employer-era repo is a read-only reference clone at `~/Source/chezmoi-boco`; files move across gradually with provenance trailers. |
| D14 | Copy the former work-account repos to the personal account as plain copies (not forks); keep the old remote as read-only `upstream`. |
| D15 | Skill/command dispositions approved. Dropped: `/time-report`, `task-init`. |
| D16 | `claude-state` design approved; transcript backups go to the external SSD. |
| D17 | Repo visibility table approved; restic chosen for transcript backups; gitleaks and restic installed. |
| D18 | Follow-up: consider a LUKS-encrypted partition on the external SSD (the old backup there is unencrypted). Needs ~60 GB moved off first. Open. |

## Migration execution (2026-10-14/15)

| # | Decision |
|---|---|
| D19 | Public repos (`chezmoi-dotfiles`, `bd-track`, `claude-config`, `chess_trainer`, `resume-builder`) are scanned for client/employer references and gitleaks *before* every commit; MH reviews the redaction diff. |
| D20 | Employer-specific *data* (colleague details, tenant IDs) is held back from the public chezmoi repo pending a review and redaction pass. Applies to the Atlassian data/template, the `jira-comment-drafter` agent and the Jira CLI config. |
| D21 | `bd-track` public history is not rewritten; the current tree is cleaned instead (JSONL export untracked, client prefix replaced). |
| D22 | gpg: `pass` and all GPG operations use key `9F049F34…` (valid to 2028). Git signing key switched from the expired one; see [runbooks/gpg-and-signing.md](runbooks/gpg-and-signing.md). |
| D23 | Secret scanning uses gitleaks as a pre-commit hook (via the pre-commit framework) in each repo that needs it, not inside sync tooling. |

## BOCO chezmoi merge (see [plans/boco-merge.md](plans/boco-merge.md))

| # | Decision |
|---|---|
| D24 | The employer-era repo is authoritative for tool-specific config (all Neovim themes/plugins, zsh, `.bashrc`); exceptions are the keep-ours list in the plan. |
| D25 | Keep all personally authored BOCO tooling, even if unused here. WSL-specific items are copied and guarded **inline in templates** (shared `is-wsl` helper); employer-only tooling is guarded by a `work_tooling` data key, default false. |
| D26 | Adopt the `.chezmoiroot = home` layout here (Phase 0a). Branch strategy: `main` is trunk; `BOCO-migration` and other merged branches were deleted 2026-10-15; each phase uses a `boco-merge/<phase>` branch. |
| D27 | Mail: personal and professional accounts only; the university account is dropped. |
| D28 | `sync-repos` is ported as low-priority BOCO tooling with an empty repo list; `mani` is optional for interactive status. |

## Desktop (see [plans/wayland-desktop.md](plans/wayland-desktop.md))

| # | Decision |
|---|---|
| D29 | Add a Sway session beside GNOME. Units are scoped to their session target, not excluded per host. Keep dunst and use gammastep. One shared WM config fragment drives both i3 and Sway. *(Partly superseded by D37: SwayFX instead of plain Sway; the fragment now drives i3 and SwayFX.)* |
| D37 | Trial several compositors side by side, each listed by GDM: **SwayFX gets the full i3 port** and is the daily-driver target; niri, Hyprland and Wayfire (`simple-tile`) get minimal configs. Pick the main compositor after the trial (MH, 2026-10-17). SwayFX and Hyprland come from COPRs, pinned. |
| D38 | Run every compositor session through **uwsm** (meson install to `/usr/local`, pinned), and scope shared helper units to one hand-written `wayland-wm-session.target` (renamed `wm-helpers-wayland.target`, D47) that each compositor starts, not to `graphical-session.target` (GNOME starts that too). Rejected: per-compositor helper targets (four copies), `sway-systemd` (Sway only). Accepted by MH, 2026-10-17. |
| D39 (**draft**, awaiting MH) | Theming uses the **cache-include pattern**: chezmoi manages app configs that include generated files from `~/.cache/theme/current/`; the switcher writes only the cache. Wallpaper images are not in chezmoi (fetcher cache, optional git-annex); palettes come from the primary output's image, with outputs drawn from one palette cluster. Detail: [plans/theming.md](plans/theming.md). |
| D40 | Password picker is an own rofi/fuzzel script that never calls `pass -c`: it pipes `pass show` into `wl-copy --sensitive` (and can type with `wtype`); the `~/.local/bin/pass` wrapper still guards CLI `pass -c`. Defence in depth (MH, 2026-10-17). |
| D41 | Compositors render on the Intel iGPU; the NVIDIA card is kept for compute and opened by compositors only for scanout to its own ports (`DP-4..6`) if those are used. Stable colon-free DRM device symlinks via udev (MH, 2026-10-17). |
| D42 (**draft; parked by D50**, may be superseded by [plans/keybinding-manifest.md](plans/keybinding-manifest.md)) | One `keybindings` data tree for all apps (compositors, wlr-which-key, zsh, kitty, nvim): `generate` sections render bindings, `catalog` sections (nvim) only list them for the cheat sheet and checks. Chords and WM actions use i3/Sway syntax, translated per compositor by a table keyed on the i3 command strings. Extends D33. Detail: [plans/wayland-desktop.md](plans/wayland-desktop.md). |
| D43 | Removable drives: known drives (by UUID) automount at fixed paths; unknown drives are not automounted but get a notification with a mount action (udiskie). Safer than automounting untrusted filesystems (MH, 2026-10-17). |
| D44 | Notifications stay on **dunst** (reaffirms D29): keybinding-driven actions on the current popup, the same bindings in i3 and SwayFX, rules and pause levels. History comes from an own rofi/fuzzel browser over `dunstctl history`. SwayNotificationCenter rejected: Wayland-only, panel-centric, no documented command to act on the latest popup (MH, 2026-10-17). |
| D45 | COPRs for the compositor trial (2026-10-17): **SwayFX from `swayfx/swayfx`** (the upstream project's COPR) and **Hyprland from `sdegler/hyprland`** (successor of `solopasha/hyprland`, which now builds only for rawhide). The COPR name is the pin; COPRs are enabled lazily by the package installer, only when one of their packages is to be installed. SwayFX **replaces** Fedora's `sway` (the package conflicts with it); the fallback is `dnf swap swayfx sway`. The COPR's uwsm is not used (older than the pinned upstream build, D38). Version locking (`dnf versionlock`) is not set up yet; revisit if a COPR update breaks a config. |
| D46 | **Installers that need root prompt for sudo when `chezmoi apply` runs in a terminal** (MH, 2026-10-17): order is root → `sudo -n` (cached) → interactive `sudo` if stdin is a TTY (scripts inherit chezmoi's stdin) → otherwise print the commands and exit 1, so the next apply retries. One password prompt per fresh-machine apply instead of one aborted apply per script. Trade-off accepted: generated root steps (e.g. uwsm's `install-as-root.sh`) run without a manual read; they come from pinned, reviewed sources and stay on disk for inspection. Applies to the packages, udev, uwsm and linger scripts; new root-needing installers follow it. |
| D47 | **Session helper targets are named `wm-helpers-<scope>.target`** (MH, 2026-10-17): `wm-helpers-wayland.target` (was `wayland-wm-session.target`, D38) and `wm-helpers-x11.target` (was `xsession.target`); Wayland-only or X11-only units carry the scope as a suffix (`clipboard-stack-wayland.target`). A `wm-helpers-common.target`, pulled in by both, is added only when a helper works on both. Why: uwsm owns the `wayland-wm-*` and `wayland-session-*` unit prefixes, so the old name could collide with a future uwsm unit; the old clipboard name hid that it is Wayland-only. `i3-session.target` (i3 entry point started by `~/.xsession`) keeps its name. |
| D48 | **No broken code or configs in the repo** (MH, 2026-10-17): whatever chezmoi deploys must work on the hosts and sessions it renders for. What cannot be fixed yet is template-guarded out or removed; known breakage has an open item until then. Applies to i3: if its config stays, it must work (helper scripts ported, i3 login test), otherwise it goes. Helper scripts that both i3 and SwayFX need are ported once, to `~/.local/bin`, written to work in X11 and Wayland sessions (like `clip`). Rule in [conventions.md](conventions.md). |
| D49 | **i3 stays, fixed rather than dropped** (MH, 2026-10-17): the target is MH's old MacBook Pro (origin of `i3-config-mbp`), which may come back as a chezmoi host running i3 on X11, possibly on an older Fedora. Until then zbook is the i3 test bed (GDM 50 still starts X11 sessions; i3 and Xorg are installed), so the i3 login test runs here. Consequences: the i3/SwayFX shared fragment (step 3) stays; helper scripts must work in X11 and Wayland sessions and must not assume zbook's hardware (device names come from host data). The MacBook itself is a deferred open item. |
| D50 | **Functional daily driver first; structural refactors are side quests** (MH, 2026-10-18). MH needs to start a job search soon, and the desktop exists to make that easy. Main line: the functional SwayFX checklist in [plans/wayland-desktop.md](plans/wayland-desktop.md) ("Functional daily driver"), with a deadline (MH: Tuesday 2026-10-20). Parked as spare-time work: the keybinding manifest (D33, D42; Lua redesign in [plans/keybinding-manifest.md](plans/keybinding-manifest.md)), the package map refactor (D32; new packages are installed by hand and added to `packages.yaml` afterwards), theming, and any repo work for niri, Hyprland and Wayfire (they write default configs on first launch and their GDM entries exist). Scripts from `i3-config-mbp` are ported only when a checklist item needs them. Amends D49: to meet D48 quickly, the i3 config stops deploying on zbook until the MacBook work starts (the shared fragment stays). Binding lookup comes from a cheat sheet that reads the running config, not from a manifest. |
| D51 | **Keep gnome-keyring as the Secret Service; make SwayFX unlock it like GNOME, and keep pinentry out of it** (MH, 2026-10-18). Not disabled: Chromium's `--password-store=basic` stores passwords and cookies under a hard-coded key, masking the D-Bus service breaks GNOME and every libsecret app, and GNOME depends on the package. No `pass` bridge (`pass-secret-service`, KeePassXC as Secret Service): every secret would need a GPG decrypt, so Chromium could not start (or would lose its cookies) without the YubiKey, for app keys MH never reads; `pass` stays for MH's own credentials. Implementation: the SwayFX config runs `gnome-keyring-daemon --start --components=secrets` (GNOME does this in GNOME-only autostart entries) so the daemon unlocked by GDM's PAM step is taken over; `gpg-agent.conf` sets `no-allow-external-cache`. Fallback if the PAM daemon still dies before the handoff: the `gnome-keyring-daemon.socket` user unit, accepting one unlock prompt per login. Detail: [plans/wayland-desktop.md](plans/wayland-desktop.md), "Functional daily driver". |
| D52 | **Amends D41: render on NVIDIA when an external monitor is on its ports** (MH, 2026-10-18). Every external output on zbook (HDMI, mini-DP, USB-C) is wired to the NVIDIA card (`DP-4..6`); only the laptop panel is on Intel. MH wants external monitors drawn directly by NVIDIA rather than rendered on Intel and copied over. `~/.config/uwsm/env` (template; NVIDIA block rendered on zbook only) decides once at login: an NVIDIA connector connected → `WLR_DRM_DEVICES`/`AQ_DRM_DEVICES` gets the NVIDIA card too; none → Intel only (NVIDIA stays asleep, battery). Which card renders is the `prefer_nvidia_for_external` data key: `true` = `dgpu:igpu` (NVIDIA renders, the panel gets a copy), `false` = `igpu:dgpu` (Intel renders, frames copied to NVIDIA). **`false` for now**: MH tests Intel-first first, to see how bad the stutter is, before adopting NVIDIA-first. Hotplug mid-session needs a re-login. Panel-on-NVIDIA would need a BIOS discrete-graphics mode, if this model has one (unchecked). Fallback: GNOME for meetings. Detail: [plans/wayland-desktop.md](plans/wayland-desktop.md), "Functional daily driver". |
| D53 | **Amends D52: on zbook, always open the NVIDIA card, Intel renders; output layouts by kanshi** (MH, 2026-10-21). The NVIDIA card has no runtime D3 (`/proc/driver/nvidia/gpus/*/power`: "Not supported"), so it never sleeps and idles at P8 (~2.7 W) whether or not the compositor holds it: `WLR_DRM_DEVICES=igpu:dgpu` at every login costs no power and lets monitors be plugged in mid-session. Intel-first because it leaves the NVIDIA 3D engine and most of its 4 GB free for compute (NVIDIA only scans out copied frames) and because NVIDIA-first left the laptop panel black under SwayFX (`Failed to allocate buffer, no swapchain`, 2026-10-21). `prefer_nvidia_for_external` stays as the experiment switch. Layouts, modes and scales move from static sway `output` lines to kanshi profiles (`~/.config/kanshi/config`), matched by make/model/serial, so they apply on hotplug; device-specific settings (kanshi profiles, WirePlumber priorities) are not host-guarded, since they match devices that may also meet the MacBook (D49); only the GPU logic is zbook-only. |
| D30 | The 2 gitleaks findings in the tree (a polybar-weather API key in a service template, a Jupyter service-key `.pem`) are expected and accepted (MH, 2026-10-15); a scan showing anything else is a stop. Since 2026-10-17 both are listed in `.gitleaksignore`, so a scan shows none. |

## Tooling (proposed)

| # | Decision |
|---|---|
| D32 (**draft; parked by D50**: designed in spare time) | Make package installation distro-agnostic with a **logical-name package map** in `home/.chezmoidata/packages.yaml`: one entry per tool, per-manager overrides only where names differ, a single derived manager key, and one installer that does the lookup. Tools that are not natively packaged (or whose native package is a different program) use a fallback *method* in the same map (`pipx`, `mise`, `cargo`, or the repo's pinned-release installer), plus an optional `verify:` check. Conditionals do **not** go in individual templates. Nix derivations were rejected for now: they need a Nix install and a second package ecosystem on every host, solve a problem `mise` backends and the existing pinned installers already cover, and add a new language to maintain. Detail: [open-items.md](open-items.md#detail-package-map-refactor). Note: the table above already contains two rows numbered D30; renumber when convenient. |
| D33 (**draft; parked by D50**; format may be superseded by [plans/keybinding-manifest.md](plans/keybinding-manifest.md)) | zsh key bindings come from **one YAML manifest** (generalising BOCO's `fzf.keybindings`) rendered into a snippet that loads after all plugins, with a render-time duplicate check and a runtime audit script that reports overridden, undefined and unclaimed bindings. Done after the BOCO zsh switch-over, not as part of it. Detail: [plans/boco-merge.md](plans/boco-merge.md), "Keybinding manifest". |

## Documentation

| # | Decision |
|---|---|
| D30 | Docs live in `docs/`, are organized for Claude to navigate (see [README.md](README.md)), and are public, so sensitive material goes to the private repo. `CLAUDE.md` + `docs/STATUS.md` replace one-shot session prompts. |
| D31 | Superseded plan drafts and the scratch notes file are deleted (rollback copy kept locally in `~/.local/state/claude-migration-backups/docs-2026-10-15/`). |

## Hardware and security

| # | Decision |
|---|---|
| D34 | scdaemon reaches the YubiKey **through pcscd in shared mode** (`disable-ccid` + `pcsc-shared` in `~/.gnupg/scdaemon.conf`), rendered only on hosts where pcscd is installed (MH, 2026-10-17). Reason: once pcscd runs it owns the CCID interface, and gsd-smartcard and Chromium keep the card open, so the built-in driver and an exclusive connect both fail. Accepted trade-off: GnuPG calls shared mode "somewhat dangerous" (scdaemon caches card state and keeps the PIN verified, so another PC/SC client in the session could use the unlocked card). Rejected: exclusive mode with gsd-smartcard and Chromium's card access disabled (loses lock-on-removal, Chromium's holder is hard to pin down). Detail: [runbooks/gpg-and-signing.md](runbooks/gpg-and-signing.md). |

## Repos, hooks and sync

| # | Decision |
|---|---|
| D35 | **Where repos are cloned is discovered, not listed in chezmoi data** (MH, 2026-10-17). A generated, unmanaged `~/mani.yaml` (one project per clone found under a few root folders) is the registry of hand-made clones; the tasks run on it live in the chezmoi-managed `~/.config/mani/config.yaml`. **Pre-commit hooks are keyed off each repo's committed `.pre-commit-config.yaml`**: the install task runs `pre-commit install` in every clone whose config has a gitleaks hook, so making a repo scanned means committing that file and nothing else. Replaces the plan's hand-kept `mani` task list. ghq was rejected: it only sees repos under its own root, and the chezmoi source, `~/.claude/projects` and `~/.local/src/bd-track` cannot move there. |
| D36 | **The `sync-repos` list holds only repos chezmoi itself provisions** (fixed, known paths, so the list stays in the `sync-repos-list` template; no mani), and **unattended commits scan for secrets themselves** instead of relying on a per-clone hook, which can be silently missing (`claude-config` and `chess_trainer` have committed pre-commit configs whose hooks were never installed in these clones) (MH, 2026-10-17). Next: give `sync-repos` `claude-state-sync`'s gitleaks scan, `pull --rebase` and failure notifications, make `claude-state` its first entry and retire `claude-state-sync`. Deferred: one `dstask` repo provisioned by chezmoi with a remote, then listed. Amends D28. |

## Resolved questions (migration)

- **Q2 notifier:** `notify-send` plus the adapter; every caller (hooks, auto-session, `/reminder`, `/alert-timer`) uses the adapter.
- **Q3 timew:** not needed; bd-track 0.5 dropped it (SessionEnd hook uses `bd-track status`).
- **Q6 settings:** `modify_settings.json.tmpl` manages `cleanupPeriodDays`; model, effort, `autoCompactEnabled`, `awaySummaryEnabled` are set only if absent.
- **Q13 backups:** restic over rsync because the SSD is exFAT (no hard links), so rsync could only keep one unencrypted mirror.
