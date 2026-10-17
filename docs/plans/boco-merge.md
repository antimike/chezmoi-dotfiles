---
summary: Phased plan to merge the employer-era (BOCO) chezmoi repo into this one: decisions, guards, phases, checklists
status: Phase 0a done (2026-10-15); rest of Phase 0 is next
updated: 2026-10-15
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
- Feature branch off `BOCO-migration` per phase (`boco-merge/<phase>`). Never `chezmoi init/apply`
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
- Acceptance: on this host, `chezmoi managed | grep -iE '(^|/)(\.?wsl[^/]*|[^/]*\.exe|vpn-[^/]*|dual-vpn|namespaced-openvpn|install-vpn-symlinks|rano[^/]*|winpath|getwinip|getlocalhost|sync-nfs)(/|$)'` is empty (anchored on path components; the earlier loose `vpn` pattern matched the personal `.config/protonvpn`) and `chezmoi diff` is quiet
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

### Phase 1: self-contained tools (BOCO versions authoritative; Fedora installers)
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

### Phase 2: Neovim (all BOCO plugins and themes)
Copy all ~35 plugin specs and the config files that differ (`init.lua`, `config/*.lua`, `plugins/{chezmoi,example,
formatting,treesitter}.lua`). BOCO wins; reconcile the lockfile (`lazyvim-lock.json` here vs `lazy-lock.json`) by
running `:Lazy restore`/`sync` on a clean profile. Skip `*.bak`. `mason.lua` is WSL-flavoured: check, guard if so.
Port `run_once_install_neovim_deps` for Fedora.

### Phase 3: timers and services (needs Phase 0)
- **`sync-repos` (low priority).** Its use-case in BOCO history was a single entry: a daily auto-commit and push of
  `~/.timewarrior` (the timewarrior data directory), to get off-machine history for a data repo nobody commits by
  hand. timew is obsolete (bd-track keeps its own event log) and `nb`/`dstask` handle their own git sync, so there
  is currently **no concrete use for it here**. Port it anyway as BOCO tooling (script + timer + `sync-repos-list`),
  with an **empty** repo list on this host; revisit when a real data repo qualifies. Auto-committing unreviewed
  content is only safe with a secret scan, which is handled by hooks, not by this script (below).
  It does not need replacing: `mani`/`git for-each-repo` run a command per repo but don't auto-commit.
  Add a templated `mani.yaml` for interactive `mani run status --all` ("what needs pushing?") if wanted.
- **gitleaks pre-commit hooks in every repo that needs them** (replaces a scan inside `sync-repos`; a hook also
  fires on the auto-commit, and a failing hook just leaves that repo dirty and logged). Pattern: the
  `.pre-commit-config.yaml` used in `claude-state` (a `local`/`system` gitleaks hook) plus `pre-commit install`.
  Roll out to: all public repos (`chezmoi-dotfiles`, `bd-track`, `claude-config`, `chess_trainer`, `resume-builder`),
  any repo on the sync list, and `claude-state` (done). Make it repeatable with a `mani` task that installs the hook
  across tagged repos. Hooks are per clone, so a fresh machine needs the task re-run. Optional safety net: a chezmoi-managed
  `init.templateDir` whose `hooks/pre-commit` runs `gitleaks protect --staged`, so every new clone gets a hook.
  Watch for conflicts: `pre-commit install` refuses if `core.hooksPath` is set (unset in the repos checked on
  2026-10-14), and `bd hooks install` also writes `.git/hooks/*`; pre-commit chains existing hooks as `.legacy`.
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
2. `chezmoi diff` on the new targets is understood; apply those targets only; `chezmoi status` clean.
3. Guards hold: nothing WSL- or work-only is managed on this host (see Guards acceptance).
4. `gitleaks detect --no-git --no-banner -s .` shows only the 2 accepted findings (`home/private_dot_config/private_systemd/private_user/private_polybar-weather.service.tmpl`, `home/private_dot_jupyter/private_certs/private_service-key.pem`; accepted by MH 2026-10-15); anything new is a stop.
5. Grep changed files with the pattern list in the private `client-terms.md`; expect nothing.
6. Tick [../bootstrap-debt.md](../bootstrap-debt.md) if a hand-installed tool is now managed; push the branch.

## Open questions

1. When should the Atlassian/Jira redaction pass happen, and who reviews it? (Held items.)
