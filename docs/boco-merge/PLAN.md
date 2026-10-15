# Merging the BOCO chezmoi config into this repo

Planning document for future sessions. Survey date: 2026-10-14; decisions recorded the same day.
Work happens in this repo (`~/.local/share/chezmoi`); the BOCO repo is a **read-only reference
clone** at `~/Source/chezmoi-boco` (source root `home/`, 256 commits, private mirror on `antimike`).
Context: `~/claude-migration-plan.md` (D13, Q11) and `BOOTSTRAP-DEBT.md`.

## Decisions (MH, 2026-10-14)

1. **BOCO is authoritative for tool-specific config**: Neovim (keep *all* themes and plugins), zsh
   (the BOCO configuration system is more current and is the target state), `.bashrc`, and any other
   per-tool config. Where a file differs, BOCO wins unless it is on the keep-ours list below.
2. **Keep everything MH built at BOCO**, even if unused on this machine: the repo exists for
   cross-machine management. Machine-specific items are *guarded*, not dropped (see Guards).
3. **WSL-specific items are copied over**, template-guarded to install only on WSL hosts, for a future
   work laptop.
4. Mail accounts in use: the personal and the professional Gmail accounts. BOCO's mail files
   contain only personal-domain accounts (`professional`, `csu`, `personal`), so port them whole.
5. `sync-repos`: keep BOCO's script as the engine; add `mani` for interactive status (see Phase 3).

### Keep-ours list (BOCO does not win here)
Files already adapted for Fedora or fixed on this machine; re-diff but do not overwrite:
- everything under `.claude/**` (step 4), `.local/bin/reminder` and the `notify` adapter
- `.chezmoidata/{packages,beads,beads_viewer,dolt}.yaml`, installers (`run_onchange_install-*`) (Fedora, exact pins)
- `.chezmoi.yml.tmpl` (merge by hand: it carries `notifier`, `enable_user_lingering`, the new signing key)
- `snippets/mise.zsh`, `snippets/direnv.zsh`, `functions/pyproj` (finished versions), `create_okularrc`
- The 2 known gitleaks findings stay out: never copy the old ***REMOVED*** key (in BOCO history)

## Ground rules

- This repo is **public**. Employer- or client-specific *data* must be made generic or kept private
  (see "Employer-specific content"). Run `gitleaks` and show MH the redaction diff before committing.
- Copy files, don't cherry-pick (unrelated histories; `home/X` vs `X`). One logical unit per commit,
  conventional message, trailer `Source: AudensAurantius/chezmoi@<sha>:home/<path>`
  (`git -C ~/Source/chezmoi-boco log -1 --format=%h -- home/<path>`).
- Feature branch off `BOCO-migration` per phase (`boco-merge/<phase>`). Never `chezmoi init/apply`
  against the clone. Apply named targets only, then `chezmoi status`.
- Chezmoi ignores source mode bits: scripts invoked by path need `executable_`. Verify after apply.
- Fedora, not Debian: take package names from `.chezmoidata/packages.yaml`.

## Guards (how BOCO-only things stay inert elsewhere)

- **WSL:** add `is_wsl` to `.chezmoi.yml.tmpl` (same test the `notifier` logic already uses:
  `.chezmoi.kernel.osrelease | lower | contains "wsl"`), and list WSL-only targets in
  `.chezmoidata/wsl.yaml`. In `.chezmoiignore`, `{{ if not .is_wsl }}` ignore that list (works for plain
  files like the `*.exe` shims and for `run_` scripts; **verify with `chezmoi managed` on this host**).
  Use a `.tmpl` + `{{ if .is_wsl }}` body only where a file must render conditionally.
- **Employer-specific tooling** (VPN stack, `rano`, Atlassian/Jira): same mechanism with a `work_tooling`
  data flag, default false here.
- **Tool present:** keep the existing `lookPath` guards on units and scripts.
- Acceptance: on this host, `chezmoi managed | grep -iE 'wsl|\.exe|vpn'` is empty and `chezmoi diff` is quiet
  for guarded items. Add a dry-run render with `--override-data` (`is_wsl: true`) to prove the WSL side still renders.

