---
name: document-style
description: Document structure and writing standards for any prose document — design docs, READMEs, proposals, articles, reports, explanations, wikis. Use whenever writing or revising a document, even if the user just says "write a doc", "write up X", "explain X", "draft a proposal", or "document this". Covers top-down structure, argument ordering, paragraph and sentence discipline, vocabulary, lists and hierarchy, tables, references, figures, and examples. Language-agnostic — apply to English and Japanese documents alike.
---

# Document Style

## Overview

A document is read top-down, once, often under time pressure. Structure it so the reader always holds the big picture, and can stop reading at any point without losing the most important ideas. Every rule below serves one goal: spend the writer's effort to save the reader's.

## When to Use

- Writing any prose document: design docs, READMEs, proposals, articles, reports, explanations
- Revising or reviewing a draft of such a document
- For Japanese manuscript prose (books, chapters, articles), ALSO apply `japanese-technical-writing` — it adds Japanese-specific formatting and phrasing rules on top of this skill

## Top-Down Structure

Show the whole picture before any detail. Open the document with what it is about, why it matters, and the key conclusion. Then let each section descend one level deeper.

Detail must only increase as the document proceeds. A reader who stops halfway still knows the overview and the important points. Test a draft by truncating it at each section boundary: if the truncated version misleads, or omits a conclusion stated only later, move that conclusion earlier.

Mirror the content's structure in the document's structure. If the content has hierarchy, make it visible — nest sections, or nest bullets. Do not flatten a real hierarchy into running prose, and do not invent nesting the content does not have.

## Argument Order

Present material in this order:

1. **Problem awareness** — why the reader should care; what hurts today.
2. **Definitions** — introduce the terms needed to state the problem precisely.
3. **Problem statement** — formalize the problem using exactly those terms.
4. **Solution** — address the problem as formalized.

Attach an example to every important definition, problem, and solution. Examples are never optional decoration: a rule the reader cannot instantiate is a rule they have not understood. When you cannot exemplify everything, attach the example to what the reader will use first — an API doc that exemplifies a rarely-used endpoint but not the one every client integrates first has its examples backwards.

Use a figure wherever it explains structure or flow better than prose — architecture, sequences, state transitions, data flow. A reader parses in seconds a diagram that prose would take paragraphs to serialize.

## Paragraphs and Sentences

Write in paragraphs by default. Open each paragraph by stating what it will discuss and why it matters; the rest of the paragraph delivers exactly that. A reader skimming only first sentences should still be able to follow the argument.

Give each sentence one meaning. When a sentence carries two claims, split it. A period tells the reader: digest this before moving on.

Use punctuation deliberately to control the reader's load:

- A comma separates items within one thought and marks a small pause — a breath when read aloud.
- A period closes a thought completely — a full stop when read aloud.
- When one sentence enumerates several items, make the boundaries explicit with commas, or promote the enumeration to a bullet list.

Punctuation sets the reader's rhythm. Reading a passage aloud is a fast test of whether the pauses fall where the reader needs them.

## Vocabulary

Use plain words. Prefer the everyday term over the impressive one; the reader's energy should go to the content, not the phrasing.

Repeat the same word for the same concept. Do not rotate synonyms for aesthetic variety — every new word forces the reader to check whether it means something new. Once a term is defined, keep using that exact term. This holds across every representation: prose, tables, figures, headings, and identifiers must all carry the one term — a section named "Appendix" in one place and its translation in another reads as two different things.

Do not coin a name for a concept the document uses only once; state the idea plainly. Introduce a name only when the document will refer back to it.

State things concisely, without decoration. Delete sentences that only build atmosphere.

Separate fact from speculation explicitly. Mark inference as inference, and keep verified statements unhedged. The reader must never have to guess which of the two they are reading.

**Example:**

> Bad: "The service leverages a sophisticated caching layer, which is why latency is excellent."
>
> Good: "The service caches responses in Redis (`cache.go`). We have not profiled it, but we expect this caching is why p99 latency stays under 10 ms."

The bad version decorates ("leverages", "sophisticated", "excellent") and states a guess as fact. The good version uses plain words, cites the source inline, and labels the causal claim as expectation.

## Lists, Hierarchy, and References

Use a bullet list for parallel items. Three parallel clauses jammed into one sentence hide their structure; a list shows it. Nest bullets when the items themselves have sub-structure.

Never force the reader to jump back. If a point depends on something from an earlier section, restate the needed piece inline in one clause — "the invariant from the Ownership section (every job has exactly one owner)" — so reading continues forward. A bare back-reference is a pointer the reader must dereference by scrolling.

