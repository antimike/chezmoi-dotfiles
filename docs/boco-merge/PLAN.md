# Merging the BOCO chezmoi config into this repo

Planning document for future sessions. Survey date: 2026-10-14. Work happens in this repo
(`~/.local/share/chezmoi`); the BOCO repo is a **read-only reference clone** at
`~/Source/chezmoi-boco` (source root `home/`, 256 commits, private mirror on `antimike`).
Context: `~/claude-migration-plan.md` (D13, Q11) and `BOOTSTRAP-DEBT.md`.

## Ground rules (already decided)

- This repo is **public**. Make anything employer- or client-specific generic *before* committing;
  run `gitleaks` and show the redaction diff. Material that must stay specific goes in the private
  `chezmoi-boco` repo, not here.
- Copy files, don't cherry-pick (unrelated histories, different layout: `home/X` vs `X`). One
  logical unit per commit, conventional message, trailer
  `Source: AudensAurantius/chezmoi@<sha>:home/<path>` (sha from `git -C ~/Source/chezmoi-boco log -1 -- home/<path>`).
- Work on a feature branch off `BOCO-migration` (e.g. `boco-merge/<phase>`); never run
  `chezmoi init`/`apply` against the clone. Apply only named targets, then `chezmoi status`.
- Don't migrate client-project material (list in `~/claude-migration-plan.md`, D3). Chezmoi ignores source mode bits: scripts invoked
  by path need an `executable_` prefix. Verify with `chezmoi archive` or `stat` after apply.
- Fedora, not Debian: package names come from `.chezmoidata/packages.yaml`; no `apt`.

## Survey (by target path)

| | BOCO | This repo |
|---|---|---|
| source files | 390 | 492 |
| only here | 202 | 304 |
| in both | 188 (95 identical, 93 differ) | |

Of the 93 that differ, 54 are `.claude/**`, reconciled in step 4 and intentionally adapted; only
spot-check them. The other 39 are listed in Phase 5. Regenerate with `compare-trees.py` (this directory).

## Phases

Order matters: Phase 0 unblocks the timers in later phases.

### Phase 0: prerequisites
- **Port `run_onchange_after_reload-systemd-user.sh.tmpl`** (reloads and enables timers on change;
  documented in `dot_claude/references/chezmoi-systemd-timers.md` as "not yet ported"). Known gap
  to fix while porting: it never disables removed timers.
- **Decide `~/.gitconfig`**, which is currently *unmanaged* here but managed in BOCO
  (`dot_gitconfig.tmpl`). Merge the two by hand, with the current signing key
  `9F049F34…` (the old one expired); consume `.gpg.keys.signing` from `.chezmoi.yml.tmpl`.
  Same for `~/.gnupg/gpg-agent.conf` (here: `enable-ssh-support`; `gpg.conf` `default-key` also unmanaged)
  and `~/.ssh/config` (BOCO maps hosts to key files; port personal hosts only, never client or employer hosts).
- **Name clash:** completions live in `dot_local/share/zsh/completion` here but `completions` in
  BOCO. Keep ours; map BOCO files into it. Check how `local.plugin.zsh` finds the directory.
- **zsh framework lineage:** `.chezmoitemplates/zsh` here has more pieces (`exports.d`, `ensure_resource`,
  `set_options.zsh`, `profile.zsh`, `widgets`) than BOCO. Work out which side is newer
  before merging any zsh file in Phase 5.

### Phase 1: low-risk, self-contained tools (copy, adapt installers)
Each is a `.chezmoidata/<tool>.yaml` + `run_onchange_install-<tool>.sh.tmpl` (+ completion/snippet).
Check the pinned release is >=14 days old and has a Linux x86_64 asset; use exact versions.
- `fzf` (data, installer, `.bashrc.d/fzf-*`, `snippets/fzf-*`, `plugins.d/0015.fzf.yaml`)
- `cheat`, `cht-sh` (+ `~/.local/bin/cht`), `the-way` (+ widgets/snippet), `nb`, `dnote`, `dstask`, `d2`
- Small helpers: `.local/bin/{tutor,claude-init,etckeeper-secret-audit}`, `.local/share/zsh/functions/{bd,docstring}`, `snippets/{pass,dotnet}.zsh`, `.bash_aliases`, `.bash_env`, `.zprofile`
- zsh completions (~30 files in `.local/share/zsh/completions`): don't copy generated ones
  (`_mise`, `_pdm`, `_chezmoi`, `_python_argcomplete*`, `_poetry`, `_bun`); regenerate or let tools provide them.