## Employer-specific content (needs MH's attention)

"Keep everything" collides with "public repo" in one place: content that identifies the employer's
systems or other people. Tooling *code* is fine once generic. Keep the following private
(default: leave in `antimike/chezmoi-boco`; or add a private data layer, e.g. a second source via
`.chezmoiexternal` from a private repo): Atlassian data/template and `jira-comment-drafter` (colleague
names, emails, account IDs); employer hostnames, VPN profiles and tenant IDs; the work gitconfig identity;
`rano` internals if they reference employer systems. Check each file when porting.

## Survey (by target path)

| | BOCO | This repo |
|---|---|---|
| source files | 390 | 492 |
| only here | 202 | 304 |
| in both | 188 (95 identical, 93 differ) | |

54 of the 93 differing files are `.claude/**` (reconciled in step 4). 39 others are in Phase 5.
Regenerate with `compare-trees.py` (this directory).

## Phases

Order matters: Phase 0 unblocks the timers.

### Phase 0: prerequisites
- Port `run_onchange_after_reload-systemd-user.sh.tmpl` (documented as missing in
  `dot_claude/references/chezmoi-systemd-timers.md`). Fix its known gap: removed timers are never disabled.
- Add `is_wsl`, `work_tooling`, `.chezmoidata/wsl.yaml` and the `.chezmoiignore` block (Guards).
- **zsh switch-over (high regression risk).** BOCO's `.chezmoitemplates/zsh` and `.local/share/zsh`
  become the base. This repo has extra pieces BOCO lacks (`exports.d`, `ensure_resource`,
  `set_options.zsh`, `profile.zsh`, `widgets`, the `completion` dir name). Before replacing: record
  what each does and who sources it; after: re-add any piece still used, rename `completion` to
  `completions` (or the reverse) consistently, and test with `zsh -i -c exit` (no errors, startup time)
  and a diff of `env` before/after. Keep a rollback copy of the live `~/.zshrc`/`~/.zshenv`/`~/.zprofile`.
- **Git/GPG/SSH config.** `~/.gitconfig` is unmanaged here and managed in BOCO (`dot_gitconfig.tmpl`):
  merge by hand with signing key `9F049F34…` and *this* identity, work identity guarded by `work_tooling`. Same for
  `gpg-agent.conf` (here: `enable-ssh-support`; `gpg.conf` `default-key` is also unmanaged) and `~/.ssh/config`
  (private host entries only; keys never enter the repo).

### Phase 1: self-contained tools (BOCO versions authoritative; Fedora installers)
Each is `.chezmoidata/<tool>.yaml` + `run_onchange_install-<tool>.sh.tmpl` (+ completion/snippet).
Pins must be exact, >=14 days old, with a Linux x86_64 asset.
- `fzf` (+ `.bashrc.d/fzf-*`, `snippets/fzf-*`, `plugins.d/0015.fzf.yaml`), `cheat`, `cht-sh` (+ `cht`), `the-way`
  (+ widgets/snippet), `nb`, `dnote`, `dstask`, `d2`
- Helpers: `tutor`, `claude-init`, `etckeeper-secret-audit`, `functions/{bd,docstring}`, `snippets/{pass,dotnet}.zsh`,
  `.bash_aliases`, `.bash_env`, `.zprofile`, `.bashrc`
- zsh completions: skip generated ones (`_mise`, `_pdm`, `_chezmoi`, `_python_argcomplete*`, `_poetry`, `_bun`); let tools provide them.

### Phase 2: Neovim (all BOCO plugins and themes)
Copy all ~35 plugin specs and the config files that differ (`init.lua`, `config/*.lua`, `plugins/{chezmoi,example,
formatting,treesitter}.lua`). BOCO wins; reconcile the lockfile (`lazyvim-lock.json` here vs `lazy-lock.json`) by
running `:Lazy restore`/`sync` on a clean profile. Skip `*.bak`. `mason.lua` is WSL-flavoured: check, guard if so.
Port `run_once_install_neovim_deps` for Fedora.

