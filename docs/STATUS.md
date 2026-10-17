---
summary: Where the work stands and what to do next; the repo's standing session-start prompt
status: current
updated: 2026-10-17
---

# Status

## Where we are
- Claude Code migration (BOCO/WSL2 → zbook, Fedora 44): **done** except the claude-mem evaluation. Log: [log/migration-steps.md](log/migration-steps.md).
- Dev environment is functional: chezmoi applied, tools pinned, `bd`/`bd-track`, `claude-state` sync and restic backups running, GPG on the YubiKey.
- `main` is trunk and in sync with origin (**history rewritten and force-pushed 2026-10-17**, now `cd888d3`; see below). The `boco-merge/0a`, `0b` and `0c-zsh` branches are merged and deleted. Docs consolidated into this tree on 2026-10-15.
- BOCO merge **Phase 2 (Neovim) done, merged to `main` and pushed 2026-10-17** (merge commit `fbc8169`; `boco-merge/2-nvim` kept locally, undeleted). All 39 BOCO plugin specs + config ported into `private_dot_config/nvim/`; adopted current LazyVim 16.0.1 (blink.cmp, treesitter `main`); modern `mason.lua` superseded the old `mason-lspconfig.lua`; lockfile regenerated on a clean profile (123 plugins) and validated by a headless load with no config errors; `run_once_install_neovim_deps.sh.tmpl` ported distro-gated (venv step live-tested, rest runs on next apply); `venvDir`/`npmDir` added to `.chezmoi.yml.tmpl`. luarocks enabled via forced hererocks in `lazy.lua` (`rocks = { enabled = true, hererocks = true }`; system luarocks is Lua 5.4, Neovim is 5.1). New helper `tools/nvim-lazy-sync/` regenerates+validates the lockfile. **Post-merge:** pinned `neovim` to `0.11.7` (floating `latest` → 0.12.6 broke lualine/checkhealth and caused `E5009: Invalid $VIMRUNTIME`); added mmdc + `latex` parser + lazygit (go) for Snacks.image/lazygit. Details: [plans/boco-merge.md](plans/boco-merge.md) "Phase 2", [bootstrap-debt.md](bootstrap-debt.md).
- BOCO merge **Phase 1 (self-contained tools) done and on `main`** (force-pushed 2026-10-17). Before the push the whole history was rewritten with `git filter-repo` to purge client-term hits: bundle backup at `~/.local/state/claude-migration-backups/chezmoi-prerewrite-20261016-233103.bundle`, 7 okular/vifminfo path spellings dropped, the `client-terms.md` pattern scrubbed from all blobs and 5 commit messages, verified 0 hits across all 246 commits and the branch tip tree byte-identical to the pre-rewrite tip, origin re-added, 5 in-repo doc SHAs remapped from the commit-map. Every old commit SHA changed. **Outstanding (MH):** the GitHub Support request to purge GitHub's cached commit views of the old SHAs — until then the old terms stay viewable at `github.com/.../commit/<old-sha>` URLs.
- `@docs/STATUS.md` import in `CLAUDE.md` verified working (2026-10-15): STATUS.md is in context at session start without a Read.
- BOCO merge **Phase 0a done and on `main`** (2026-10-15): chezmoi source root is now `home/`; docs, `tools/`, `CLAUDE.md`, `.envrc` and `.ripgreprc` stay at the repo root.
- BOCO merge **Phase 0 done** (2026-10-16): `is-wsl` helper, `work_tooling` key, systemd reload script, git/GPG/SSH config (branch `0b`, on local `main`); zsh switch-over (branch `0c-zsh`, applied and merged; snapshot in `~/.local/state/claude-migration-backups/zsh-apply/`). Details: [log/zsh-step4-inventory.md](log/zsh-step4-inventory.md), [zsh-plugins.md](zsh-plugins.md). New tools: `tools/zsh-probe/`, `tools/home-snapshot/`.
- A private doc (keys, findings, client terms) is committed in `~/Source/chezmoi-boco` but **not pushed** (waiting for MH's OK).

## Next actions (in order)
1. **GitHub Support request (MH)** to purge cached views / stale refs of the old (pre-rewrite) SHAs on `antimike/chezmoi-dotfiles`. The force-push is done; this is the last step that keeps the old client terms reachable until GitHub acts.
2. **Run a full `chezmoi apply`** to pick up the `mmdc` + `lazygit` lines added to `run_once_install_neovim_deps.sh.tmpl` after the last apply (the script re-fires on content change); and optionally delete the merged `boco-merge/2-nvim` branch.
3. **BOCO merge Phase 3 (timers and services)** ([plans/boco-merge.md](plans/boco-merge.md), "Phase 3"); needs Phase 0 (done).
4. Sway work ([plans/sway.md](plans/sway.md)); Phase 0a is done, so it can start.
5. Atlassian/Jira review pass and gitleaks hook rollout when MH schedules them.

## Blockers / watch
- `gitleaks detect --no-git` reports exactly 2 findings; they are **expected and accepted** (MH, 2026-10-15): `private_polybar-weather.service.tmpl` (generic-api-key) and `private_dot_jupyter/private_certs/private_service-key.pem` (private-key), both under `home/private_dot_config/…` and `home/private_dot_jupyter/…`. Anything beyond these two is a stop.
- The YubiKey must be plugged in for pushes, signing tags, `pass`, and the backup/sync timers.
- Atlassian/Jira items are held until a redaction pass ([plans/boco-merge.md](plans/boco-merge.md), "Held items").
- No second machine for testing the zsh switch-over; use the scratch-home method in the plan.

## Start prompt (paste when starting or restarting a session outside this directory)
> Work in `~/.local/share/chezmoi`. Read `CLAUDE.md` and `docs/STATUS.md`, then continue with "Next actions". Confirm with me before pushing, deleting remote branches, or anything outward-facing. Follow `docs/conventions.md`; the repo is public, so scan for client/employer terms and gitleaks before committing.

## At session end
Update this file (what changed, next actions, blockers), `docs/open-items.md`, and add any decision to `docs/decisions.md`. Commit docs separately.
