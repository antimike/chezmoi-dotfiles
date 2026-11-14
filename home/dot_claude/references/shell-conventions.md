# Shell command conventions: detail

The always-on rule is in `~/.claude/CLAUDE.md`, "Shell command conventions" (moved here 2026-11-13, chezmoi chz-ae3).

## Full text

- **Avoid `sed` (and `awk`) for reading or editing files — use the Read and Edit tools instead.** `sed` is deliberately *not* added to permission allowlists, because Claude Code's prefix-based Bash matching cannot safely separate read-only `sed -n`/substitution from destructive in-place `sed -i`: flag combinations like `sed -ni` or `sed -n -i …` defeat any `sed -n`-style prefix pattern. So `sed` will always prompt, and an allowlisted `sed` would be a real footgun. Reserve `sed` for pipelines where it is genuinely necessary and no dedicated tool fits; never use it to view file sections (use Read with offset/limit) or to edit files (use Edit).
- The same caution applies to any tool whose read-only and destructive modes differ only by a flag that can be combined with allowed flags — prefer a purpose-built tool or leave it to prompt rather than allowlisting an unsafe prefix.
