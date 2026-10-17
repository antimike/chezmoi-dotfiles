---
summary: Phased plan to merge the employer-era (BOCO) chezmoi repo into this one: decisions, guards, phases, checklists
status: Phases 0-2 done and on main (Phase 2 merged + pushed 2026-10-17, merge fbc8169); Phase 3 timers merged 2026-10-17; gitleaks hook rollout in progress on boco-merge/3-hooks
updated: 2026-10-17
---

# Merging the BOCO chezmoi config into this repo

Planning document for future sessions. Survey date: 2026-10-14; decisions recorded the same day.
Work happens in this repo (`~/.local/share/chezmoi`; after Phase 0a its source root is `home/`); the BOCO repo is a **read-only reference
clone** at `~/Source/chezmoi-boco` (source root `home/`, 256 commits, private mirror on `antimike`).
Context: [../decisions.md](../decisions.md) (D13, D24–D28), [../bootstrap-debt.md](../bootstrap-debt.md), [../conventions.md](../conventions.md).

## Decisions (MH, 2026-10-14)

1. **BOCO is authoritative for tool-specific config**: Neovim (keep *all* themes and plugins), zsh
   (the BOCO configuration system is more current and is the target state), `.bashrc`, and any other
   per-tool config. Where a file differs, BOCO wins unless it is on the keep-ours list below.
2. **Keep everything MH built at BOCO**, even if unused on this machine: the repo exists for
   cross-machine management. Machine-specific items are *guarded*, not dropped (see Guards).
3. **WSL-specific items are copied over**, template-guarded to install only on WSL hosts, for a future
   work laptop.
4. Mail accounts in use: the personal and the professional Gmail accounts. BOCO's mail files contain no employer
   account (`professional`, `csu`, `personal`). **The CSU account is dropped** (access lost): omit its
   `mbsync`/`msmtp`/`neomutt` blocks and the CSU signature and template files; port the rest whole.
5. **Adopt BOCO's `.chezmoiroot = home` layout** here (Phase 0a).
6. **WSL guards are inline template logic** checking the OS directly, not a data flag plus `.chezmoiignore`
   (see Guards). `work_tooling` stays as a data flag, default false.
7. **Atlassian data and the Jira agent are held back** pending a review and redaction pass (see Held items).
8. **Secret scanning is done by gitleaks pre-commit hooks in each repo that needs it**, not inside
   `sync-repos` (Phase 3).
9. `sync-repos` itself is low priority: its only BOCO use-case (a timewarrior data repo) is obsolete (Phase 3).

### Keep-ours list (BOCO does not win here)
Files already adapted for Fedora or fixed on this machine; re-diff but do not overwrite:
- everything under `.claude/**` (step 4), `.local/bin/reminder` and the `notify` adapter
- `.chezmoidata/{packages,beads,beads_viewer,dolt}.yaml`, installers (`run_onchange_install-*`) (Fedora, exact pins)
- `.chezmoi.yml.tmpl` (merge by hand: it carries `notifier`, `enable_user_lingering`, the new signing key)
- `snippets/mise.zsh`, `snippets/direnv.zsh`, `functions/pyproj` (finished versions), `create_okularrc`
- Never copy credentials from the reference clone's history; gitleaks gates every commit (known findings: see the private doc)

## Ground rules

- This repo is **public**. Employer- or client-specific *data* must be made generic or kept private
  (see "Employer-specific content"). Run `gitleaks` and show MH the redaction diff before committing.
- Copy files, don't cherry-pick (unrelated histories; `home/X` vs `X`). One logical unit per commit,
  conventional message, trailer `Source: AudensAurantius/chezmoi@<sha>:home/<path>`
  (`git -C ~/Source/chezmoi-boco log -1 --format=%h -- home/<path>`; private-only commits use
  `antimike/chezmoi-boco@<sha>`, see `conventions.md`).
- Feature branch off `main` per phase (`boco-merge/<phase>`). Never `chezmoi init/apply`
  against the clone. Apply named targets only, then `chezmoi status`.
- Chezmoi ignores source mode bits: scripts invoked by path need `executable_`. Verify after apply.
- Fedora, not Debian: take package names from `.chezmoidata/packages.yaml`.