### Phase 2: Neovim
BOCO has ~35 plugin specs (themes, `molten`, `quarto`, `jupyter`, `vimtex`, `harpoon`, `dap`, `neotest`,
`claude`, ...) that this repo lacks; both sides have a LazyVim base. Differing files: `init.lua`,
`config/{autocmds,keymaps,lazy,options}.lua`, `plugins/{chezmoi,example,formatting,treesitter}.lua`.
Needs MH's call on which themes to keep. Port `run_once_install_neovim_deps` (adapt for Fedora).
Skip `*.bak` files and `mason.lua` unless still needed. Lockfile: this repo tracks `lazyvim-lock.json`.

### Phase 3: timers and background services (needs Phase 0)
`sync-repos` (script + timer + `.chezmoitemplates/sync-repos-list`; reconcile with the `mani`/`ghq`
plan in `BOOTSTRAP-DEBT.md`; the repo list must be generic here), `dstask-notify`. Use the `notify` adapter.
Not ported on purpose: `timew-*` (obsolete with bd-track), `claude-mem-cleanup` (claude-mem held).

### Phase 4: mail stack (largest design question)
neomutt (15 files), `mbsync`, `msmtp`, `procmail`, `mailcap`, notmuch, `graph-send-mail`. Contains
several accounts (personal, university, work). Decide first which accounts you still use; work
accounts are out of scope. Credentials must come from `pass`. Template one account per file so
accounts can be dropped cleanly. Verify end to end with a real sync before committing.

### Phase 5: reconcile the 39 shared-but-different non-Claude files
Direction is per file; BOCO is older in some, newer in others.
- Shell: `.bashrc` (BOCO is much larger), `.profile`, `.zshenv`, `.zshrc`, `.vimrc`, `direnv/direnvrc`, `kitty.conf`
- zsh templates (9) and `snippets/{direnv,mise,npm}.zsh`, `functions/pyproj` (**keep ours**: finished version)
- Data: `.chezmoi.yml`, `.chezmoiexternal.toml`, `.chezmoidata/{beads,beads_viewer,dolt,packages,zsh}.yaml`
  (the installers/packages were already adapted in step 6; expect to keep ours)
- `.local/bin/reminder` (already adapted)

### Phase 6: decide, probably leave behind
- **WSL-only (drop):** `.wslconfig`, `.config/etc/{wsl,resolv}.conf`, the `*.exe` shims, `wsl-notify-send`, `winpath`,
  `getwinip`, `getlocalhost`, `sync-nfs`, `.local/PowerShell/*`, `symlink-wayland-socket.service`,
  `install-burnttoast`, `check-wsl-lso`, `apply-wslconfig`, `apply-etc-config`.
- **Employer-specific:** the namespaced-VPN stack (`vpn-*`, `dual-vpn`, `namespaced-openvpn` data and installer,
  `install-vpn-symlinks`); `rano` (an employer AI-governance PoC; data, installer, report, timers);
  Atlassian data/template/`jira-comment-drafter` and `.config/.jira` (kept in private `chezmoi-boco`).
- **Held or dropped earlier:** `claude-mem-*`, `fewer-permission-prompts`, `time-report`, `auto-session/.transcripts`.
Ask MH before porting any of these; the default is to leave them in `chezmoi-boco`.

## Per-phase checklist

1. `compare-trees.py` shows the files moved from only-BOCO to both.
2. `chezmoi diff` on the new targets is understood; apply only those targets; `chezmoi status` clean.
3. `gitleaks detect --no-git -s .` shows only the two known findings (polybar-weather key, Jupyter key).
4. Grep the changed files for employer/client terms (patterns in `~/claude-migration-plan.md`, D3, and the old hostname/user); expect nothing.
5. Tick the item in `BOOTSTRAP-DEBT.md` if it removes a hand-installed tool; push the branch.

## Decisions needed from MH before Phase 2 and Phase 4

1. Neovim: keep all BOCO themes/plugins, or a curated subset?
2. Mail: which accounts survive, and is `graph-send-mail` (Microsoft Graph) still needed?
3. Is the BOCO `.bashrc` still wanted (zsh is primary here)?
4. `sync-repos`: keep the BOCO design, or replace with `mani`/`git for-each-repo`?
