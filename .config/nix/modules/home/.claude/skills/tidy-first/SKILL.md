---
name: tidy-first
description: Follow Kent Beck's Tidy First principles by strictly separating structural changes from behavioral changes. Use when refactoring code, restructuring code, making structural changes without changing behavior, renaming variables/functions, extracting methods, separating concerns, preparing code for new features, or need to ensure structural and behavioral changes are in separate commits.
---

# tidy-first

Follow Kent Beck's "Tidy First" approach: strictly separate structural changes
from behavioral changes.

## Core principle

- **Structural changes** rearrange code without changing behavior: rename,
  extract method/class, move code, reorganize.
- **Behavioral changes** add or modify functionality: features, bug fixes,
  business-logic changes.

**Never mix the two in the same PR.** Each PR — and each commit inside it — is
purely structural or purely behavioral. This is the skill's whole thesis: it
makes review easier, debugging simpler, and reverts safer.

When both are needed, make the structural change first: tidy the code to
receive the new behavior, merge that PR, then build the behavioral PR on the
updated base.

A structural change is validated by the tests: the full suite passes with
identical results before and after. If behavior changed, it was not a pure
structural change.

## Commit gate (owned here — `commit-message` defers to this)

Only commit when:

1. ALL tests are passing. The gate applies at the end of a Red → Green →
   Refactor cycle: never commit a standalone Red (failing) test — keep it in
   the working tree and commit it together with the Green implementation as one
   behavioral commit. If a test fails during the Refactor step, the cycle is
   not complete: fix or revert the refactor before committing.
2. ALL compiler/linter warnings have been resolved.
3. The change represents a single logical unit of work:
   - one structural commit = one applied refactoring pattern (one Extract
     Method, one Rename, one Move Method — not a bundle of them)
   - one behavioral commit = one completed Red → Green → Refactor cycle (one
     failing test made to pass, plus any inline refactor of the new code)

Use small, frequent commits rather than large, infrequent ones.

## Commit types

Structural commits are ♻️ refactor or 🧹 tidy; `commit-message` owns the type
table and the rule that splits the two (mechanical for an IDE → 🧹; needs
judgment about module boundaries, control flow, or dependency direction → ♻️).
Apply that rule to the pattern at hand rather than a fixed pattern-to-emoji
list: the same named pattern lands either way depending on whether it moves a
boundary. Behavioral changes: ✨ feat or 🐛 fix.
