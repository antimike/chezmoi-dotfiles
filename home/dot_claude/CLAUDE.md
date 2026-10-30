# Global Claude Instructions

These instructions apply to all projects. Project-specific CLAUDE.md files may extend or override them.

## Session Discipline

- Follow conventional commits: `<type>(<scope>): <description>` with `Co-Authored-By` trailer
- Make commits modular — one logical unit per commit. For multi-step features, commit each layer as you validate it (e.g., domain models, then storage, then service, then config wiring, then routes, then tests). Never batch an entire feature into a single commit.
- Use feature branches for significant work. Branch off the primary working branch, develop incrementally with modular commits, merge back when complete. This keeps the working branch clean and makes changes reviewable.
- Before starting a bead, evaluate whether the user should `/clear` first (large unrelated context loaded, prior bead's scope diverges from the new one); raise the same suggestion after closing a bead.
- Before starting a bead, recommend an appropriate model for its scope: Haiku for mechanical/lookup work, Sonnet as the default, Opus for architectural decisions, deep multi-file refactors, or work touching sensitive surfaces.

## Persistent State

Three stores, split by purpose:

- **`bd remember` + `bd memories`** — project-technical facts (pitfalls, naming conventions, environment quirks). Auto-injected at `bd prime` time. Persists via the project's `.beads/` nested repo; requires off-machine sync (push the nested repo, or use Dolt sync) for true account-rotation resistance.
- **Auto-memory** (`~/.claude/projects/<project>/memory/`) — user-specific preferences, collaboration feedback, cross-project user facts. Typed topic files (user/feedback/project/reference) loaded on demand via the auto-memory `MEMORY.md` index. Update organically during sessions when new facts emerge; no ritual "update before /clear" needed.
- **CLAUDE.md** (this file and project-local) — always-on rules and one-line pointers to frequently-relevant auto-memory topics. Graduate durable, broadly-applicable feedback into CLAUDE.md one-liners; keep the "Why:/How to apply:" detail in auto-memory.

Hygiene rules that persist:
- Keep the auto-memory `MEMORY.md` index under 200 lines; archive stale content to `~/.claude/projects/<project>/memory/history.md`
- Create checkpoint files at `~/.claude/projects/<project>/memory/checkpoint-YYYY-MM-DD-<topic>.md` for sessions that advance a roadmap item or make significant decisions — claude-mem observations cover mechanical activity, but gestalt / "where we left off" narrative still benefits from explicit capture. **Checkpoints live in auto-memory, NOT in the project source tree** (e.g., `~/Source/<project>/memory/`); cross-session discoverability matters more than git-versioning for this content
- Do not maintain a repo-root `MEMORY.md` as a state-tracking artifact — it fragments across accounts and duplicates what `bd remember` now handles
- When a doc says "`memory/...`" with no leading path, it means **auto-memory** (`~/.claude/projects/<project>/memory/`). Do not create or look in a `memory/` directory at the project source root
- **Opportunistically** suggest `/trim-claude-config` if, in the course of normal session work, you read a Claude-context-injected file (`CLAUDE.md`, `MEMORY.md`, or another always-on chained file) that exceeds the skill's soft caps. Do NOT proactively examine config files for this purpose — only flag what you encounter.

## Network ops in beads workflows

- Do NOT run `bd dolt push` as part of session-end automation, cleanup, or checkpointing. The Dolt-side push is the user's responsibility to run interactively when convenient.
- The JSONL state (the human-readable issues export) IS pushed via plain `git push` from the project's `.beads/` directory. That's small, fast, and adequate for cross-session visibility into bead state.
- This convention exists because `bd dolt push` can stall on transient network issues (LSO bugs, PMTU blackholes, TCP metrics cache poisoning — see project pitfall docs); blocking session-end on it is unacceptable. The JSONL push is reliable; the Dolt push is best-effort.

## Implementation Approach

- Implement features depth-first: complete and validate one unit before starting the next
- Never generate parallel implementations before validating any of them
- For multi-part work, screen each part with minimal effort before committing to full treatment
- Prioritize working software over scaffolding — a running feature beats a planned architecture
- For small-scope work (< 2 hours), prefer a plan-mode discussion followed by implementation over creating a separate planning document. The conversation is the plan; don't persist it as an artifact unless the scope grows
- **Python scripts follow the `python-scripting` skill** (`~/.claude/skills/python-scripting/SKILL.md`), the source of truth for Python conventions (argparse with `--loglevel`, `logging` over `print`, ruff, credentials from config/env). Load it before writing or editing any `.py` file, even when it does not trigger on its own

## Verification Before Claiming Completion

Before saying "done", "fixed", "passing", "working", or any equivalent — in the same message that carries the claim:

- **Run the verification command fresh.** Prior-run output doesn't count. "I ran it earlier and it passed" is a claim, not evidence.
- **Mind the gap between tools.** Linter passing ≠ compiler passing. Tests passing ≠ feature works. An agent reporting "success" ≠ code actually changed — check `git diff`.
- **Regression tests need a red-green-red cycle.** If you wrote a test to catch a specific bug, revert the fix, re-run (must fail), restore the fix, re-run (must pass). A test that only passes once isn't a regression test.
- **Multi-item requirements need a checklist.** "Tests pass" ≠ "all requirements met". Re-read the plan, enumerate each item, verify each one. Report gaps explicitly.
- **"Should work now", "I'm confident", and "just this once" are red flags.** They usually mean the command wasn't run. Run it.

## Spawning independent agents

Before invoking the Agent tool, use the `spawn-agents` skill — predict tools each agent needs, pre-load deferred-tool schemas, declare the tool set for batch approval, dispatch only after approval. If you can't reasonably predict tool usage, say so and wait for the user to accept the in-flight-prompts friction. Full procedure + rationale: `~/.claude/skills/spawn-agents/SKILL.md`.

## Shell command conventions

- **Avoid `sed` (and `awk`) for reading or editing files — use the Read and Edit tools instead.** `sed` is deliberately *not* added to permission allowlists, because Claude Code's prefix-based Bash matching cannot safely separate read-only `sed -n`/substitution from destructive in-place `sed -i`: flag combinations like `sed -ni` or `sed -n -i …` defeat any `sed -n`-style prefix pattern. So `sed` will always prompt, and an allowlisted `sed` would be a real footgun. Reserve `sed` for pipelines where it is genuinely necessary and no dedicated tool fits; never use it to view file sections (use Read with offset/limit) or to edit files (use Edit).
- The same caution applies to any tool whose read-only and destructive modes differ only by a flag that can be combined with allowed flags — prefer a purpose-built tool or leave it to prompt rather than allowlisting an unsafe prefix.

## Standing Instructions

- Push back against any aspect of a prompt that seems misguided, vague, ill-informed, or overly ambitious — be direct, not diplomatic
- Discuss alternatives to the proposed approach, summarizing trade-offs concisely
- When a design decision is significant enough to affect the project's direction, flag it and suggest adding it to the project's decision log
- Do not soften feedback to be polite; clarity matters more than comfort
- Ask for tool installs freely: if a package would give better data or tooling (even an interactive one only the user would run, e.g. `nvtop`), name it and ask; installing costs the user one `sudo` command in an adjacent terminal. Add what gets installed to the project's package manifest, guarded to the hosts where it is relevant.

### Beads (bd) Performance

- **Slow `bd` commands** (5-30s): caused by journal bloat or commit history growth in the embedded Dolt store. Fix: `bd compact --days 7 --force && bd gc --skip-decay --force`. Nuclear reset: `bd flatten --force && bd gc --skip-decay --force`. See `~/.claude/references/beads-performance.md`.
- **New project setup**: always run `bd config set dolt.auto-commit batch` and `bd config set no-push true` after `bd init`. Add the daily maintenance cron (commit + compact + gc). Details in the reference file.

### Beads (bd) Gotchas

**Dependency hygiene (standing practice)**: whenever you work on a cluster of related beads -- creating, reviewing, or restructuring them -- actively discover the relationships between them and formalize each as an edge via `bd link` (`blocks` / `tracks` / `related` / `parent-child` / `discovered-from`) or `bd dep` (`blocks`). Err on the side of more edges, not fewer: **when in doubt, add the edge.** Prose-only relationships are invisible to `bd ready`, `bd dep list`, and `bd dep cycles`. After any cluster restructure, run `bd dep cycles` to confirm no loop was introduced.

One-line gotchas (detail in cheatsheet — see end of section):

- **Edge types beyond `blocks`**: `bd link <a> <b> --type <T>` accepts `blocks` / `tracks` / `related` / `parent-child` / `discovered-from`; `bd dep add/remove` only handles `blocks`. Edges are directed even for symmetric types.
- **Node-type rule for `blocks`**: epic↔epic OK; epic→task **rejected**. To make a task depend on an epic, block it on the epic's terminal leaf task.
- **Custom statuses**: `bd config set status.custom <comma-list>`; entry shape `<name>` or `<name>:<category>`; name regex `[a-z][a-z0-9_-]*`. Mirror to `~/.config/bd-track/repos.yaml` without the category suffix.
- **`BEADS_DIR` contamination**: do NOT export `BEADS_DIR` or `BEADS_DOLT_PASSWORD` from any `.envrc` — they leak into other projects' shells and override cwd-based auto-discovery. If contaminated, `unset` them.
- **Dependency edge removal**: `bd dep remove <id> <depends-on-id>` removes whichever edge exists between two beads regardless of type.
- **`bd init` commits and adds a Dolt remote**: it commits `.beads/` to the outer repo and makes git `origin` a Dolt remote (`sync.remote`). `bd config set` stops committing once `no-git-ops` is set; `bd config unset` commits anyway. For a public repo: `bd config set no-git-ops true`, `bd dolt remote remove origin`, `bd config unset sync.remote`, gitignore `.beads/`, then `git reset` (mixed) over bd's commits and check `git log`.
- **Searching memories**: `bd memories <substring>` matches slugs; add `--json` for full bodies. Cheap — reach for it before guessing bd syntax. **Note**: bd memories are per-project; slugs only resolve inside their originating project.

**Maintenance**: when new bd findings turn up, add a one-liner here if broadly useful and expand `~/.claude/references/beads-cheatsheet.md`.

**Full reference**: `~/.claude/references/beads-cheatsheet.md`.

### Ticket inboxes (cross-project requests)

Every project in the registry `~/.config/projects.yaml` has an inbox at `~/.local/state/triage/<project>/` (`triage/` open tickets, `triage/inbox.md` quick notes, `done/` handled). To hand something to another project, file a ticket with the `ticket` command and **never touch that project's repo or beads** (the `triage-file` skill has the format). A project processes its own inbox with `/triage` (the `triage` skill): MH decides each ticket; accepted ones become beads or docs. Design: chezmoi D72.

### Collaboration Preferences (see auto-memory for full context)

- **Jira comments**: lead with context/methodology, integrate links, connect to team knowledge; avoid prescriptive "next steps" in analysis comments. See `feedback-jira-comment-style.md`.
- **Jira drafts**: track posting status (`posted`, `comment_id`, `target_status`) in YAML frontmatter; always use `contentFormat: "adf"`. See `feedback-jira-draft-frontmatter.md`.
- **Chezmoi edits**: respect templating layers and known pitfalls when modifying dotfiles. See `feedback-chezmoi-patterns.md`.
- **Chezmoi propagation -- never `cp`**: to push a source edit to its live target, use `chezmoi apply --force <target>`, NOT `cp ~/.local/share/chezmoi/... ~/.claude/...`. A raw `cp` bypasses chezmoi's state bookkeeping, so a later `chezmoi apply` sees the target as externally-modified and tries to prompt before overwriting -- which fails with `could not open a new TTY` in a non-interactive shell. Using `apply` consistently keeps the bookkeeping coherent; `--force` skips the destination-modified confirmation.
- **Chezmoi worktree testing**: `chezmoi apply` always reads from the canonical source (`~/.local/share/chezmoi/`), not the active feature worktree. To test from a worktree: `chezmoi apply --source ~/Source/chezmoi-features/home --force <target>`.
- **Chezmoi repo docs**: plans, decisions, open items and current status for the dotfiles repo live in `~/.local/share/chezmoi/docs/` (start at `docs/STATUS.md`; the repo's own `CLAUDE.md` auto-loads it when the session runs there). When working on chezmoi from another directory, read it first.

## Review Checkpoints

- After completing each feature or roadmap item, offer a brief review checkpoint
- Review checkpoints should summarize: what changed, decisions made, new bugs/pitfalls found, roadmap impact
- For team projects, persist review summaries to `docs/reviews/`; for personal projects, a verbal summary suffices unless the user requests persistence

## Documentation Practices

- Maintain a single source of truth — never create overlapping summary documents
- Use Markdown links from higher-level docs to detailed explanations rather than duplicating content
- When referencing code, include file paths and line numbers
- Distinguish confirmed facts from hypotheses in all analysis
- Keep documentation proportional to the project's complexity and audience
