# Response Style

Apply these standards to EVERY output — chat replies, summaries, explanations, review comments, commit messages, PR text — not only documents. They are the response-scale subset of the `document-style` skill. When writing a full document (design doc, README, proposal, article, report), invoke that skill: it adds the doc-scale rules (argument order, truncation test, figures and references, the scored verification loop).

Language-agnostic — apply to English and Japanese output alike.

## Structure

- Lead with the conclusion. The first sentence answers the question or states the outcome; detail only increases as the text proceeds.
- Mirror the content's structure. Parallel items become a bullet list; real hierarchy becomes nested structure. Do not flatten a real hierarchy into running prose, and do not invent nesting the content does not have.
- Never force a back-jump. If a point depends on something said earlier, restate the needed piece inline in one clause instead of pointing at it.

## Sentences

- Give each sentence one meaning. When a sentence carries two claims, split it.
- Use plain words. Prefer the everyday term over the impressive one; delete sentences that only build atmosphere.
- Repeat the same word for the same concept — no synonym rotation. Do not coin a name for a concept used only once.
- Separate fact from speculation explicitly. Mark inference as inference ("I expect", "not verified"); keep verified statements unhedged.

## Tables

- Each column holds one kind of content — reasons in the reason column, outcomes in the outcome column.
- Status or verdict columns draw from a small closed set of values, each used with one meaning.
- A table must agree with the surrounding prose; readers skim tables first and trust them over the text.

## Where this is restated

Skills that hand over a **fixed output template** restate these rules inline,
specialized to that artifact: a concrete template competes with this background
rule at the moment of writing, and measurement (2026-07-30, executor A/B runs
logged in the dotfiles decisions.md) showed compliance drops ~11 points without
the restatement. Skills whose deliverable is free-form prose (a report, a
verdict) carry no restatement — the same measurement showed this rule alone
holds there.

Editing the sentence, vocabulary, or table rules above means checking these for drift:

| Skill | Output it governs |
|---|---|
| `pr-body` | PR body prose inside the fixed format |
| `commit-message` | commit subject line and body |
| `pr-dependency-review` | the review comment, its tables and diagram labels |
| `issue-resolver` | scored-review strings and the closing report |
| `issue-loop` | the batch summary table |
| `plan-state` | `plan.md` |
| `extract-skill-from-session` | skill proposals |
| `replay-prompt` | the distilled prompt |
| `document-style` | full prose documents; adds the doc-scale rules |
| `japanese-technical-writing` | Japanese manuscripts; adds Japanese-specific rules |
