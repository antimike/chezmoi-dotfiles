---
summary: Working rules for sessions in this repo: commits, branches, public-repo scans, push/auth, chezmoi, shell quirks
status: current
updated: 2026-10-15
---

# Conventions

## Git
- Conventional commits `type(scope): description`; one logical unit per commit; trailer `Co-Authored-By` as configured.
- `main` is trunk. Significant work on a feature branch (`boco-merge/<phase>`, `docs-…`), merged when its checklist passes.
- Porting a file from the reference clone: add trailer `Source: AudensAurantius/chezmoi@<sha>:home/<path>`
  (`git -C ~/Source/chezmoi-boco log -1 --format=%h -- home/<path>`).
- Pushes use the `antimike.github.com` SSH alias (needs the YubiKey; test with `ssh -T git@antimike.github.com`). Claude may not create public repos; MH does.
- Keep real client/employer detail out of commits to public repos: scan first, show MH the redaction diff (D19).

## Public vs private
- This repo, `bd-track`, `claude-config`, `chess_trainer`, `resume-builder` are **public**. Before committing: `gitleaks detect --no-git -s <path>` and the client-term grep (pattern list in the private repo: `~/Source/chezmoi-boco/docs/zbook-migration/client-terms.md`).
- Do not migrate client-project material. Sensitive inventories are in `~/Source/chezmoi-boco/docs/zbook-migration/`.
- Never print secrets (`pass show`, `gpg -d`): redirect or pipe, or they land in the transcript.

## Chezmoi
- `$PC` = this repo (source `~/.local/share/chezmoi`, becoming `…/home` after Phase 0a). Never `chezmoi init/apply` against the reference clone `~/Source/chezmoi-boco`.
- Propagate source edits with `chezmoi apply --force <target>`; never `cp`. Apply named targets, then check `chezmoi status`. `chezmoi apply` takes literal paths, not globs.
- Chezmoi ignores source mode bits: scripts invoked by path need an `executable_` prefix.
- Template guards: tool present = `lookPath`; WSL = shared `is-wsl` helper; employer-only = `work_tooling` (D25).
- Render-time commands go through `.chezmoitemplates/safe-output.sh`.

## Shell and tools
- zsh does not word-split unquoted variables: use arrays (`"${files[@]}"`) or `${=var}`.
- Paths beginning with `-` need `./` for `rm`, `du`, `ls`.
- Use the Read/Edit tools instead of `sed` or `awk` for viewing or editing files.
- Backups and rollbacks: `~/.local/state/claude-migration-backups/`.
