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
- BOCO merge **Phase 1 (self-contained tools) done and on `main`** (force-pushed 2026-10-17). Before the push the whole history was rewritten with `git filter-repo` to purge client-term hits: bundle backup at `~/.local/state/claude-migration-backups/chezmoi-prerewrite-20261016-233103.bundle`, 7 okular/vifminfo path spellings dropped, the `client-terms.md` pattern scrubbed from all blobs and 5 commit messages, verified 0 hits across all 246 commits and the branch tip tree byte-identical to the pre-rewrite tip, origin re-added, 5 in-repo doc SHAs remapped from the commit-map. Every old commit SHA changed. **Outstanding (MH):** the GitHub Support request to purge GitHub's cached commit views of the old SHAs — until then the old terms stay viewable at `github.com/.../commit/<old-sha>` URLs.
- `@docs/STATUS.md` import in `CLAUDE.md` verified working (2026-10-15): STATUS.md is in context at session start without a Read.
- BOCO merge **Phase 0a done and on `main`** (2026-10-15): chezmoi source root is now `home/`; docs, `tools/`, `CLAUDE.md`, `.envrc` and `.ripgreprc` stay at the repo root.
- BOCO merge **Phase 0 done** (2026-10-16): `is-wsl` helper, `work_tooling` key, systemd reload script, git/GPG/SSH config (branch `0b`, on local `main`); zsh switch-over (branch `0c-zsh`, applied and merged; snapshot in `~/.local/state/claude-migration-backups/zsh-apply/`). Details: [log/zsh-step4-inventory.md](log/zsh-step4-inventory.md), [zsh-plugins.md](zsh-plugins.md). New tools: `tools/zsh-probe/`, `tools/home-snapshot/`.
- A private doc (keys, findings, client terms) is committed in `~/Source/chezmoi-boco` but **not pushed** (waiting for MH's OK).

## Next actions (in order)
1. **GitHub Support request (MH)** to purge cached views / stale refs of the old (pre-rewrite) SHAs on `antimike/chezmoi-dotfiles`. The force-push is done; this is the last step that keeps the old client terms reachable until GitHub acts.
2. **BOCO merge Phase 2 (Neovim)** on a new branch `boco-merge/2-nvim` ([plans/boco-merge.md](plans/boco-merge.md), "Phase 2"). Copy all ~35 BOCO plugin specs + the differing config files (`init.lua`, `config/*.lua`, `plugins/{chezmoi,example,formatting,treesitter}.lua`); BOCO wins; reconcile the lockfile (`lazyvim-lock.json` here vs `lazy-lock.json`) via `:Lazy restore`/`sync` on a clean profile; skip `*.bak`; check `mason.lua` for WSL flavour and guard if so; port `run_once_install_neovim_deps` for Fedora. Then Phases 3–6.
3. Sway work ([plans/sway.md](plans/sway.md)); Phase 0a is done, so it can start.
4. Atlassian/Jira review pass and gitleaks hook rollout when MH schedules them.

## Blockers / watch
- `gitleaks detect --no-git` reports exactly 2 findings; they are **expected and accepted** (MH, 2026-10-15): `private_polybar-weather.service.tmpl` (generic-api-key) and `private_dot_jupyter/private_certs/private_service-key.pem` (private-key), both under `home/private_dot_config/…` and `home/private_dot_jupyter/…`. Anything beyond these two is a stop.
- The YubiKey must be plugged in for pushes, signing tags, `pass`, and the backup/sync timers.
- Atlassian/Jira items are held until a redaction pass ([plans/boco-merge.md](plans/boco-merge.md), "Held items").
- No second machine for testing the zsh switch-over; use the scratch-home method in the plan.

## Start prompt (paste when starting or restarting a session outside this directory)
> Work in `~/.local/share/chezmoi`. Read `CLAUDE.md` and `docs/STATUS.md`, then continue with "Next actions". Confirm with me before pushing, deleting remote branches, or anything outward-facing. Follow `docs/conventions.md`; the repo is public, so scan for client/employer terms and gitleaks before committing.

## At session end
Update this file (what changed, next actions, blockers), `docs/open-items.md`, and add any decision to `docs/decisions.md`. Commit docs separately.
