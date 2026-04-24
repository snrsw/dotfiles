---
name: debug
description: Structured debugging and investigation using reproduce, isolate, fix, regression test workflow. Use when fixing bugs, investigating unexpected behavior, diagnosing failures, troubleshooting errors, something is broken, a test is failing unexpectedly, behavior doesn't match expectations, the user says "debug", "investigate", "why is this failing", "what's wrong", or "figure out why". Also use when a bug report or issue needs systematic analysis rather than a quick guess.
---

# debug

## Instructions

Follow a structured debugging methodology: reproduce, isolate, fix, verify. Every bug fix must be backed by a regression test written before the fix.

### Two Modes

Choose the mode based on how clearly the problem is defined:

- **Bug Mode**: A clear failure exists (crash, wrong output, failing test). Follow the four phases linearly.
- **Investigation Mode**: Behavior is unclear or surprising but there is no definitive failure yet. Front-load isolation with instrumentation and hypothesis testing. If a bug is confirmed, switch to Bug Mode at Phase 3.

### Core Principle

Understand before you fix. Do not apply a fix until you can explain the root cause. Treating symptoms creates new bugs.

### The Debug Workflow

#### Phase 1: Reproduce

Confirm the failure is observable right now.

- Record exact steps, inputs, and observed vs expected output
- Reduce to a minimal reproduction case -- strip away everything unrelated
- If not reproducible, switch to Investigation Mode: add logging, narrow conditions, gather data

The reproduction case becomes the basis for the regression test in Phase 3. Without it, fixes are guesses.

#### Phase 2: Isolate

Binary search the problem space to find the root cause.

- Narrow which component, module, function, or line is responsible
- Techniques: comment out code, add assertions, `git bisect`, reduce inputs, test subsystems in isolation
- Identify the root cause, not just the symptom
- Document ruled-out hypotheses -- this prevents re-exploring dead ends and helps if the investigation is handed off

#### Phase 3: Fix (via TDD)

Before writing any fix code, write a failing test that reproduces the bug. This test is the regression test -- it must fail without the fix and pass with it.

1. Write a failing test for the bug (Red) -- follow the `tdd` skill's Defect Fixing workflow
2. Write the minimal fix to make the test pass (Green)
3. If structural changes are needed to make the code testable, use `tidy-first` to separate them into their own commits before the fix

#### Phase 4: Verify

- Run the full test suite, not just the regression test
- Confirm the original reproduction case now behaves correctly
- Check for side effects -- did fixing this break something else?
- If the fix touches a protected domain (auth, payments, data deletion, security), trigger a DR before merging

### Golden Rules

1. **Never fix without a failing test** -- write the regression test before the fix. If you cannot write a test, trigger a DR to discuss why.
2. **Understand before you fix** -- explain the root cause before applying any change.
3. **One fix per commit** -- each bug fix is a single commit. Structural prep goes in separate commits first.
4. **Document dead ends** -- when you rule out a hypothesis, note it briefly. This saves time if the investigation is revisited.

### Commit Standards

Use the `commit-message` skill format:

- Bug fixes: `🐛(<scope>): <description of root cause>`
- Structural prep: `♻️ refactor` or `🧹 tidy` in separate commits before the fix
- The commit message should explain the root cause (the "why"), not just what changed

### Integration with Other Skills

- **tdd**: Phase 3 delegates to the Defect Fixing workflow (write failing test first, then minimal fix)
- **tidy-first**: If structural changes are needed to make buggy code testable, separate them into their own commits before the fix
- **plan-driven-workflow**: If a bug is discovered during plan execution, pause the plan, debug using this skill, add the regression test to plan.md, then resume
- **git-wt**: For complex investigations, consider creating a worktree to isolate debugging work from in-progress feature development
- **DR pattern**: Trigger a DR when the fix touches a protected domain, multiple valid fixes exist with meaningful trade-offs, or the bug reveals a design flaw requiring architectural discussion

## Examples

### Bug Mode

```go
// Phase 1 — Reproduce
// CalculateDiscount(100, 0) returns -5, expected 0

// Phase 2 — Isolate
// Root cause: discount rate defaults to -0.05 when 0 is passed
// Ruled out: input validation (caller passes correct value)

// Phase 3 — Fix (Red → Green)
func TestCalculateDiscount_ZeroRate(t *testing.T) {
    got := CalculateDiscount(100, 0)
    if got != 0 {
        t.Errorf("CalculateDiscount(100, 0) = %f, want 0", got)
    }
}
// ❌ FAILS — returns -5

// Fix: check for zero rate before applying default
// ✅ PASSES

// Phase 4 — Verify: full test suite passes
// Commit: 🐛(pricing): handle zero discount rate instead of applying default
```

### Investigation Mode

```
// "Nix build seems slower than last week" — no clear failure

// Phase 2 (front-loaded) — Isolate
// Add timing to build phases, compare with cached build log
// Hypothesis 1: new dependency added → ruled out (deps unchanged)
// Hypothesis 2: derivation rebuilding unnecessarily → confirmed
// Root cause: hash changed due to unrelated file included in source filter

// Confirmed as bug → switch to Bug Mode at Phase 3
// Write test for source filter, fix filter, verify build time
```

### DR Trigger

```
// Debugging a login failure — root cause is in session token validation
// Session handling is a protected domain → trigger DR before applying fix
```
