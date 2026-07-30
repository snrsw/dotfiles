---
name: tdd
description: Guide development following Kent Beck's Test-Driven Development (TDD) using Red → Green → Refactor cycle. Use when writing tests first, implementing features with TDD, need to write failing tests, make tests pass, refactoring after tests pass, following red-green-refactor, fixing defects with tests, or practicing test-driven development methodology.
---

# Test-Driven Development (TDD)

Follow Kent Beck's Red → Green → Refactor cycle:

1. **Red** — write the simplest failing test that defines a small increment of
   functionality, one test at a time, with a name that describes the behavior.
2. **Green** — write just enough code to make it pass, no more.
3. **Refactor** — improve structure only while green, one refactoring at a
   time, running all tests (except long-running ones) after each step.

Repeat until the feature is complete.

## Defect fixing

When fixing a defect:

1. First write an API-level failing test (exercises only the public contract
   the caller sees).
2. Then write the smallest possible test that replicates the problem — the
   minimum inputs and minimum assertion surface that still pin the defect.
3. Get both tests to pass.

If the fix requires a signature change (e.g., adding an `error` return),
updating pre-existing tests to the new contract is a mechanical migration, not
a forbidden refactor — preserve their behavioral assertions verbatim while
adapting call sites.

## Commits

Format via `commit-message`. The commit gate — when a change may be committed,
and why a standalone Red (failing) test never is — is owned by `tidy-first`:
one completed Red → Green → Refactor cycle is one behavioral commit.