## Guards (how BOCO-only things stay inert elsewhere)

- **WSL:** wrap WSL-specific files in template logic that tests the OS directly. Rename the source file to
  `*.tmpl` and put the body inside the guard. A file that renders empty is not managed, and the same
  holds for `run_` scripts. This is what the repo already does for tool presence (`lookPath`). Use one shared
  helper so the test is written once: `.chezmoitemplates/is-wsl` emitting `true`/`false` from
  `.chezmoi.kernel.osrelease | lower | contains "wsl"` (the test `notifier` already uses), used as
  `{{ if eq (includeTemplate "is-wsl" .) "true" -}} ... {{- end }}`.
  Costs to watch: files that are copied verbatim must be renamed to `.tmpl` (record that in the provenance
  trailer), and a directory whose files all render empty may still be created, so check
  `chezmoi managed` for stray empty dirs.
- **Employer-specific tooling** (VPN stack, `rano`): same inline guard on `.work_tooling`, a data key in
  `.chezmoi.yml.tmpl`, default false here, true on a future work laptop.
- **Tool present:** keep the existing `lookPath` guards on units and scripts.
- Acceptance (corrected 2026-10-17, Phase 3): `chezmoi managed` **does list** templates that render empty (it lists
  source entries, not rendered output), so it cannot prove a guard. Check what would be written instead: guarded targets
  must be absent from `chezmoi status` and `chezmoi apply --dry-run --verbose <targets>` must print nothing for them.
  The original check, kept for reference: on this host, `chezmoi managed | grep -iE '(^|/)(\.?wsl[^/]*|[^/]*\.exe|vpn-[^/]*|dual-vpn|namespaced-openvpn|install-vpn-symlinks|rano[^/]*|winpath|getwinip|getlocalhost|sync-nfs)(/|$)'` is empty (anchored on path components; the earlier loose `vpn` pattern matched the personal `.config/protonvpn`) and `chezmoi diff` is quiet
  for guarded items. Prove the other side by rendering one guarded file with
  `chezmoi execute-template --override-data '{"chezmoi":{"kernel":{"osrelease":"x-microsoft-wsl2"}}}'`
  (or on a WSL host); the body must appear.

## Employer-specific content (needs MH's attention)

"Keep everything" collides with "public repo" in one place: content that identifies the employer's
systems or other people. Tooling *code* is fine once generic. Check each file when porting for:
employer hostnames, VPN profiles and tenant IDs, the work gitconfig identity, and `rano` internals that
reference employer systems. Anything that cannot be made generic stays in private `antimike/chezmoi-boco`.

### Held items (do not port until MH has reviewed and approved a redaction pass)
- `.chezmoidata/atlassian.yaml`, `.chezmoitemplates/atlassian-boco-context`, the `jira-comment-drafter` agent,
  and `.config/.jira/.config.yml`: they contain colleague names, emails and account IDs and employer tenant details.
- Procedure when MH schedules it: read each file with MH, list every identifying value, replace with data keys or
  placeholders, show the redaction diff, run gitleaks and the employer-term grep, and only then commit.
  The Jira skills and commands already imported are dormant and generic; they stay as they are.

## Survey (by target path)

| | BOCO | This repo |
|---|---|---|
| source files | 390 | 492 |
| only here | 202 | 304 |
| in both | 188 (95 identical, 93 differ) | |

54 of the 93 differing files are `.claude/**` (reconciled in step 4). 39 others are in Phase 5.
Regenerate with [../../tools/compare-trees.py](../../tools/compare-trees.py).

## Phases

Order matters: Phase 0 unblocks the timers.

### Phase 0: prerequisites

**0a. Restructure to the `home/` layout. DONE 2026-10-15 on `boco-merge/0a-home-layout` (4 commits: `.chezmoiroot`, pure renames, `.chezmoiignore` cleanup, path fix-up).**
Verified empirically: with `.chezmoiroot = home`, `.chezmoi.sourceDir` is `<repo>/home` and
`.chezmoi.workingTree` is `<repo>`, so every `joinPath .chezmoi.sourceDir ...` keeps working *if the file it
points at moves into `home/`*. After this, BOCO paths map 1:1 (`home/X` to `home/X`), which also makes
provenance trailers and diffs trivial.
- Branches: nothing to settle (checked 2026-10-15: `main` is the only branch, local and remote; see D26). Each phase
  gets its own `boco-merge/<phase>` branch off `main`, merged back (fast-forward or merge commit) when its checklist
  passes. Stop other work in the repo during the rename.
