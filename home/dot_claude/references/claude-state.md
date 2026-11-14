# Claude persistent state: detail

The always-on summary is in `~/.claude/CLAUDE.md`, "Persistent State". This file keeps the rationale (moved there 2026-11-13, chezmoi chz-ae3).

## Stores and hygiene (full text)

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
