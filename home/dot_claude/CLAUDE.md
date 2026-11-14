# Global Claude Instructions

These instructions apply to all projects. Project-specific CLAUDE.md files may extend or override them.

## Session Discipline

- Follow conventional commits: `<type>(<scope>): <description>` with `Co-Authored-By` trailer
- Make commits modular — one logical unit per commit. For multi-step features, commit each layer as you validate it (e.g., domain models, then storage, then service, then config wiring, then routes, then tests). Never batch an entire feature into a single commit.
- Use feature branches for significant work. Branch off the primary working branch, develop incrementally with modular commits, merge back when complete. This keeps the working branch clean and makes changes reviewable.
- Before starting a bead, evaluate whether the user should `/clear` first (large unrelated context loaded, prior bead's scope diverges from the new one); raise the same suggestion after closing a bead.
- Before starting a bead, recommend an appropriate model for its scope: Haiku for mechanical/lookup work, Sonnet as the default, Opus for architectural decisions, deep multi-file refactors, or work touching sensitive surfaces.

## Persistent State

- **`bd remember` / `bd memories`**: project-technical facts (pitfalls, naming conventions, environment quirks); injected at `bd prime`.
- **Auto-memory** (`~/.claude/projects/<project>/memory/`): user preferences, collaboration feedback, cross-project user facts; update as facts emerge. Keep its `MEMORY.md` index under 200 lines (archive to `history.md`).
- **CLAUDE.md and `~/.claude/rules/`**: always-on rules and one-line pointers. Graduate durable, broadly-applicable feedback into one-liners; keep the "Why:/How to apply:" detail in auto-memory.
- **Checkpoints** for sessions that advance a roadmap item or make significant decisions: `~/.claude/projects/<project>/memory/checkpoint-YYYY-MM-DD-<topic>.md`, in auto-memory, never in the project source tree.
- "`memory/...`" with no leading path means auto-memory. No repo-root `MEMORY.md`, no `memory/` directory in the source root.
- **Opportunistically** suggest `/trim-claude-config` when a Claude-context file you happen to read exceeds the skill's soft caps; never examine config files for this on purpose.

Rationale and full text: `~/.claude/references/claude-state.md`.

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

- **Avoid `sed` (and `awk`) for reading or editing files**: use Read (offset/limit) and Edit. `sed` stays off the permission allowlists on purpose (`sed -ni` defeats any `sed -n` prefix rule, so it always prompts); reserve it for pipelines no dedicated tool fits. The same goes for any tool whose destructive mode is one combinable flag away. Detail: `~/.claude/references/shell-conventions.md`.

## Standing Instructions

- Push back against any aspect of a prompt that seems misguided, vague, ill-informed, or overly ambitious — be direct, not diplomatic
- Discuss alternatives to the proposed approach, summarizing trade-offs concisely
- When a design decision is significant enough to affect the project's direction, flag it and suggest adding it to the project's decision log
- Do not soften feedback to be polite; clarity matters more than comfort
- Ask for tool installs freely: if a package would give better data or tooling (even an interactive one only the user would run, e.g. `nvtop`), name it and ask; installing costs the user one `sudo` command in an adjacent terminal. Add what gets installed to the project's package manifest, guarded to the hosts where it is relevant.

## Rules and pointers

- **Topic rules** live in `~/.claude/rules/` (chezmoi-managed): `beads.md` and `ticket-inboxes.md` load every session; `chezmoi.md` loads when chezmoi source files are touched.
- **Editing chezmoi-managed dotfiles from another directory**: read `~/.claude/rules/chezmoi.md` and `~/.local/share/chezmoi/docs/STATUS.md` first.
- **Jira** comments and drafts: the `jira-conventions` skill.

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