- Gotchas found in 0a: `chezmoi diff` is not byte-identical after the move. Two targets embed `sourceDir`
  (the nvim `lazy-lock.json` symlink and the `funk` function); `chezmoi apply --force` those two. The live
  `~/.claude.json` hunk (trailing newline from the `modify_` script) is baseline drift, not a regression.
  `chezmoi doctor` output differs only in the `~/.local/share/chezmoi/home/` path text.
- Add `.chezmoiroot` (content `home`) at the repo root. `git mv` every source entry into `home/`
  (including `.chezmoidata`, `.chezmoitemplates`, `.chezmoiignore`, `.chezmoiexternal.toml.tmpl`,
  `.chezmoi.yml.tmpl`, `bin/`, `lazyvim-lock.json`). Stay at the root: `.git*`, `.envrc`, `.ripgreprc`, `tools/` (added 2026-10-16),
  `docs/`, `CLAUDE.md`, `.chezmoiroot`. (`.chezmoiignore` entries for root-only files
  are then unnecessary: files outside `home/` are not managed at all.)
- Commit the pure renames separately (no content changes) so `git log --follow` works.
- Fix-up commit: re-insert `home/` into the ~40 hard-coded source paths of the form
  `~/.local/share/chezmoi/dot_*` (undoing the step 4.7 stripping) in the `/add-*`, `/edit-*`, `/remove-*`
  commands, `trim-claude-config`, `auto-session`, `CLAUDE.md`, `chezmoi-systemd-timers.md`, unit `Documentation=`
  lines, `beads-cheatsheet.md`; and `.chezmoi.yml.tmpl`'s `stat` of `dot_local/bin/...` (works unchanged, as
  `sourceDir` includes `home`). The nvim `lazy-lock.json` symlink target uses `sourceDir/lazyvim-lock.json`: it must live in `home/`.
- Check: `chezmoi init` (regenerates config), then `chezmoi diff` is **identical to before** (record it before
  starting: `chezmoi diff > /tmp/pre.diff`), `chezmoi managed | wc -l` unchanged, `chezmoi doctor` has no new errors.
  The worktree workflow in `dot_claude/CLAUDE.md` (`--source ~/Source/chezmoi-features`) needs `--source <worktree>/home`.

- Port `run_onchange_after_reload-systemd-user.sh.tmpl` (documented as missing in
  `dot_claude/references/chezmoi-systemd-timers.md`). Fix its known gap: removed timers are never disabled.
