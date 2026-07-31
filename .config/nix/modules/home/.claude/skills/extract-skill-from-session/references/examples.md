# extract-skill-from-session examples

Read this when a candidate sits near the extraction bar and you need a
calibration point for which side it falls on.

## Example 1 — 0 candidates (typical)

*Session summary*: user asked you to fix a flaky test; you read the test, found a race in the fixture, patched it, user confirmed.

*Output*:
> No reusable patterns worth extracting. The fix was specific to one test's fixture; debugging flaky tests in general is already within the `debug` skill.

## Example 2 — 1 candidate

*Session summary*: user had you run a multi-iteration prompt-tuning loop (baseline → dispatch subagents → evaluate both quantitatively and qualitatively → patch the skill → re-run) on a target skill. During the session the user repeatedly corrected you to keep scenarios fixed between iterations and to distinguish "material" from "periphery" unclear points.

*Output* (abbreviated):
> ### Candidate: iterative-skill-tightening
>
> **One-liner**: Run a tightening loop on an existing skill, dispatching fresh subagents each iteration and applying minimal edits between runs.
>
> **When to trigger**: use this when the user asks to "tune", "tighten", or "iterate on" a specific existing skill and already has a draft in hand.
>
> **Why it's worth extracting**:
> - During this session you repeatedly had to re-derive the loop structure (baseline → dispatch → evaluate → patch → re-run) from `empirical-prompt-tuning`'s generic description.
> - The same loop will apply to any user-owned skill the user wants to tighten.
>
> **Outline**:
> 1. Confirm the target skill and its current SKILL.md path.
> 2. Define 1–2 fixed evaluation scenarios with [critical] requirement checklists.
> 3. Dispatch fresh subagents on each scenario per iteration.
> 4. Apply one themed minimal edit between iterations; keep scenarios fixed.
> 5. Stop when critical requirements hit 100% twice and new unclear points are peripheral.
>
> **Checked against existing skills**:
> - `empirical-prompt-tuning`: not a duplicate — that skill is the general framework; this would be the applied recipe for tightening one specific existing skill, with the scenario/checklist ergonomics baked in.
>
> **Next step if you want it**: run `/skill-creator:skill-creator` with this proposal.

## Example 3 — candidate that fails the bar

*Session summary*: user had you debug a gnarly TypeScript generics issue involving conditional types and mapped types. Satisfying debugging session, lots of back-and-forth.

*Output*:
> No reusable patterns worth extracting. The debugging was valuable but project-specific (the fix depended on the exact type hierarchy in the codebase). `debug` already covers the general investigation pattern.
