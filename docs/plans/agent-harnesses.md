# Agent harnesses: gitagent and Pi (chz-awx)

Read-only, timeboxed evaluation (2026-11-20; no installs), from MH's note of 2026-11-13: could either tool
replace part of the chezmoi-managed Claude Code config (`home/dot_claude/`) or claude-config's sandbox and
profile work? Sources: each project's README and docs, GitHub metadata via `gh api`. Nothing below was run
here; claims marked "docs" are the project's own.

## Verdicts

| Tool | What it is | Verdict, personal | Verdict, team / job |
|---|---|---|---|
| gitagent | Its own agent harness (Rust), plus a git-repo format for agent definitions | **No** | No |
| Pi | Its own minimal coding-agent harness (TypeScript), multi-provider | **No** for daily use; revisit after the job search | **Worth knowing**; a hands-on trial only if a role uses it |

Neither is a config layer for Claude Code. Adopting either means running a second agent harness beside
Claude Code (or instead of it), with its own instruction, skill, memory and hook formats, and, as far as
the docs say, paid per token on an API key rather than on MH's Claude subscription.

## gitagent (open-gitagent/gitagent)

- **What it is** (docs): "your agent is a git repository". An agent is a folder: `agent.yaml`
  (`spec_version` 0.1.0), `SOUL.md`, `RULES.md`, `memory/`, `skills/<name>/SKILL.md`, `tools/`, `hooks/`,
  `schedules/`, `workflows/`; a single Rust binary reads it on every start and runs its own agent loop.
  Python/TypeScript SDKs drive the binary over JSON-lines IPC. It can read an existing `.claude/` layout
  (agents, skills, settings, hooks) and names its tools like Claude Code's (`Bash`, `Read`, `Edit`).
- **Providers** (docs): Anthropic, OpenAI, Gemini, any OpenAI-compatible endpoint; API keys.
- **Sandbox** (docs): Linux Landlock + seccomp (writes limited to the workdir, output, temp and
  `~/.cache`; reads unrestricted), `sandbox-exec` on macOS.
- **Maturity**: MIT, 755 stars, 9 contributors, created 2026-03. v3.0.0 (2026-11-08) is a Rust rewrite of
  the 1.x/2.x TypeScript tool, 12 days old (fails our 14-day pin rule). Its Terminal-Bench claim (93% with
  Opus 5.5) is self-reported.
- **What it would replace here**: nothing worth replacing. "Agent config as versioned files" is what this
  repo already does for Claude Code (`home/dot_claude/`, deployed by chezmoi, history in git). Switching
  would move skills, rules, hooks and memory into gitagent's format and run its loop instead of Claude
  Code's: high cost (every hook, skill and the bd-track/beads wiring re-tested), no gain named.
- **For claude-config**: its Landlock + seccomp sandbox is prior art for claude-config's Phase 1
  (`claude-sandbox`), together with Claude Code's own sandboxing (its `/sandbox` mode; not checked in this
  evaluation); ticket filed there (below).

## Pi (earendil-works/pi, formerly badlogic/pi-mono)

- **What it is** (docs, README): "AI agent toolkit: unified LLM API, agent loop, TUI, coding agent CLI".
  A separate, deliberately minimal coding agent (`pi`), not a Claude Code wrapper. Instructions in
  `AGENTS.md`; prompt templates, skills, extensions (tools, commands, event handlers), custom TUI
  components and installable packages; state in `~/.pi/agent/`. It shows every tool call but "does not ask
  before every tool call"; its docs say to use a container or sandbox for unattended or untrusted work.
- **Providers** (docs): about 40, including Anthropic. For Anthropic the docs document an API key
  (`ANTHROPIC_API_KEY`); whether `/login` offers a Claude Pro/Max subscription sign-in is not stated, and
  whether Anthropic's terms allow a subscription in a third-party harness was not checked: assume
  per-token API billing until verified.
- **Maturity**: MIT, about 123k stars, 100+ contributors, releases every few days (v1.6.0 on 2026-11-20);
  an ecosystem around it (web UI, MCP and ACP adapters, a Hugging Face Python port).
- **What it would replace here**: Claude Code itself, not its config. Cost of switching: port CLAUDE.md
  and the rules to `AGENTS.md`, skills to Pi's format, hooks (SessionStart ticket notice, bd-track checks,
  the baduk project's contract hooks) to extensions; add a sandbox because Pi does not prompt; pay per
  token. Gain: provider choice and a smaller, hackable harness.
- **Personal fit**: no while the job search is first (D50) and every workflow here (beads, bd-track,
  `/work-queue`, triage skills) is built on Claude Code.
- **Team / job fit**: Pi is the best-known open harness, so knowing it (multi-provider agents, AGENTS.md,
  extensions) is useful in interviews and at a job that standardises on it or on non-Anthropic models. A
  timeboxed hands-on trial (an API key with a spend cap, inside a container) is worth doing then, not now.

## Follow-ups

- Ticket to claude-config: prior-art entries for Phase 1 (the D81 gate), Claude Code's own sandboxing
  and gitagent's Landlock + seccomp, before more sandbox work.
- Revisit Pi after the job search, or when a role calls for it (no bead).