- Add the `is-wsl` helper template and the `work_tooling` data key (Guards).
- **zsh switch-over (high regression risk).** BOCO's `.chezmoitemplates/zsh` and `.local/share/zsh`
  become the base. This repo has extra pieces BOCO lacks (`exports.d`, `ensure_resource`,
  `set_options.zsh`, `profile.zsh`, `widgets`, the `completion` dir name). Before replacing: record
  what each does and who sources it; after: re-add any piece still used, rename `completion` to
  `completions` (or the reverse) consistently, and test with `zsh -i -c exit` (no errors, startup time)
  and a diff of `env` before/after. Keep a rollback copy of the live `~/.zshrc`/`~/.zshenv`/`~/.zprofile`.
  Fallbacks: a plain `bash` terminal works for most failures (errors in `.zshrc`). It does not help when zsh
  hangs or `exec`s away at startup, or when a broken `.zshenv` breaks tools that spawn `zsh -c` (including
  Claude Code's own shell), so the scratch-home test below is still worth the few minutes.
  **No second machine needed:** render into a scratch home first (`chezmoi apply --destination "$S" --source ...`
  with `--config` pointing at a copy of the config), then run `HOME="$S" ZDOTDIR="$S" zsh -i -c exit` and exercise a few
  functions/widgets there, and only then apply to the real `$HOME`. Do the real apply from a shell that stays open
  (`bash`/`zsh -f` as the fallback), keep a terminal session open while you open a new one to test, and
  `chsh` stays untouched. Optional clean-room: a Fedora container (`podman run -it fedora zsh`) with the repo bind-mounted.
  **Step 4 decisions (MH, 2026-10-16)** and findings: [../log/zsh-step4-inventory.md](../log/zsh-step4-inventory.md).
  Goal: replicate the BOCO *rendered* config here, and note ways to simplify how it is configured. BOCO is not a drop-in
  (data-schema mismatch, undefined `filesystem.tmpDir`, Debian-only `bat` alias, hard-coded foreign home path), and
  the keep-list includes the `SSH_AUTH_SOCK` + `gpgconf --launch gpg-agent` lines in `zshenv` (YubiKey SSH auth).
  Removed: `asdf` plugin, `voidmobile` block, `profile.zsh`, `0115.fzf.yaml` (BOCO's `fzf` files arrive in Phase 1; fzf is
  unused meanwhile). Widgets `command-prefixes.zsh` and `twf.zsh` are parked in `docs/parked/zsh-widgets/`, not loaded.
  Sequence on branch `boco-merge/0c-zsh` (status 2026-10-16: steps 1-6 done and committed, the real apply not yet): (1) inventory and baseline (done); (2) `completion` to `completions` rename;
  (3) data and templates; (4) `zshenv`; (5) `zshrc`; (6) cleanup commit (removals above); (7) DONE 2026-10-16: the scratch-home harness is `tools/zsh-probe/` at the repo root (MH; not `docs/tools/`), in its own commit: no hard-coded paths (repo root via `git rev-parse`, scratch dir under `${XDG_CACHE_HOME:-~/.cache}/zsh-probe`), a `--baseline <git-rev>` option that builds the temporary worktree, `drive.py` conformed to the python-scripting conventions, and a README with the lessons (a pty is required for turbo plugins, a clean `env -i` environment, wait for the zinit scheduler queue, normalise random ids); update the root-layout notes in `CLAUDE.md` and `docs/README.md`, `compare-trees.py` is already there; (8) docs. Each commit is rendered
  and tested in a scratch home first; the pass criterion is the baseline's stderr (not empty: p10k gitstatus prints
  errors without a TTY), startup within about 20% of 0.145 s, and intended-only diffs of `env`, `alias`, `fpath`, `options`
  and `bindkey -L`. Apply `zshrc` first and `zshenv` last, with a rollback script that runs under `env -i bash --noprofile --norc`.
- **Keybinding manifest (after Step 4, separate item; D33 draft).** One YAML manifest of keybinds, generalising BOCO's
  `.chezmoidata/fzf.yaml :: fzf.keybindings` (`key`, `keymaps`, `widget`, plus an `unbind` action). It renders to a
  single snippet that loads **after** every plugin (including `wait`ed ones, via `atload` or a one-shot first-prompt
  hook), so the manifest wins by construction. Render-time check: fail on a duplicate `(keymap, key)` pair. Runtime audit
  script: starts `zsh -ic` with a `bindkey` wrapper that logs keymap, key, widget and caller (`$funcfiletrace`), then reports
  (a) manifest entries overridden later, (b) entries whose widget is undefined (`zle -la`), (c) unclaimed bindings that differ
  from a bare `zsh -f` `bindkey -L` baseline (plugin-added binds, with source). Caveats: one key has several encodings
  (`^[OA` vs `^[[A`, terminfo names), so compare using zsh's canonical `bindkey -L`; `builtin bindkey` bypasses the wrapper.
  Step 4 seeds it by capturing the `bindkey -L` baseline and diffing it after the render.
- **Git/GPG/SSH config.** `~/.gitconfig` is unmanaged here and managed in BOCO (`dot_gitconfig.tmpl`):
  merge by hand with signing key `9F049F34…` and *this* identity, work identity guarded by `work_tooling`. Same for
  `gpg-agent.conf` (here: `enable-ssh-support`; `gpg.conf` `default-key` is also unmanaged) and `~/.ssh/config`
  (private host entries only; keys never enter the repo).

