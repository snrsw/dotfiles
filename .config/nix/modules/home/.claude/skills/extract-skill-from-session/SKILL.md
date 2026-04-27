---
name: extract-skill-from-session
description: Analyze the current session to find work that can be generalized and extracted as a new skill. Invoke at the end of a session — typically after completing substantial multi-step work — to produce a proposal (name, description, triggers, outline, rationale) for a candidate skill. This skill does NOT create files; it only produces proposals for review. Apply a strict bar: propose only patterns that are clearly multi-step, reusable across projects, not already covered by existing skills, and stable enough that a teammate doing the same task would follow the same procedure. If nothing qualifies, say so plainly rather than force a proposal.
---

# extract-skill-from-session

Reflect on the session and decide whether any work done is worth codifying as a new skill. Produce a proposal, not a file. The proposal is input for the user to then (optionally) run `/skill-creator` or hand to an agent.

## Why this skill exists

Reusable patterns are easy to notice in the moment and easy to forget five minutes later. At session end, the patterns are fresh but the trigger to write them down has passed — the task is done and attention moves on. This skill creates the trigger: invoke it, get an audit of what in this session might generalize, and decide cheaply whether it's worth codifying.

The default bias is **toward not creating a skill**. A bad skill is worse than a missing one: it clutters the skill list, mis-triggers on adjacent tasks, and adds maintenance burden. Propose only patterns where the payoff is obvious.

## Workflow

1. **Inventory the session**. Look at the conversation: what did the user ask for, what workflows did you execute, what corrections did they make, what did you get wrong and then fix? Write a short mental list — not for the user, just to ground the analysis.
2. **Filter against the extraction bar** (next section). Most sessions produce 0 candidates. Some produce 1. Producing 2+ is rare — if you're finding many, you're being too loose.
3. **For each surviving candidate, draft a proposal** using the proposal format below. Include the negative check: name existing skills you considered and ruled out as duplicates.
4. **Present to the user**. If 0 candidates: say so in one sentence and stop. If 1+: show proposals and ask which (if any) to pursue.
5. **Stop.** Do not invoke `/skill-creator` or write any SKILL.md. The user runs that separately if they decide to go ahead.

## Extraction bar (strict)

A candidate must clear **all** of these:

- **Multi-step**. One tool call or one obvious prompt is not a skill. There has to be a sequence where the order, or the judgment between steps, matters.
- **Reusable across projects**. If the steps only make sense inside this specific codebase or company, it is not a skill — it belongs in `CLAUDE.md` or memory.
- **Stable**. The user did not visibly change their mind about the approach mid-session. If the workflow you're eyeing is the third version after two failed attempts, wait until it has been used again in a later session.
- **Clear trigger conditions**. You can write, in one sentence, "use this when the user …". Vague triggers produce vague skills.
- **Not already covered**. Check the installed skills. If an existing skill covers 80%+ of this workflow, propose extending that skill instead of creating a new one.
- **Non-trivial enough to be worth consulting**. If Claude would solve the task fine from a 1-line prompt without the skill, the skill adds nothing.

A candidate that fails any one of these does not get proposed.

### Positive indicators (raise confidence)

- The user corrected Claude's initial approach and the correction is generalizable.
- The sequence took real effort to figure out — subagent searches, back-and-forth, dead ends.
- You can imagine a different user on a different project benefiting from the same procedure.
- The user said something like "we always do X this way" or "remember to do Y before Z".

### Negative indicators (rule out)

- Content/knowledge rather than procedure. Belongs in memory or `CLAUDE.md`.
- Project-specific deployment steps, internal URLs, team conventions.
- A one-time migration or investigation.
- Something trivially obvious in hindsight — the effort was in the debugging, not the procedure.
- Work that is already implicitly handled by default tool behavior.

## Proposal format

For each candidate, output exactly this structure:

```
### Candidate: <proposed-skill-name>

**One-liner**: <what the skill does, in one sentence>

**When to trigger**: <one sentence — "use this when the user …">

**Why it's worth extracting**:
- <reason 1, grounded in this session — "during this session you did X and had to …">
- <reason 2 — the generalization claim — "this will also apply to …">

**Outline** (3–6 steps):
1. …
2. …
3. …

**Checked against existing skills**:
- <existing-skill-1>: not a duplicate because …
- <existing-skill-2>: not a duplicate because …
(List only skills that plausibly overlap — do not enumerate all installed skills.)

**Next step if you want it**:
Run `/skill-creator:skill-creator` and paste this proposal as the starting prompt.
```

## When 0 candidates is the right answer

Often the session just used existing tools and skills to solve one specific problem. That is fine. Output should be one sentence:

> No reusable patterns worth extracting. The work in this session was either project-specific, already covered by existing skills, or a one-off.

Do not pad with apologies or suggestions for future sessions. Silence on 0 is part of the skill's value.

## Anti-patterns

- **Proposing a skill because the session "felt productive"**. Productivity ≠ generalizability. The question is "would a different person on a different project follow these same steps?" — not "did this work?"
- **Proposing a skill that is really a memory**. If the output is facts about the user, their project, their preferences — save to memory. Skills are procedures.
- **Padding to reach a proposal**. If the candidate barely clears the bar, it does not clear the bar. Report 0 instead.
- **Duplicating an existing skill with a different name**. Always scan the installed skill list first. If 80%+ overlap exists, the proposal is "extend skill X", not "create new skill Y".
- **Proposing the skill you are currently running**. This skill is not a candidate for itself.

## Examples

### Example 1 — 0 candidates (typical)

*Session summary*: user asked you to fix a flaky test; you read the test, found a race in the fixture, patched it, user confirmed.

*Output*:
> No reusable patterns worth extracting. The fix was specific to one test's fixture; debugging flaky tests in general is already within the `debug` skill.

### Example 2 — 1 candidate

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

### Example 3 — candidate that fails the bar

*Session summary*: user had you debug a gnarly TypeScript generics issue involving conditional types and mapped types. Satisfying debugging session, lots of back-and-forth.

*Output*:
> No reusable patterns worth extracting. The debugging was valuable but project-specific (the fix depended on the exact type hierarchy in the codebase). `debug` already covers the general investigation pattern.

## Related

- `skill-creator` — actually produces the SKILL.md files. This skill hands off to that one, it does not replace it.
- `empirical-prompt-tuning` — for tightening a skill after it exists. Runs after skill-creator, not before.
- The user's memory system — for session-specific facts, preferences, and corrections. Not for procedures.
