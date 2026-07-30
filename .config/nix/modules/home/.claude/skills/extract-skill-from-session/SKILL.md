---
name: extract-skill-from-session
description: Analyze the current session to find work worth extracting as a new skill. Invoke at session end — typically after substantial multi-step work — to produce a proposal (name, description, triggers, outline, rationale) for review; it never creates files. Applies a strict extraction bar and says plainly when nothing qualifies.
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
- The session merely "felt productive". Productivity ≠ generalizability — ask whether a different person on a different project would follow the same steps.
- A candidate that barely clears the bar, or this skill itself. Report 0 instead of padding.

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

## Response style

A proposal is a decision aid — the user reads it to decide yes or no. The
`response-style` rule applies to the prose inside the format above.

- **The one-liner is the conclusion.** A reader who stops there should know what
  the skill does and be able to decide whether to keep reading.
- **Separate fact from speculation, per bullet.** "During this session you did X"
  is an observation — state it unhedged. The generalization ("this will also apply
  to …") is a prediction — mark it as one. The bar depends on the reader being able
  to tell these apart.
- **One meaning per bullet.** A reason that carries both an observation and a
  prediction gets split into two.
- **Plain words.** Do not dress a thin candidate in impressive phrasing; the strict
  bar only works if the proposal reads as plainly as the evidence supports.

## When 0 candidates is the right answer

Often the session just used existing tools and skills to solve one specific problem. That is fine. Output should be one sentence:

> No reusable patterns worth extracting. The work in this session was either project-specific, already covered by existing skills, or a one-off.

Do not pad with apologies or suggestions for future sessions. Silence on 0 is part of the skill's value.

## Examples

See `references/examples.md` — a typical 0-candidate session, a 1-candidate
session, and a candidate that fails the bar.

## Related

- `skill-creator` — actually produces the SKILL.md files. This skill hands off to that one, it does not replace it.
- `empirical-prompt-tuning` — for tightening a skill after it exists. Runs after skill-creator, not before.
- The user's memory system — for session-specific facts, preferences, and corrections. Not for procedures.
