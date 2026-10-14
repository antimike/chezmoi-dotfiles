---
name: ado-pr-draft
description: Drafting Azure DevOps Pull Request descriptions in plain Markdown with a YAML frontmatter scaffold. TRIGGER when drafting, composing, or editing a PR description for an Azure DevOps repo; when the user asks for "a PR draft" / "a PR body" in an ADO context; when touching files named `pr-draft.md` under `tasks/<bead>/deliverables/`. Codifies plain-Markdown body (not code-fenced), the 4000-char ADO description limit, YAML frontmatter shape (title, target/source branches, linked beads + Jira tickets, line/char counts), the no-source-side-line-wrapping rule (ADO renders wrapped), brevity over referential completeness, ASCII-only, the no-bead-refs-in-body rule, and the prefer-bulleted-over-inline-comma-lists rule.
author: Michael Haynes
scope: global
tags: [ado, azure-devops, pull-request, draft]
timestamps:
  - action: created
    at: 2026-05-19T21:00:00-05:00
    actor: Michael Haynes
  - action: edited
    at: 2026-05-19T22:00:00-05:00
    actor: Michael Haynes
    note: "Added rule 7 (prefer bulleted lists to inline comma-delimited lists) after observing the pattern emerge during PR drafting."
comments:
  - "Source: 2026-05-19 session. A blue-green deployment PR surfaced the need to formalize ADO-specific drafting conventions distinct from the Jira conventions skill."
  - "Distinct from `jira-conventions`: ADO has no ADF, no client-side mention resolution, a hard 4000-char description limit, and a UI that wraps lines (so source-side line-breaking is anti-helpful)."
related: [jira-conventions, "project CLAUDE.md External-Facing Writing section"]
---

# ADO PR Draft Conventions

Drafting conventions for Azure DevOps Pull Request descriptions. PR draft files live at `tasks/<bead-or-ticket>/deliverables/pr-draft.md`.

## Must-know rules

1. **Body is plain Markdown -- not a code-fenced chunk inside a larger draft document.** The body that ships to ADO is everything after the closing `---` frontmatter delimiter, verbatim. No surrounding commentary, no triple-backtick wrapper. If you need to leave drafter-only notes, put them in an HTML comment that is obviously stripped before posting (`<!-- draft-meta ... -->`), or in frontmatter.

2. **4000-character hard limit on the body.** ADO truncates beyond this. Frontmatter does not count. Track the live `char_count` in frontmatter and re-check on every edit.

3. **Do not line-break for readability.** ADO's renderer wraps paragraphs to available width. Source-side line breaks at ~80 columns produce broken paragraphs in the rendered output. Let paragraphs run; insert real blank lines only between distinct paragraphs.

4. **Brevity over referential completeness.** A terse, focused body beats an exhaustive one. Link to specs and decision docs in the repo rather than restating them. Trust the reader to follow.

5. **No bead references in the body.** Beads are internal-only. Reference the Jira tickets explicitly. Bead IDs can appear in frontmatter for the drafter's records.

6. **ASCII only.** No em-dashes (use `--`), no fancy quotes, no arrows (use `->` / `=>`), no section signs. ADO's reviewer tools handle ASCII without surprises.

7. **Prefer bulleted lists to inline comma-delimited lists.** Whenever you find yourself enumerating three or more items inline (especially the "X, Y, and Z" pattern), break them out into a bulleted list. ADO's renderer makes bulleted lists much easier to scan; inline lists buried in a paragraph get skimmed past. Applies wherever a list appears, including in section preambles and one-line sentences that introduce subsequent content.

   Bad:

   > Six runbooks covering production deploy, staging deploy, emergency slot flip, rollback, troubleshooting, and monitoring.

   Good:

   > Six runbooks covering:
   > - production deploy
   > - staging deploy
   > - emergency slot flip
   > - rollback
   > - troubleshooting
   > - monitoring

   Two-item lists (X and Y) stay inline.

## Frontmatter scaffold

```yaml
---
posted: false
posted_at: null
ado_pr_id: null
title: "<type>(<scope>): <summary> (<JIRA-KEY>)"
target_branch: main
source_branch: <user>/feat/<slug>
beads:
  - <bead-id>
jira:
  - <JIRA-KEY>
line_count: <int>     # body line count (after the closing frontmatter ---)
char_count: <int>     # body char count (NOT including frontmatter)
---
```

Update `line_count` and `char_count` after every body edit. They are the self-check that the 4000-char limit is respected and that a reviewer is not staring at a wall of text.

## Title conventions

Conventional-commits prefix with scope, Jira key in parens at end:

`feat(pipeline): blue-green deployment infrastructure (PROJ-16499)`

Match the first commit's subject line. ADO uses the PR title as the default merge commit subject for squash merges.

## Body structure (suggested, not mandated)

ADO does not enforce a template. A tight pattern for non-trivial PRs:

```
## Summary
One paragraph describing what this PR does and why. Let it flow; do not bulletize.

## Changes
- Brief enumeration of files / subsystems touched. Skip if diff is small.

## Testing
- What was run, what passed. One line each.

## Related
- PROJ-XXXXX
- docs/specs/<spec>.md
```

Skip any section that adds no value. A two-line description is fine for a one-commit fix.

## When to invoke this skill autonomously

- User asks for a PR draft, PR description, or PR body and the target is an ADO repo.
- User opens or edits a file named `pr-draft.md` under `tasks/.../deliverables/`.
- User mentions "ADO PR" or "Azure DevOps PR" in a drafting context.
- Pairs with: drafting a commit message that will become the PR title.

## When NOT to invoke

- GitHub PRs: ADO's quirks (4000-char limit, no source-side line wrapping) do not apply; GitHub's UI handles standard Markdown line breaks well.
- Jira issue or comment drafting: use the `jira-conventions` skill instead.
