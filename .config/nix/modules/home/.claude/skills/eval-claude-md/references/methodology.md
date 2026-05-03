# Operationalizing vague rules

A rule like "follow Kent Beck's TDD principles" cannot be evaluated as written.
Before the eval can proceed, the rule needs to be operationalized into a
binary, observable check. This page is the reference for doing that.

## Pattern: vague → operational

| Vague rule | Operational form |
|---|---|
| "Be a positive partner" | "When the prompt contains a planted flaw, does the response point it out before complying?" — requires planted-flaw prompts |
| "Follow TDD" | "When asked to implement a function, does the response write a failing test before any production code?" |
| "Avoid mutation" | "In code blocks ≥ 5 lines, what fraction of variable bindings are immutable (`const`/`let`/`val`/`final`) vs mutable?" — language-specific threshold |
| "Propose a plan first" | "Does the response present a numbered/bulleted plan and explicitly request approval before producing implementation code?" |
| "Use functional style" | "Does the response use map/filter/reduce or pipelines for collection transformations longer than 3 lines, instead of imperative for-loops?" |

## When to refuse to evaluate

If every reasonable rubric is subjective — e.g., "Be a positive partner" with
no way to plant a testable flaw — that's a finding in itself. Surface it to
the user:

> "This rule can't be operationalized as written. Either we leave it
> unmeasured (and its presence in CLAUDE.md is unverifiable), or we rewrite
> it to a more concrete behavior. Which?"

A rule that can't be measured probably can't be reliably followed either.
Rewriting it is usually the right call, and the eval was the catalyst.

## Triggers vs rubric

These two fields in `rules.yaml` are easy to conflate. The split:

- **triggers**: when does the rule apply? Used to author the on-target /
  off-target prompt sets. Answer: "what kind of user prompt should make this
  rule fire?"
- **rubric**: given that the rule applied, was it followed? Used by the judge.
  Answer: "what does the response look like when the rule was followed
  correctly?"

If a rule fires on every turn (e.g., a global "always do X" rule), there's no
meaningful off-target set. Note that explicitly in `triggers` and skip the
off-target prompts.

## On-target prompt design

Aim for variety, not just paraphrases. A 10-prompt set should cover:

- 2–3 phrasings of the most common case
- 2–3 edge cases at the boundary of the trigger condition
- 2–3 cases mixing the rule's domain with adjacent ones (does it still fire?)
- 1–2 cases where the rule applies but not obviously (the model has to think)

If all 10 prompts are paraphrases of the same idea, the eval measures only
robustness to paraphrasing, not generality.

## Off-target prompt design

Hard rule: off-target prompts must be **plausible adjacent**. Random unrelated
prompts ("write a fibonacci function" for a CLAUDE.md communication rule)
test nothing — Claude will obviously not apply the rule there, but that
proves nothing about its trigger discipline.

Good off-target prompts share keywords, structure, or domain with on-target
ones, but require behavior the rule should *not* impose. They test whether
the rule's trigger conditions are sharp enough to avoid bleed.
