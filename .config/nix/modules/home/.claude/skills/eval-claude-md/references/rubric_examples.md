# Good and bad rubric checks

A rubric check is reliable when two graders applying it to the same response
reach the same verdict. Subjective checks fail this test and produce noise.

## Bad: subjective

- "Is the response well-written?"
- "Does Claude sound like a senior engineer?"
- "Is the code style good?"
- "Did Claude do a good job pushing back?"

These cannot be graded reliably. Different runs of the same judge will
disagree. Rewrite into a concrete behavior the response either does or
doesn't show.

## Good: binary, observable

- "Does the first non-empty line begin with `**Rewritten**:`?"
- "Does the response contain at least one `def test_` function before any
  non-test `def`?"
- "Does the response include the literal substring 'Plan:' before any code
  block?"
- "Does the response ask the user a clarifying question before writing any
  implementation code?"
- "In the largest code block, what fraction of variable bindings are `const`
  (or analogous) — is it ≥ 80%?"

These have clear pass/fail outcomes. The judge prompt can ask "yes or no"
and get a stable answer.

## Borderline: works with care

- "Does the response use `map`/`filter`/`reduce` instead of `for` loops?"
  — Fine if you specify "in code blocks longer than 3 lines" and "not
  counting imports or one-liner ranges."

- "Does Claude push back on the user's incorrect premise?"
  — Needs the prompt to *plant* an incorrect premise. Without that, the
  check isn't well-defined.

- "Does the response stay under 200 words?"
  — Easy to grade, but ask whether word count is what you actually want to
  measure. Often a proxy for "concise" — and "concise" deserves a sharper
  rubric.

## The pattern

The more constraints you add to a check, the more reliably it grades. Start
with a vague intent, then ask "what would I look at in the response to know
the rule was followed?" Whatever you'd point at — a specific phrase, a
specific structure, a specific count — that's the rubric.

If you can't point at anything specific, the rule is too vague to evaluate.
See `methodology.md` for what to do then.
