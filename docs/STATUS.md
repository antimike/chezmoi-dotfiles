---
summary: Where the work stands and what to do next; the repo's standing session-start prompt
status: current
updated: 2026-10-17
---

# Status

## Where we are
- Claude Code migration (BOCO/WSL2 → zbook, Fedora 44): **done** except the claude-mem evaluation. Log: [log/migration-steps.md](log/migration-steps.md).
- Dev environment is functional: chezmoi applied, tools pinned, `bd`/`bd-track`, `claude-state` sync and restic backups running, GPG on the YubiKey.
- `main` is trunk (**history rewritten and force-pushed 2026-10-17**; see below), in sync with origin. All merged `boco-merge/*` branches are deleted; `boco-merge/3-hooks` is open (below). Docs consolidated into this tree on 2026-10-15.
- BOCO merge **Phase 3 timers and services merged to `main` and pushed 2026-10-17** (merge `5ab6ded`): `sync-repos` (empty list, so no timer), `dstask-notify` (weekdays 09:30 via `notify`; MH kept `~/.dstask`, timer enabled), `rano` (all `work_tooling`-guarded). Same day: the reload script became `run_after_` (guard flips were missed; `chezmoi status` now always lists ` R reload-systemd-user.sh`).
- BOCO merge **Phase 3 gitleaks hook rollout merged and pushed 2026-10-17** (merge `c26baff`; branch deleted): D35/D36; `mani-discover` generates the unmanaged `~/mani.yaml` and the managed `~/.config/mani/config.yaml` has `install-hooks`/`status` tasks; chezmoi repo has `.pre-commit-config.yaml` + `.gitleaksignore` (scan 0). Hooks red/green-tested and pushed in chezmoi, `chess_trainer`, `resume-builder`, `claude-state`. `bd-track`/`claude-config` **deferred** (open item).
- **`sync-repos` hardened and pushed 2026-10-17** (`d1e5cdf`, `6ad8fe4`): in-script gitleaks, `pull --rebase`, `notify`, network wait, 3 retries; now syncs claude-state, and `claude-state-sync` is retired (it had been failing on DNS at resume). Runbook: [runbooks/memory-and-backups.md](runbooks/memory-and-backups.md).
- YubiKey after the reboot (2026-10-17): pcscd owned the reader; fixed with `~/.gnupg/scdaemon.conf` (`disable-ccid`, `pcsc-shared`), rendered only where pcscd is installed (D34, pushed). Runbook: [runbooks/gpg-and-signing.md](runbooks/gpg-and-signing.md).
- BOCO merge **Phase 2 (Neovim) done, merged to `main` and pushed 2026-10-17** (merge commit `fbc8169`; branch deleted 2026-10-17). All 39 BOCO plugin specs + config ported into `private_dot_config/nvim/`; adopted current LazyVim 16.0.1 (blink.cmp, treesitter `main`); modern `mason.lua` superseded the old `mason-lspconfig.lua`; lockfile regenerated on a clean profile (123 plugins) and validated by a headless load with no config errors; `run_once_install_neovim_deps.sh.tmpl` ported distro-gated (venv step live-tested, rest runs on next apply); `venvDir`/`npmDir` added to `.chezmoi.yml.tmpl`. luarocks enabled via forced hererocks in `lazy.lua` (`rocks = { enabled = true, hererocks = true }`; system luarocks is Lua 5.4, Neovim is 5.1). New helper `tools/nvim-lazy-sync/` regenerates+validates the lockfile. **Post-merge:** pinned `neovim` to `0.11.7` (floating `latest` → 0.12.6 broke lualine/checkhealth and caused `E5009: Invalid $VIMRUNTIME`); added mmdc + `latex` parser + lazygit (go) for Snacks.image/lazygit. Details: [plans/boco-merge.md](plans/boco-merge.md) "Phase 2", [bootstrap-debt.md](bootstrap-debt.md).
- BOCO merge **Phase 1 (self-contained tools) done and on `main`** (force-pushed 2026-10-17). Before the push the whole history was rewritten with `git filter-repo` to purge client-term hits: bundle backup at `~/.local/state/claude-migration-backups/chezmoi-prerewrite-20261016-233103.bundle`, 7 okular/vifminfo path spellings dropped, the `client-terms.md` pattern scrubbed from all blobs and 5 commit messages, verified 0 hits across all 246 commits and the branch tip tree byte-identical to the pre-rewrite tip, origin re-added, 5 in-repo doc SHAs remapped from the commit-map. Every old commit SHA changed. **Outstanding (MH):** the GitHub Support request to purge GitHub's cached commit views of the old SHAs — until then the old terms stay viewable at `github.com/.../commit/<old-sha>` URLs.
- `@docs/STATUS.md` import in `CLAUDE.md` verified working (2026-10-15): STATUS.md is in context at session start without a Read.
- BOCO merge **Phase 0a done and on `main`** (2026-10-15): chezmoi source root is now `home/`; docs, `tools/`, `CLAUDE.md`, `.envrc` and `.ripgreprc` stay at the repo root.
- BOCO merge **Phase 0 done** (2026-10-16): `is-wsl` helper, `work_tooling` key, systemd reload script, git/GPG/SSH config (branch `0b`, on local `main`); zsh switch-over (branch `0c-zsh`, applied and merged; snapshot in `~/.local/state/claude-migration-backups/zsh-apply/`). Details: [log/zsh-step4-inventory.md](log/zsh-step4-inventory.md), [zsh-plugins.md](zsh-plugins.md). New tools: `tools/zsh-probe/`, `tools/home-snapshot/`.
- **Wayland desktop step 2 (session plumbing) built and applied 2026-10-17** on branch `wayland/2-session-plumbing` (pushed, not merged): `wm-helpers-wayland.target`, `~/.config/uwsm/env` (`WLR_DRM_DEVICES`/`AQ_DRM_DEVICES`), minimal `~/.config/sway/config`. D47 renamed the session targets to `wm-helpers-<scope>` (`xsession.target` → `wm-helpers-x11.target`, `clipboard-stack.target` → `clipboard-stack-wayland.target`); the X11 rename is verified with `systemd-analyze` only, not an i3 login. Login test pending.
- **Wayland desktop steps 0 and 1 done, merged to `main` and pushed 2026-10-17** (branch `wayland/0-1-sessions`). Recovery checks done (console login works; `/etc` clean at etckeeper `0f391be`); driver-matched udev rule for `/dev/dri/igpu`/`dgpu`; `packagesWayland` with lazily enabled COPRs (`swayfx/swayfx`, `sdegler/hyprland`; D45; SwayFX **replaces** Fedora's `sway`); uwsm 0.27.0 in `/usr/local` with GDM entries SwayFX/niri/Wayfire (uwsm). Root-needing installers now prompt for sudo in a terminal (D46). Side fix: YubiKey PIN prompts on a text console (`pinentry-auto` + `PINENTRY_USER_DATA`; run `sshstart` back in the GUI). Details: [plans/wayland-desktop.md](plans/wayland-desktop.md) steps 0-1, [open-items.md](open-items.md).
- **Wayland desktop planning done 2026-10-17** (merged branch `docs-wayland-plan`). MH's untracked `ricing.md` is folded into the plans (item-by-item map in [plans/ricing-backlog.md](plans/ricing-backlog.md)) but **kept unmodified at the repo root for MH's review**; MH deletes it, and it is never committed. Plans: [plans/wayland-desktop.md](plans/wayland-desktop.md) (compositor trial: SwayFX full i3 port, niri/Hyprland/Wayfire minimal; uwsm D38; Intel-only rendering D41; own password picker D40; one keybinding tree, draft D42; greeter last), [plans/devices-and-audio.md](plans/devices-and-audio.md) (D43 notify-then-mount), [plans/theming.md](plans/theming.md) (after the daily driver; draft D39), [runbooks/display-session-recovery.md](runbooks/display-session-recovery.md). Source repos `i3-config-mbp`, `i3wm-configuration`, `arcolinux-i3wm` cloned to `~/Source/antimike/`.
- A private doc (keys, findings, client terms) is committed in `~/Source/chezmoi-boco` but **not pushed** (waiting for MH's OK).

## Next actions (in order; reprioritized by MH 2026-10-17)
1. **GitHub Support request (MH)** to purge cached views / stale refs of the old (pre-rewrite) SHAs on `antimike/chezmoi-dotfiles`. The force-push is done; this is the last step that keeps the old client terms reachable until GitHub acts.
2. **Wayland desktop, step 2: login test (MH).** Plumbing is built and applied on branch `wayland/2-session-plumbing`
   (not merged): helper target, uwsm env (`WLR_DRM_DEVICES`), minimal SwayFX config. MH logs into `SwayFX (uwsm)` at GDM
   (this also confirms GDM lists the uwsm entries) and runs the 5 checks in [plans/wayland-desktop.md](plans/wayland-desktop.md),
   "Step 2 login test". Pass → merge, then step 3 (shared fragment split). Waiting on MH: the `DP-4..6` socket check (backlog).
3. **kitty: merge and debug pass.** Merge BOCO's `kitty.conf` (taken out of Phase 5; guard WSL-only lines) and fix what is broken, including the `notes` launcher pointing at a missing `~/.config/i3/bin/open-notes.bash` ([open-items.md](open-items.md)). Best done once SwayFX runs, since kitty is the terminal there.
4. Atlassian/Jira review pass when MH schedules it.
5. Phase 4 (mail): **low priority** (MH: time-consuming, and webmail covers the need).

Deferred: hooks in `bd-track`/`claude-config`; chezmoi provisioning of `claude-state` and of one `dstask` repo (all in [open-items.md](open-items.md)).

## Blockers / watch
- `gitleaks dir .` reports **no leaks**: the 2 accepted findings (D30) are in `.gitleaksignore` by `file:rule:line` fingerprint. If one of those files changes so the finding moves line, it reappears: re-review, then refresh the fingerprint. Anything else is a stop.
- The YubiKey must be plugged in for pushes, signing tags, `pass`, and the backup/sync timers.
- Atlassian/Jira items are held until a redaction pass ([plans/boco-merge.md](plans/boco-merge.md), "Held items").
- No second machine for testing the zsh switch-over; use the scratch-home method in the plan.

## Start prompt (paste when starting or restarting a session outside this directory)
> Work in `~/.local/share/chezmoi`. Read `CLAUDE.md` and `docs/STATUS.md`, then continue with "Next actions". Confirm with me before pushing, deleting remote branches, or anything outward-facing. Follow `docs/conventions.md`; the repo is public, so scan for client/employer terms and gitleaks before committing.

## At session end
Update this file (what changed, next actions, blockers), `docs/open-items.md`, and add any decision to `docs/decisions.md`. Commit docs separately.