Link references inline where they are used, not only in a final list. A closing "References" section is useful as an index, but the sentence that depends on a source should carry the link itself.

**Example:**

> Bad: "This follows the approach described in [3]." (reader must scroll to find [3])
>
> Good: "This follows the [circuit breaker pattern](https://martinfowler.com/bliki/CircuitBreaker.html), also listed in References."

## Tables

A table is parallel structure in grid form, and each column is a promise: it holds one kind of content for every row. Put reasons only in the reason column and outcomes only in the outcome column — a reason smuggled into the outcome cell breaks the reader's scan. When a column holds statuses or verdicts, draw its values from a small closed set, and use each value with one meaning.

A table that summarizes prose must agree with that prose. Readers skim tables first and trust them over the surrounding text, so a row that contradicts the prose plants the wrong fact even when the prose is correct.

**Example:**

> Bad: a status column containing "sent / declined / future work / done (needs adjustment)" — ad-hoc labels, one of them self-contradictory.
>
> Good: a status column limited to "adopted / declined / deferred / out of scope", with the nuance ("adopted; format under discussion") in a notes column.

## Checklist for Revision

- [ ] The opening states the subject, the motivation, and the key conclusion before any detail
- [ ] Truncating at any section boundary leaves a non-misleading document
- [ ] Order: problem awareness → definitions → formalized problem → solution
- [ ] Every important definition, problem, and solution has an example
- [ ] Each paragraph's first sentence announces its topic
- [ ] Each sentence carries one meaning
- [ ] The same term is used for the same concept throughout — in prose, tables, figures, and headings alike
- [ ] No coined terms that appear only once
- [ ] Facts and speculation are explicitly distinguished
- [ ] Parallel items are bullet lists; hierarchical content is nested structure
- [ ] Each table column holds one kind of content; status columns use a small closed set of values; tables agree with the prose
- [ ] No back-jumps: earlier content needed later is restated inline
- [ ] References are linked inline at the point of use
- [ ] Figures are used where structure or flow beats prose

## Verification Loop

The checklist above is a single-pass tool. When the document is high-stakes — external or client-facing, or the user asks for a verified result ("verified", "loop until it passes") — run this scored loop instead, and offer it proactively when the stakes warrant it. Default usage stays single-pass; the loop costs one review subagent plus one revise subagent per round.

Roles are separated so no agent grades its own work: the main session orchestrates; a **fresh subagent** reviews each round (never a previous reviewer, never the reviser); a **separate subagent** revises. The reviewer never fixes, and the reviser never scores.

Each round:

1. **Review.** Dispatch a fresh reviewer with this skill file and the document. It scores EVERY item of the Checklist for Revision and ends its reply with exactly one fenced json block:

   ```json
   {"policies": [{"policy": "<checklist item>", "score": 0-100, "confidence": 0-1,
     "reason": "...",
     "issues": [{"issue": "...", "quote": "<verbatim offending text>",
                 "severity": "critical|high|medium|low", "confidence": 0-1, "fix": "..."}]}]}
   ```

   Parse the final fenced json block of the reply. On parse failure, re-ask once ("return only the json block"); on a second failure, treat the round as failed and stop.

2. **Anchor the scores — no vibes.** Each policy starts at 100 and deducts per issue: critical −30, high −15, medium −8, low −3. A reviewer that deviates states why in `reason`. This makes ≥ 80 mean something concrete: no critical/high issue, at most minor nits.

3. **Gates a score cannot buy back.** In a revision, any lost or altered technical fact is an automatic `critical` issue, whatever the style quality. The loop exits only when BOTH hold: every policy scores ≥ 80 AND no confirmed critical/high issue remains.

4. **Refute before fixing.** For each critical/high issue with confidence < 0.7, dispatch a fresh subagent to REFUTE it ("assume this may be wrong; default to not confirmed"). Only confirmed issues drive fixes — this stops the loop from chasing a hallucinated issue.

5. **Fix and re-review.** A reviser subagent applies the remaining issues, locating each by its `quote` and preserving every technical fact. The next round starts with a FRESH reviewer.

**MAX_ROUNDS = 3.** If the cap is hit with a policy still below 80, stop and report the residual policies and issues to the user instead of looping — a stuck policy is a decision for the user, not fuel for iteration.

## Related Skills

- `japanese-technical-writing` — Japanese-specific manuscript rules (formatting, phrasing, banned filler expressions). Apply both when writing Japanese manuscripts.
- `response-style` rule (`.claude/rules/response-style.md`) — the always-on, response-scale subset of this skill; it applies to every output, not only documents. When editing the sentence-level, vocabulary, or table rules here, update the rule to match.
