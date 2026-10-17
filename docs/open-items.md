---
summary: Every open item across the migration, BOCO merge, Sway and housekeeping, with source and who acts
status: current
updated: 2026-10-16
---

# Open items

"MH" = needs the repo owner. "Claude" = can be done in a session. Update this file when an item closes; keep decisions in [decisions.md](decisions.md).

## Next up
| Item | Who | Where |
|---|---|---|
| BOCO chezmoi merge, Phases 1-6 | Claude | [plans/boco-merge.md](plans/boco-merge.md) |
| Push the private findings doc to `chezmoi-boco` (committed locally) | MH approval | `~/Source/chezmoi-boco/docs/zbook-migration/` |
| Distro-agnostic package map (logical names, per-manager overrides, non-native fallbacks) | MH + Claude | [Detail below](#detail-package-map-refactor); proposed as D32 |
| zsh switch-over (Step 4 of Phase 0), then the keybinding manifest (D33 draft) and zsh simplification (two-layer plugin templating, exports machinery) | Claude | [plans/boco-merge.md](plans/boco-merge.md), [log/zsh-step4-inventory.md](log/zsh-step4-inventory.md) |
| Atlassian/Jira review and redaction pass | MH + Claude | [plans/boco-merge.md](plans/boco-merge.md), "Held items" |

## Plans waiting on a start
| Item | Who | Where |
|---|---|---|
| Sway session, then shared WM config fragment | Claude | [plans/sway.md](plans/sway.md) (Phase 0a done; unblocked) |
| claude-mem evaluation (about 30 min requirements, ~1 week trial in `CLAUDE_CONFIG_DIR=~/.claude-trial`) | MH + Claude | deferred; evidence so far favors dropping it |
| gitleaks pre-commit hook rollout across public repos | Claude | [plans/boco-merge.md](plans/boco-merge.md), Phase 3 |
| zsh switch-over test (scratch-home render first) | Claude | [plans/boco-merge.md](plans/boco-merge.md), Phase 0 |

## Housekeeping
| Item | Who | Notes |
|---|---|---|
| Delete stray remote branch `claude/implement-from-notes` in `chess_trainer` | MH approval | duplicate of `main`; deferred |
| Wire the env var for the credential moved to `pass` (consumer project unknown) | MH | details in the private doc |
| Rotate two unused keys that sit in the public chezmoi repo | MH | details in the private doc; source from `pass` |
| Extend or retire the expired old GPG key; clean the keyring | MH | [runbooks/gpg-and-signing.md](runbooks/gpg-and-signing.md) |
| Bring `~/.gitconfig`, `gpg.conf`, `~/.ssh/config` under chezmoi | Claude | Phase 0 of the BOCO merge |
| Live-test `/start`, `/stop`, `/status`, `/next` | MH | `/next` falls back to `bd ready` (`bv` not installed) |
| Prune the legacy session log in auto-memory `MEMORY.md` of the home project | Claude | it is not an index |
| LUKS partition on the external SSD (D18) | MH | needs ~60 GB moved off the exFAT drive first |
| Timers fail while the YubiKey is unplugged | info | retry next run; consider a dedicated unattended password path if annoying |
| Known gaps: java pin, Go version mismatch, unmanaged `yq`, `tofi` | Claude | [bootstrap-debt.md](bootstrap-debt.md) |
| `.chezmoi.yml` doctor warning (`suspicious-entries`) | info | cosmetic; renaming would create a second config |
| zinit's `~/.zcompdump` is reused with `-C` by `fast-syntax-highlighting`'s `zicompinit`, so new completions only appear after deleting it (`rm ~/.zcompdump*`); `.zcompdump.zbook.220817` (2024) is a leftover | info | found 2026-10-16 |
| rustup: `~/.cargo/bin` holds a stale toolchain (cargo 1.74.0, 2023) that is off `PATH`; the packaged cargo is 1.98.1. Decide: managed rustup installer + current `stable` + `PATH`, or remove `~/.cargo` | MH + Claude | left out of `zshenv` on purpose (2026-10-16) |
| Unmanaged zsh leftovers: `snippets/pipx.zsh` (2023 argcomplete handler; overlaps the managed `_python_argcomplete` completion, Phase 1 skips generated completions), parked `widgets/`, old `completion/` | Claude | triage after the zsh apply |
| `^X^R` is `redisplay` instead of `_read_comp` since the zshrc switch (rarely used completion-debug key) | info | not traced; the D33 audit would surface this kind of change |
| fzf `--bash` Alt-C and `**` completion verified in a scratch home only; darwin/arm64 checksum rows are untested on those hosts | info | 2026-10-16 |

| New zsh completions are invisible until `zinit creinstall -q ~/.local/share/zsh/completions` runs and `~/.zcompdump*` is removed: `completions/` is not on `fpath`; files reach it as symlinks in `zinit/completions`, made only by the `atpull` hook. The Phase 1 installers write `_cheat`, `_dstask`, `_the-way` there (linked by hand on 2026-10-16). Proposal: put the directory on `fpath` in the zshrc (then no creinstall is needed), after a zsh-probe run | MH decides, Claude | found 2026-10-16 |
| `_mise.tmpl` and `_pdm.tmpl` use the render-time `output` pattern and render empty on a first apply; convert to installer-generated, like `cheat` | Claude | optional |
| 11 already-tracked files in this public repo hit the client-term scan (a previous machine's username/home path in 10 of them): `man1h/glow.1h`, `man1h/virtualenv.1h`, `man1r/symlink_i3lock-fancy.README.md`, `man1r/symlink_xsv.README.md`, `private_dot_config/{i3/config.tmpl,jrnl/jrnl.yaml,kitty/sessions/notes.conf,pet/config.toml,vifm/vifminfo.json,create_okularrc}`. Run the scan from `docs/conventions.md` for the matches. Pre-existing, not from Phase 1 (`the-way.toml` is fixed). Needs a redaction diff for MH (D19) | MH + Claude | found 2026-10-16 |
| `the-way` `copy_cmd` is `xclip`; this host is Wayland (`wl-copy` is installed). Change if `the-way cp` misbehaves | info | 2026-10-16 |
| `dstask-notify` script and systemd units are not ported yet | Claude | Phase 3 (timers) |
| Installers were run directly (a scoped apply cannot target a `run_onchange` script), so chezmoi has no state for them; the next full apply re-runs them, and they are idempotent | info | 2026-10-16 |
| Untested on non-Linux/non-amd64 hosts: the darwin and arm64 checksum rows for fzf, cheat, dnote, d2, dstask (darwin only), the-way (macos amd64 only) | info | rows verified against upstream, not run |

## Closed recently
- bash `PATH` order (2026-10-16): conda's hook put `/usr/bin` first; `~/.bashrc` now re-asserts `~/.local/bin` last. Note `python` in bash still resolves to `/usr/bin/python` because the pyenv shims sit behind `/usr/bin`; not addressed.
- Phase 1 tool installers (2026-10-16, branch `boco-merge/1-tools`): cheat 5.1.0, cht.sh (+ `cht`), the-way v0.20.3 (+ widgets), nb 7.25.5, dnote cli-v0.16.0, dstask v1.0.1, d2 v0.9.0, with a shared completion helper. Fixed BOCO bugs: the dstask URL returned 404 and its hashes matched un-uploaded files; the-way fetched the x86_64 build on arm64; `_the-way` was a 0-byte file; `the-way.toml` hard-coded a foreign home. Applied with a snapshot in `~/.local/state/claude-migration-backups/tools-apply/`.
- fzf, Phase 1 item 1 (2026-10-16, branch `boco-merge/1-tools`): v0.74.4 pinned, installer, `fzf --bash` integration; applied to `~/.local/bin/fzf` and `~/.bashrc.d` (snapshot in `~/.local/state/claude-migration-backups/fzf-apply/`).
- Phase 0 of the BOCO merge (2026-10-16): `is-wsl`, `work_tooling`, systemd reload script, git/GPG/SSH config, zsh switch-over (applied, merged, pushed). Stale `rtx` RPM removed by MH.
- BOCO merge Phase 0a (`home/` layout), merged and pushed 2026-10-15; the 2 gitleaks findings are accepted as expected.
- Public `bd-track` scrub (2026-10-15), GPG key switch, branch consolidation, step 7 (see [log/migration-steps.md](log/migration-steps.md)).

## Detail: claude-mem evaluation (deferred)
1. Requirements session with MH (~30 min).
2. Desk research (one web-search subagent): current claude-mem (is the `observer-sessions` recursion fixed?), native auto-memory, marketplace memory plugins, MCP memory servers. Criteria: footprint, dependencies, injected content, token cost, storage growth, export, maintenance, license.
3. Trial ~1 week in an isolated profile (`CLAUDE_CONFIG_DIR=~/.claude-trial`) vs a native-only baseline. Measure session-start tokens, `/usage` deltas, disk growth, and log whether it surfaced anything useful.
4. Decide, then migrate data. Clean its DB (drop `observer-sessions` and client rows, `VACUUM`) only if it stays. Evidence so far: 9,211 hook firings vs one `mem-search` invocation. Held items in chezmoi: `claude-mem-audit` skill/command, `claude-mem-cleanup` script and timer, `.claude-mem/` settings.

## Detail: package map refactor
Status: proposed, not started ([D32](decisions.md) is a draft). Goal: make package installation distro-agnostic without scattering distro conditionals through templates.

**Today.** `home/.chezmoidata/packages.yaml` is `packages: fedora: [...]` and `run_onchange_install-packages.sh.tmpl` exits unless the distro is Fedora with `dnf`. Some other data files use `- dnf: <pkg>` / `- pipx: <pkg>` entries (`systemd.yaml`, `rofi.yaml`). Tools with pinned releases have their own `.chezmoidata/<tool>.yaml` plus `run_onchange_install-<tool>.sh.tmpl`.

**Design.**
1. **Logical-name map.** One entry per tool, keyed by a logical name. Per-manager overrides are listed only where the native package name differs. Example: `delta: { dnf: git-delta }` (the apt/pacman/brew name is `delta`).
2. **Manager key.** One derived data key (from `osRelease.id`: fedora to `dnf`, debian/ubuntu to `apt`, arch to `pacman`) selects the column. Adding a distro means one entry in that table, one install-command branch in the installer, and overrides only where names differ.
3. **Non-native tools.** A manager entry may be a *method* instead of a package name: `{ pipx: <pkg> }`, `{ mise: <backend:tool> }`, `{ cargo: <crate> }`, or `{ release: <tool-id> }` (use the repo's pinned-release installer). `false` or a missing entry means "not available here, use the `fallback`".
4. **No silent default when identity can differ.** Names that mean different programs on different distros (known case: `yq`, see below) must carry an explicit entry for every manager, never the default-to-logical-name rule. An optional `verify:` command (for example `yq --version | grep -q mikefarah`) is run after install and fails loudly on a mismatch.
5. **Fedora behaviour unchanged.** The refactor must produce the same single `dnf install` with the same package set. Acceptance: the rendered installer diff for this host shows no change in the package list.

**Open points.**
- `yq`: Fedora's `yq` is the Go tool (mikefarah). Debian/Ubuntu's `yq` is, to my recollection (not yet checked here), a different tool, the Python jq-wrapper. [bootstrap-debt.md](bootstrap-debt.md) lists `yq` as unmanaged; it is the natural first entry to model, with a `mise` or pinned-release method as the portable fallback.
- Nix derivations were considered for the non-native category and rejected as overkill for now (rationale in D32). Revisit only if more than a handful of tools need build recipes that `mise` backends cannot express.
- `git-delta` is added to the current Fedora list during Phase 0 and carried over by the refactor.
- **No `pipx` manifest exists yet.** `packages.yaml` only installs the `pipx` program itself; tools installed through it are tracked nowhere (`pipx list` shows 20 on this host, e.g. `nbdime`, `dvc`, `conda-lock`), apart from `bd-track` (own installer) and `pywal` (`systemd.yaml`). The refactor's `{ pipx: <pkg> }` method is the manifest: `nbdime` (installed by hand 2026-10-16; `~/.gitconfig` renders its diff/merge drivers when it is on `PATH`) is the first entry, and the rest should be triaged into it (keep, drop, or leave unmanaged). Until then the installer must not be assumed to cover them.
