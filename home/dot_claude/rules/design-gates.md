# Design gates: prior art, scope, decide before building

Always loaded (no `paths:`): these gates apply before any design work, in every project. Source: chezmoi D81 (2026-11-19; client rule amended 2026-11-25), from the 2026-11 repo reviews. Why: implementation is cheap with an assistant, so effort no longer brakes scope; the reviews found subsystems with no client, home-built tools where existing ones fit, and decisions confirmed after they were built.

## Prior-art gate

- Before designing any new tool, subsystem, service or framework, write a **prior-art entry** in the project's decision log or design doc: the existing tools that could do the job, and for each, the **specific requirement it fails** (tested, or quoted from its docs; say which). "Ours would be cleaner" is not a failed requirement.
- **Installing a tested tool is the default.** Building wins only when every candidate fails a stated requirement. Model: the tracker research in chezmoi `docs/plans/issue-tracker.md` (D80).
- **Recommend existing tools proactively**, even when MH asked for a build, and offer further research (a timeboxed survey or a hands-on trial) when the field is unclear. Read each tool's own docs and test its documented workflow before rejecting it.

## Scope-creep rule

- **No subsystem ships without a real client in the same release**: a caller that exists and is used, or a **named use**: MH, or another project's ticket, saying "I would use this for X", or a named person (usually MH) who says they will run the command at the terminal. A hypothetical user is not a client.
- **A feature shipped for a named use is experimental, with a review date** (in its help or docs, and in its bead), and is kept or removed after real use (model: amontillado amo-0k6.8). Named uses must not pile up unused features.
- **Announce before building**: when a feature's consumer lives in another project, put the interface in the design doc and file it to the consumer as a ticket (`triage-file`) before the build. The consumer commits to the same release, or the consumer-facing part waits.
- **Infrastructure keeps the strict rule**: generic runners, plugin systems, engines and abstractions over one case are extracted from two or three concrete uses, not designed ahead of them. A named use does not count for them.
- **Flag unrequested infrastructure aggressively**: plugin systems, engines, generic runners, logs, caches, abstractions over one case. Say so before writing it, and weigh it against the current priorities (chezmoi D50: job search first). Directness over diplomacy.
- Prefer the smallest change that serves today's client; note the generalisation as an open item instead of building it.

## Decide before building

- A decision that shapes a design (a D-number, a new component, a dependency) is **confirmed by MH before implementation starts**, not recorded as "Claude's call, confirmed" afterwards. Batch the open questions, ask, then build.
- If implementation shows a confirmed decision was wrong, stop and re-raise it; do not quietly build around it.

## Review gates

- Run `/project-review` (fresh context, cold read, adversarial brief) at two gates: **before a design is accepted** and **before a release adds a subsystem**. Not routinely otherwise.
- It reports numbers, not ratings. It is still Claude reviewing Claude: one human skim and real adoption are the better checks.
