# Jira Comment Style Guide

Voice and structure preferences for Jira comments (analysis, findings, status updates).

## Analysis / findings comments

1. **Lead with context and methodology** before presenting findings. Don't assume the reader knows the tools or process — introduce what was done, link to scripts/tools at first mention, and describe the approach briefly.

2. **Integrate document/resource links into narrative prose** rather than as standalone lines or a header block. The reader should encounter them naturally while reading.

3. **Connect findings to the team's recent shared context** (e.g., "mostly in line with the fixes we implemented on Friday"). Anchor results in something the audience already knows rather than presenting in a vacuum.

4. **Separate questions from proposed solutions** using sub-bullets. Keep the ask on the main bullet; put "if so, here's how we'd handle it" on an indented sub-bullet. Cleaner for the reader to distinguish what they need to answer vs. what's already been thought through.

5. **Do NOT include "Next steps" sections** in analysis/findings comments. Comments should report findings and ask questions, not prescribe follow-up actions. Next steps belong in separate tickets or are for the reader to decide.

6. **Backtick all tool/executable names** — `schemachange`, `SqlPackage`, `terraform`, `msbuild`, etc. should always be in backticks, not bare text.

## Status update comments

Progress updates on deliverables have different norms — they can be more direct and transactional. Numbered deliverables with per-item progress notes work well. Don't try to impose the analysis-comment structure on routine status posts.

## Voice and tone (applies to both kinds)

These calibrate the prose toward how Mike actually writes to teammates, rather than the patient-explainer default. They're not absolute rules — break any of them when the content demands it — but defaulting to them produces drafts that need less rewriting.

1. **Trust the recipient's domain expertise.** Default to the technical vocabulary they use daily (DML, DDL, MERGE, dynamic table, declarative state, the actual role / schema / object names). Don't gloss terms the recipient defines for a living. The audience is teammates, not students.

2. **Lead with mechanism, not metaphor.** When explaining *why* something is being asked or done, name the actual system or process driving it ("implementing declarative Terraform state for all Snowflake environments") rather than a soft narrative ("tidying things up", "papering over", "no surprises").

3. **Use contractions.** Default to *hasn't / isn't / I'm / doesn't / can't*. Reserve uncontracted forms for emphasis. A draft with zero contractions almost always reads as someone-else's-voice.

4. **Prefer alternatives over reassurances.** Instead of "no rush" or "detail level is up to you", offer a different *shape* the answer can take that lowers the recipient's cost (e.g., "alternatively, if you can give me the list of workspaces/notebooks, I can derive the rest"). Cap reassurance moves at **one** per message; two or more stacked ("no rush" + "happy to defer" + "let me know if it's easier verbally") read as anxious.

5. **End direct asks with a binary question.** "Can you confirm I can DROP this proc?" not "is the dynamic table the path going forward?" When a yes/no answer is what unblocks the work, ask for one.

6. **Bold the lead clause of the message and the key alternative offer** so a scanner can absorb the spine in one pass. Don't bold defensively (every list label, every term of art); reserve bold for the two or three nodes a scanning reader must hit.

7. **Long sentences must earn their length with information density.** A 60-word sentence is fine if every clause adds a constraint. If the middle clauses restate the topic or hedge a previous clause, split or cut.

8. **Drop "Quick context:" / "Concretely," / "Specifically," as section scaffolding.** Use them as logical pivots only, not as transition glue. If a paragraph would still flow with the label removed, the label is decorative.

## Applying the guidance

Before finalizing any draft, classify it (analysis vs. status update) and apply the corresponding structural rules. Then make a voice pass against the section above. Universal: lead with "what did we do and how" before "what did we find."