### Phase 1: self-contained tools (BOCO versions authoritative; Fedora installers) — DONE, on `main` (force-pushed 2026-10-17 after the history rewrite; `boco-merge/1-tools` merged and deleted)
Each is `.chezmoidata/<tool>.yaml` + `run_onchange_install-<tool>.sh.tmpl` (+ completion/snippet).
Pins must be exact, >=14 days old, with a Linux x86_64 asset.
- `fzf` (zsh side done early on 2026-10-16: `snippets/fzf-*`, `plugins.d/0015.fzf.yaml`, `.chezmoidata/fzf.yaml` keybindings, `snippets/fzf-env.zsh`; DONE 2026-10-16: `run_onchange_install-fzf.sh.tmpl` pinned to v0.74.4 and `.bashrc.d/fzf-integration.bash` using `fzf --bash` instead of BOCO's vendored scripts), `cheat`, `cht-sh` (+ `cht`), `the-way`
  (+ widgets/snippet), `nb`, `dnote`, `dstask`, `d2`
- Helpers: `tutor`, `claude-init`, `etckeeper-secret-audit`, `functions/{bd,docstring}`, `snippets/{pass,dotnet}.zsh`,
  `.bash_aliases`, `.bash_env`, `.zprofile`, `.bashrc`
- zsh completions: skip generated ones (`_mise`, `_pdm`, `_chezmoi`, `_python_argcomplete*`, `_poetry`, `_bun`); let tools provide them.
  Installer-generated, decided 2026-10-16: for tools with a completion command (`cheat`, `dstask`, `the-way`) the installer writes
  `completions/_<tool>` through `.chezmoitemplates/install-completion.sh`, not a render-time `output` template (that renders empty on a
  first apply, and BOCO's `_the-way` was committed as a 0-byte file). Static `_cht`, `_nb`, `_nbterm` stay as files.
  Status 2026-10-16: `fzf`, `cheat`, `cht-sh`, `the-way` (+ widgets), `nb`, `dnote`, `dstask`, `d2`, and `clipse` (not BOCO; added 2026-10-16) done on `boco-merge/1-tools`. The helpers below are done too (2026-10-16); `functions/bd` was rewritten to call `bd-track`, and `docstring` and `.zprofile` were duplicates and are not ported.

### Phase 2: Neovim (all BOCO plugins and themes) — DONE, merged to `main` and pushed 2026-10-17 (merge `fbc8169`)
Ported all 39 BOCO plugin specs (15 themes + 19 features + the 4 shared chezmoi/example/formatting/treesitter) and the
config files, into this repo's `private_dot_config/nvim/` (note: this repo nests `.config` as `private_`; `norm()` in
`compare-trees.py` strips the prefix, so paths still match 1:1). BOCO won throughout. Outcomes and corrections to the
plan's assumptions:
- **`mason.lua` is NOT WSL-flavoured** — it is a dual-OmniSharp .NET/C# LSP setup. No WSL guard needed. It is also the
  *modern* mason pattern (`mason-org/*` + `automatic_enable`, mason-lspconfig 2.0), so it superseded this repo's old
  `mason-lspconfig.lua` (`williamboman/*` + manual `setup()`); `html`+`purescriptls` folded into its lists. OmniSharp is
  inert here (not in `ensure_installed`, `run_on_start=false`).
- **BOCO uses blink.cmp, not nvim-cmp** (see `snippets.lua`). The stale committed lock was from 2023 (LazyVim 10.8.2) and
  misled an initial nvim-cmp assumption. Supertab preserved as blink's `super-tab` keymap preset (`cmp.lua`); telescope-
  fzf-native preserved (`telescope.lua`); symbols-outline dropped (BOCO's `aerial.lua` covers it).
- **init.lua**: BOCO's == this repo's minus the Python-host preamble, so the host-prog setter consolidated into BOCO's
  templated `options.lua.tmpl` (reads new `.filesystem.venvDir`) and `init.lua.tmpl` became a plain `init.lua`.
- **Lockfile reconciled on a clean profile** against current LazyVim 16.0.1 (123 plugins; treesitter on its `main`
  branch). Validated by a headless load exercising treesitter/LSP/cmp/formatting with no config errors, via the new
  `tools/nvim-lazy-sync/` helper. The big snag was lazy.nvim's "too many rounds of missing plugins" — an *install-failure*
  loop, not a spec problem: oxocarbon's dev fennel rockspec failed to build because the system luarocks is Lua 5.4 while
  Neovim is LuaJIT/5.1. Fixed with `rocks = { enabled = true, hererocks = true }` (forcing lazy's isolated 5.1 luarocks)
  plus `hererocks` + `ImageMagick-devel` in the installer.
- **`run_once_install_neovim_deps.sh.tmpl`**: ported distro-gated (original Debian `apt-get` logic kept under `else`;
  Fedora `dnf` branch with verified names). Only the venv/pip provider step was live-tested (venv rebuilt at
  `~/.venv/neovim`); the `sudo dnf`/gem/npm steps run on the next full `chezmoi apply`. Manifest migration of its OS
  packages deferred to D32.
- `venvDir`/`npmDir` added to `.chezmoi.yml.tmpl` (absolute paths). Themes coexist: BOCO's set + this repo's
  `colorschemes.lua`/`lush` (this repo's `kanagawa.lua` dropped — colorscheme.lua defines it); active colorscheme is
  gruvbox (BOCO's `colorscheme.lua`).
- **image.nvim** enabled with a runtime guard (kitty session only, never WSL), `backend = "kitty"`, `magick_rock`
  processor; its `magick` luarock builds via lazy's native rocks (hererocks) from image.nvim's rockspec, so
  `vhyrro/luarocks.nvim` was dropped. Regenerate the lock from a kitty session so the gated image.nvim stays pinned.
Remaining (not blockers): `ruff` binary and mason LSP servers (jedi, ruff) install on demand.

### Phase 3: timers and services (needs Phase 0)
**Timers and services DONE, merged to `main` 2026-10-17 (merge `5ab6ded`).** Ported: `sync-repos` (empty list: the
timer and `~/.config/sync-repos` stay unmanaged until an entry is added; script + service installed, service run clean),
`dstask-notify` (via the `notify` adapter; also guarded on `~/.dstask` existing; fixed a UTC end-of-day bug that hid
tasks due the same evening), `rano` (installer, monitor, weekly report, all `work_tooling`-guarded; employer report
recipient moved to data key `rano.report_email`), and the reload script's long-running-services list
(`rano-monitor.service`). The reload script became `run_after_` the same day (guard flips were missed).
**Hook rollout done on `boco-merge/3-hooks` (unmerged) except `bd-track`/`claude-config` (deferred, open item).** **Next:** `sync-repos` hardening (below).
- **`sync-repos` (D28, amended by D36).** Its BOCO use-case (`~/.timewarrior`) is obsolete. Its list holds **only repos
  chezmoi itself provisions** (fixed paths, so the `sync-repos-list` template stays; no mani). Unattended commits must
  scan for secrets **inside the script**, not via a per-clone hook, which can be silently missing (`claude-config`
  and `chess_trainer` have committed configs whose hooks were never installed here). Next step: port `claude-state-sync`'s behaviour into `sync-repos` (gitleaks on
  the staged set, refuse if gitleaks is missing, `pull --rebase --autostash` before push, `notify` on failure), list
  `~/.claude/projects` as its first entry, and retire `claude-state-sync`. Deferred: one `dstask` repo provisioned by
  chezmoi (remote + run_once clone), then listed.
- **gitleaks pre-commit hooks (D35).** Hooks protect commits made by hand; each repo opts in by committing a
  `.pre-commit-config.yaml` with a `local`/`system` gitleaks hook (`gitleaks git --pre-commit --staged --redact
  --no-banner`; `protect` is deprecated in gitleaks 8.30). Roll out to the public repos (`chezmoi-dotfiles`,
  `bd-track`, `claude-config`, `chess_trainer`, `resume-builder`) and `claude-state` (config and hook already in place since
  2026-10-14; only the deprecated `protect` command changes). Install per clone with mani: a generated, unmanaged `~/mani.yaml`
  lists the clones found under a few root folders, and the managed `~/.config/mani/config.yaml` holds an
  `install-hooks` task that runs `pre-commit install` where the config has a gitleaks hook. The chezmoi repo gets a
  `.gitleaksignore` for its 2 accepted findings (D30). Existing configs in `claude-config` and `chess_trainer` bring
  their other hooks (whitespace fixers, ruff, `just-check`) into effect too. Deferred safety net: an
  `init.templateDir` hook for new clones. Conflicts: `pre-commit install` refuses if `core.hooksPath` is set (unset
  everywhere, 2026-10-17); `bd hooks install` also writes `.git/hooks/*` (none installed); pre-commit chains existing
  hooks as `.legacy`.
- Also: `dstask-notify` (use the `notify` adapter), `rano` units (guarded `work_tooling`).
- Not ported (superseded by bd-track): `timew-autostop`, `timew-nudge`. `claude-mem-cleanup` stays held with claude-mem.

### Phase 4: mail stack (all of it)
neomutt, `mbsync`, `msmtp`, `procmail`, `mailcap`, notmuch, `graph-send-mail`. Accounts: `professional` and
`personal` only; **omit `csu`** (blocks in `.mbsyncrc`/`msmtp/config`, `signatures/{.signature-csu,csu}`, any
CSU templates). Template one block per account from `.chezmoidata/mail.yaml`. Credentials only via `pass`. Verify with a real sync before committing;
keep message data out of the repo.

### Phase 5: reconcile the 39 differing non-Claude files (BOCO wins unless on keep-ours)
- Shell: `.bashrc`, `.profile`, `.zshenv`, `.zshrc`, `.vimrc`, `direnv/direnvrc`, `kitty.conf` (guard WSL-only lines)
- zsh templates (9) and `snippets/npm.zsh` (done together with the Phase 0 switch-over)
- Data: `.chezmoiexternal.toml` (merge), `.chezmoidata/zsh.yaml`, `.chezmoi.yml` (hand-merge)

### Phase 6: WSL and employer-specific items (copy, guarded)
- **WSL (inline `is-wsl` guard):** `.wslconfig`, `.config/etc/{wsl,resolv}.conf`, the `*.exe` shims, `wsl-notify-send`, `winpath`,
  `getwinip`, `getlocalhost`, `sync-nfs`, `.local/PowerShell/*`, `symlink-wayland-socket.service`, `install-burnttoast`,
  `check-wsl-lso`, `apply-wslconfig`, `apply-etc-config`, `install-wslu-repo` equivalents.
- **Employer tooling (`work_tooling`):** namespaced-VPN stack (`vpn-*`, `dual-vpn`, `namespaced-openvpn`,
  `install-vpn-symlinks`), and `rano`. Apply "Employer-specific content" first. Atlassian/Jira: see Held items.
- Still excluded: client-project material (D3; term list in the private repo, `client-terms.md`), `claude-mem-*`,
  `time-report`, `fewer-permission-prompts`, `auto-session/.transcripts`.

## Related plan: Sway

Wayland/Sway (preserving the i3 setup via a shared config fragment) is planned in [sway.md](sway.md), not here, to keep one source of truth. Sequencing: do Phase 0a (`home/` layout) first; Sway work then lands under `home/`.

## Per-phase checklist

1. `tools/compare-trees.py` shows the files moved from only-BOCO to both.
2. `chezmoi diff` on the new targets is understood; apply those targets only; `chezmoi status` clean (apart from ` R reload-systemd-user.sh`, which runs on every apply).
3. Guards hold: nothing WSL- or work-only is managed on this host (see Guards acceptance).
4. `gitleaks dir --no-banner .` finds no leaks (the 2 accepted findings are in `.gitleaksignore`, D30); anything is a stop.
5. Grep changed files with the pattern list in the private `client-terms.md`; expect nothing.
6. Tick [../bootstrap-debt.md](../bootstrap-debt.md) if a hand-installed tool is now managed; push the branch.

## Open questions

1. When should the Atlassian/Jira redaction pass happen, and who reviews it? (Held items.)
