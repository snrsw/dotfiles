---
name: document-style
description: Document structure and writing standards for any prose document — design docs, READMEs, proposals, articles, reports, explanations, wikis. Use whenever writing or revising a document, even if the user just says "write a doc", "write up X", "explain X", "draft a proposal", or "document this". Covers top-down structure, argument ordering, paragraph and sentence discipline, vocabulary, lists and hierarchy, references, figures, and examples. Language-agnostic — apply to English and Japanese documents alike.
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

Attach an example to every important definition, problem, and solution. Examples are never optional decoration: a rule the reader cannot instantiate is a rule they have not understood.

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

Repeat the same word for the same concept. Do not rotate synonyms for aesthetic variety — every new word forces the reader to check whether it means something new. Once a term is defined, keep using that exact term.

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

## Checklist for Revision

- [ ] The opening states the subject, the motivation, and the key conclusion before any detail
- [ ] Truncating at any section boundary leaves a non-misleading document
- [ ] Order: problem awareness → definitions → formalized problem → solution
- [ ] Every important definition, problem, and solution has an example
- [ ] Each paragraph's first sentence announces its topic
- [ ] Each sentence carries one meaning
- [ ] The same term is used for the same concept throughout
- [ ] Facts and speculation are explicitly distinguished
- [ ] Parallel items are bullet lists; hierarchical content is nested structure
- [ ] No back-jumps: earlier content needed later is restated inline
- [ ] References are linked inline at the point of use
- [ ] Figures are used where structure or flow beats prose

## Related Skills

- `japanese-technical-writing` — Japanese-specific manuscript rules (formatting, phrasing, banned filler expressions). Apply both when writing Japanese manuscripts.
