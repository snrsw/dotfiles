---
name: maker-checker
description: Separate the agent that produces a change from the agent that verifies it, so no model grades its own work. Use before merging non-trivial or loop/agent-generated changes, when correctness matters and you would otherwise self-review, when you want an independent check of a diff against its spec, or whenever an automated loop produces code. The checker runs with fresh context and sees only the spec plus the artifact — never the maker's own justification.
---

# maker-checker

Split production from verification across two agents. A model that writes code and then judges its own work is biased toward declaring it correct — the failure loop-engineering warns about ("don't let the model grade its own work"), and a direct cause of false confidence. Hand the verification to a separate agent with fresh context.

## When to use

- Before merging any non-trivial change, especially one an automated loop or agent produced.
- When correctness matters and the only reviewer would otherwise be the author (you, a subagent, or codex).
- When a PR needs an independent read against its stated intent, not just "looks fine".

Skip it for trivial, obviously-correct changes (a rename, a doc typo) — the overhead is not worth it there.

## The two roles

**Maker** — produces the change.
- Writes the code and its tests (via `tdd`).
- States the spec in one or two sentences: what should be true after this change, and how to tell.
- Hands the checker the spec + the diff. Does *not* hand over its own reasoning about why it is correct.

**Checker** — a *separate* agent, fresh context.
- Receives only: the spec, the diff/artifact, and the test command. Not the maker's self-justification — that is exactly what biases a self-review.
- Verifies the artifact against the spec: does it actually do what was promised, including edge cases the maker may have skipped?
- Runs the AI-PR failure-mode checks (delegate to `pr-dependency-review`'s `references/ai-pr-checks.md`): weakened CI, hallucinated correctness, reinvented utilities, phantom imports, scope creep, comprehension debt.
- Tries to break it. Returns a verdict (pass / fail) + concrete findings with file:line.

## The loop

1. Maker produces change + tests + a one-sentence spec.
2. Dispatch the checker with fresh context (see Dispatch below).
3. Checker returns verdict + findings.
4. If fail: maker addresses findings, then re-check. Keep the spec fixed between rounds.
5. Stop when the checker passes — then a **human** owns the merge. The checker reduces, it does not remove, "verification is on you".
6. If maker and checker still disagree after two rounds, escalate to the human (a DR if it is a protected domain).

## Dispatch (fresh context is the point)

Run the checker as a separate agent, not a second pass in the same thread:

- **Subagent** via the `Agent` tool — purpose-built reviewers exist: `pr-review-toolkit:code-reviewer`, `silent-failure-hunter`, `pr-test-analyzer`, `type-design-analyzer`, or `general-purpose` with a fresh review prompt. Pass it the spec + diff and instruct: "verify against this spec; do not assume the author was right."
- **codex** (`codex review` / `codex exec review`) as an independent second engine — useful when the maker was Claude, so the checker is a different model entirely.

Never let the agent that wrote the code be the one that signs off on it.

## Integration

- **tdd** — the maker writes failing tests first; the checker confirms a test fails on the pre-change behavior (catches hallucinated correctness).
- **pr-dependency-review** — supplies the checker's structural/complexity analysis and AI-PR checks.
- **loop-automation** — maker-checker is the verification gate between a loop's iterations.
- **loop-state** — record each check's verdict in `## Notes`; a failed check becomes a `## Next` item.
- **debug** — when the checker finds a real defect, switch to `debug` to fix it.
- **DR pattern** — maker/checker disagreement on a protected domain escalates as a DR.