### Phase 3: timers and services (needs Phase 0)
- **`sync-repos`**: BOCO's script is an auto-commit + push engine for dirty working trees; neither `mani`
  nor `git for-each-repo` does that (they run a command per repo), so **keep the script, don't replace it**.
  Port script/timer/`sync-repos-list` (host-aware list, generic paths). Two improvements: a gitleaks gate before
  auto-commit (as in `claude-state-sync`), and a `dirty/ahead/behind` summary.
  Add `mani` for interactive use: a templated `mani.yaml` generated from the same list, giving
  `mani run status --all` ("what needs pushing?"). Use `git for-each-repo` only for read-only maintenance
  (e.g. `git for-each-repo --config=maintenance.repo fetch`).
- Also: `dstask-notify` (use the `notify` adapter), `rano` units (guarded `work_tooling`).
- Not ported (superseded by bd-track): `timew-autostop`, `timew-nudge`. `claude-mem-cleanup` stays held with claude-mem.

### Phase 4: mail stack (all of it)
neomutt (15 files), `mbsync`, `msmtp`, `procmail`, `mailcap`, notmuch, `graph-send-mail`. Accounts: `professional` and
`personal` (active), `csu` (university; keep, mark inactive in data). Template one block per account from
`.chezmoidata/mail.yaml` so accounts toggle cleanly. Credentials only via `pass`. Verify with a real sync before committing;
keep message data out of the repo.

### Phase 5: reconcile the 39 differing non-Claude files (BOCO wins unless on keep-ours)
- Shell: `.bashrc`, `.profile`, `.zshenv`, `.zshrc`, `.vimrc`, `direnv/direnvrc`, `kitty.conf` (guard WSL-only lines)
- zsh templates (9) and `snippets/npm.zsh` (done together with the Phase 0 switch-over)
- Data: `.chezmoiexternal.toml` (merge), `.chezmoidata/zsh.yaml`, `.chezmoi.yml` (hand-merge)

### Phase 6: WSL and employer-specific items (copy, guarded)
- **WSL (`is_wsl`):** `.wslconfig`, `.config/etc/{wsl,resolv}.conf`, the `*.exe` shims, `wsl-notify-send`, `winpath`,
  `getwinip`, `getlocalhost`, `sync-nfs`, `.local/PowerShell/*`, `symlink-wayland-socket.service`, `install-burnttoast`,
  `check-wsl-lso`, `apply-wslconfig`, `apply-etc-config`, `install-wslu-repo` equivalents.
- **Employer tooling (`work_tooling`):** namespaced-VPN stack (`vpn-*`, `dual-vpn`, `namespaced-openvpn`,
  `install-vpn-symlinks`), `rano`, and (private only) Atlassian/Jira. Apply "Employer-specific content" first.
- Still excluded: client-project material (list in `~/claude-migration-plan.md`, D3), `claude-mem-*`,
  `time-report`, `fewer-permission-prompts`, `auto-session/.transcripts`.

## Per-phase checklist

1. `compare-trees.py` shows the files moved from only-BOCO to both.
2. `chezmoi diff` on the new targets is understood; apply those targets only; `chezmoi status` clean.
3. Guards hold: nothing WSL- or work-only is managed on this host (see Guards acceptance).
4. `gitleaks detect --no-git --no-banner -s .` shows only the two known findings (polybar-weather key, Jupyter key).
5. Grep changed files for employer/client terms (patterns: D3 in `~/claude-migration-plan.md`); expect nothing.
6. Tick `BOOTSTRAP-DEBT.md` if a hand-installed tool is now managed; push the branch.

## Open questions

1. How to hold employer-specific data: leave in private `chezmoi-boco`, or a private data layer? (See above.)
2. Is `csu` mail still wanted active, or inactive-but-kept?
3. zsh rollback plan: any machine other than this one to test the switch-over on first?
