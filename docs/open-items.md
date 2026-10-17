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

| **History rewrite before the first push (agreed 2026-10-16, not yet run).** The tracked tree has no client-term hits, but history still does: 28 paths (the okular recents list incl. an employer name, the old username in many files, an employer/client name in two early plan docs) and 4 commit messages. A rehearsal in a mirror clone (`git filter-repo`: drop the okular and vifminfo paths, scrub the pattern from blobs and messages) left 0 hits, 216 commits, and a tip tree identical to the current one. Real run: bundle backup, rewrite in place, re-add `origin`, map old SHAs in the docs, force-push `main` (MH confirms), then ask GitHub support to purge cached views. Do it once, right before the push | MH + Claude | rehearsed 2026-10-16 |
| The templated i3 config is not applied (no i3 session here); kitty `notes` points at `~/.config/i3/bin/open-notes.bash`, which does not exist yet | info | 2026-10-16 |
| Clipboard stack, built 2026-10-16 (details below), **untested end to end**: needs a Sway session, since GNOME has no data-control protocol. `cliphist` 0.7.0 is installed and tested (store, sensitive entries skipped, the picker and the audit against the real binary); on GNOME the three units fail with the protocol error and stop retrying, as designed. Built: `wl-clip-persist` v0.5.0 (source-build installer, applied), `cliphist@.service` + `wl-clip-persist.service` + `clipboard-stack.target` (applied, not enabled; Sway starts them with `exec systemctl --user start clipboard-stack.target`), `clipboard-history` (fzf picker) and `clipboard-history-audit` (gitleaks; finds formatted secrets only). `cliphist` honours `wl-copy --sensitive` itself (`CLIPBOARD_STATE`), so no handler script exists. `pass -c` copied with plain `wl-copy` (passwords would enter the history); fixed by the `~/.local/bin/pass` wrapper, which exports a `wl-copy` function adding `--sensitive` (tested with a real `pass`: -c, show -c, generate -c, otp -c; about 5-8 ms; upstream patch declined, fork not worth it). Also still to switch on `display_server`: `bin/screenshot`, vifm `yd`/`yf`, the-way `copy_cmd` (all `xclip`) | MH decides | 2026-10-16 |
| `_mise.tmpl` and `_pdm.tmpl` render empty on a first apply (render-time `output`); convert to installer-generated like `cheat`. Their completions already sit on `fpath`, but the files stay empty until a second apply | Claude | optional |
| `dstask-notify` script and systemd units are not ported yet | Claude | Phase 3 (timers) |
| Untested on non-Linux/non-amd64 hosts: the darwin and arm64 checksum rows for fzf, cheat, dnote, d2, dstask (darwin only), the-way (macos amd64 only) | info | rows verified against upstream, not run |

| `PASSWORD_STORE_ENABLE_EXTENSIONS` is set by the zsh snippet and `~/.bash_env`, so only interactive shells have it; a launcher or Sway keybinding that runs `pass dmenu` directly does not. Put it in `~/.config/environment.d/` if that bites | info | 2026-10-16 |
| `etckeeper-secret-audit` is installed but not run: it needs `sudo etckeeper-secret-audit` | MH | 2026-10-16 |
| Observed, not changed: `claude-init` writes `.claude/settings.local.json` with `Bash(git:*)` (includes `git push`) | info | 2026-10-16 |

## Closed recently
- Full `chezmoi apply` (2026-10-16, MH): `chezmoi status` and `chezmoi diff` are empty and `chezmoi verify` passes. It ran the 11 installers (all already current; `install-clipse` installed the Wayland clipse build, inert on GNOME) and applied `.claude.json`, the i3 config, two man pages and the newer `fzf-integration.zsh`. All nine pinned tools report their pinned versions.
- Bash cleanup (2026-10-16): conda loads on first use (interactive startup about 1.1 s to about 0.4 s; no `(base)` prefix or `CONDA_*` variables until the first `conda`), the asdf block is gone (every shim has a mise equivalent), and the `~/.local/bin` PATH fix is a function that also runs after the lazy conda hook. `bd start|stop` now routes to `bd-track` (zsh function `bd`, no longer BOCO's `bd-timew` version). `chezmoi completion bash` works again now that the stale asdf shim is off PATH.
- Phase 1 helpers (2026-10-16): `tutor` (fixed its default pager), `claude-init`, `etckeeper-secret-audit` (fixed an unchecked `cd`), the `pass` wrapper and extension setting, the `dotnet` snippet (adapted to Fedora's dotnet), `.bash_aliases` (guarded `fd`/`bat`, no obsolescent egrep alias), `.bash_env` and the merged `.bashrc`; `usage` now reads the real functions directory. `docstring`, `.zprofile` are not ported (duplicates). Applied with a snapshot in `~/.local/state/claude-migration-backups/phase1-helpers/`.
- jrnl, kitty `notes` and pet path fixes applied (2026-10-16, snapshot in `~/.local/state/claude-migration-backups/path-fixes/`).
- Completions on `fpath` (2026-10-16): the zshrc puts `~/.local/share/zsh/completions` on `fpath` before `compinit` and rescans when a file there is newer than the dump (`-C` never looks for new files); the `zinit creinstall` hook and its symlinks are gone. Measured: a full scan costs about 9 ms more with 26 extra completions, a cached start nothing.
- Client-term cleanup of the tracked tree (2026-10-16): zero hits. Home paths templated (jrnl, kitty notes, pet, i3, the-way), two man pages use `~`, and the dead README symlinks, `vifminfo.json` and `create_okularrc` are removed. History is a separate item above.
- `display_server` host key (`"wayland"`, `"x11"`, `"none"`) detected at `chezmoi init`; first user is the clipse installer (clipse v1.2.1, Wayland and X11 builds).
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
