---
summary: Working rules for sessions in this repo: commits, branches, public-repo scans, push/auth, chezmoi, shell quirks
status: current
updated: 2026-10-23
---

# Conventions

## Git
- Conventional commits `type(scope): description`; one logical unit per commit; trailer `Co-Authored-By` as configured.
- `main` is trunk. Significant work on a feature branch (`boco-merge/<phase>`, `docs-…`), merged when its checklist passes.
- Merge feature branches with `--no-ff`, so the merge commit keeps the branch's history on `main`. Finished branches
  (D65), with `git retire-branch` (`~/.local/bin/git-retire-branch`, `-n` for a dry run):
  - unmerged, may resume: keep as a branch, pushed;
  - unmerged and abandoned, or merged with a D-number or an important bugfix: `--archive` (kept as
    `refs/archive/<name>` here and on origin, hidden from `git branch` and GitHub's branch list);
  - merged and routine: `--delete`.
  List archives with `git for-each-ref refs/archive`; restore with `git branch <name> refs/archive/<name>`. A fresh
  clone fetches them after `git config --add remote.origin.fetch '+refs/archive/*:refs/archive/*'`. A history
  rewrite must cover `refs/archive/*` too (`git filter-repo` rewrites all refs by default; check afterwards).
- Porting a file from the reference clone: add trailer `Source: AudensAurantius/chezmoi@<sha>:home/<path>`
  (`git -C ~/Source/chezmoi-boco log -1 --format=%h -- home/<path>`). The SHAs are not objects in this repo (unrelated
  histories); they resolve in the public upstream. Check the SHA is an upstream commit
  (`git -C ~/Source/chezmoi-boco merge-base --is-ancestor <sha> upstream/main`). If it is only in the private clone's
  own commits, use `Source: antimike/chezmoi-boco@<sha>:home/<path>` instead. Trailers written before 2026-10-16 all use
  the upstream form; they were not rewritten (would need a force-push of `main`).
- Pushes use the `antimike.github.com` SSH alias (needs the YubiKey; test with `ssh -T git@antimike.github.com`). Claude may not create public repos; MH does.
- Keep real client/employer detail out of commits to public repos: scan first, show MH the redaction diff (D19).

## Public vs private
- This repo, `bd-track`, `claude-config`, `chess_trainer`, `resume-builder` are **public**. Before committing: `gitleaks dir <path>` (`detect` is deprecated; expect no leaks here, see D30) and the client-term grep (pattern list in the private repo: `~/Source/chezmoi-boco/docs/zbook-migration/client-terms.md`). In this repo both run as `tools/public-scan/public-scan`.
- Do not migrate client-project material. Sensitive inventories are in `~/Source/chezmoi-boco/docs/zbook-migration/`.
- Never print secrets (`pass show`, `gpg -d`): redirect or pipe, or they land in the transcript.

## Chezmoi
- `$PC` = this repo (chezmoi source root `~/.local/share/chezmoi/home` since Phase 0a; docs and `CLAUDE.md` stay at the repo root). Never `chezmoi init/apply` against the reference clone `~/Source/chezmoi-boco`.
- Propagate source edits with `chezmoi apply --force <target>`; never `cp`. Apply named targets, then check `chezmoi status`. `chezmoi apply` takes literal paths, not globs.
- Chezmoi ignores source mode bits: scripts invoked by path need an `executable_` prefix.
- Template guards: tool present = `lookPath`; WSL = shared `is-wsl` helper; employer-only = `work_tooling` (D25). Host-specific experiments: a hostname guard plus a data key in `.chezmoi.yml.tmpl`, read with `dig` and a default (e.g. `prefer_nvidia_for_external`, D52).
- Render-time commands go through `.chezmoitemplates/safe-output.sh`.
- No broken code or configs (D48): what chezmoi deploys must work where it renders. If it cannot be fixed yet, guard it
  out or remove it, and keep an open item until it is fixed.
- Helpers needed in more than one session type go in `~/.local/bin` and work in X11 and Wayland (`clip` is the model).

## Shell and tools
- zsh does not word-split unquoted variables: use arrays (`"${files[@]}"`) or `${=var}`.
- Paths beginning with `-` need `./` for `rm`, `du`, `ls`.
- Use the Read/Edit tools instead of `sed` or `awk` for viewing or editing files.
- Backups and rollbacks: `~/.local/state/claude-migration-backups/`.
