# Default review axes (hybrid: these + any issue-specific ones)

Read this when constructing reviewer dispatches. Start from these defaults and
**add** axes the issue obviously needs (e.g. "migration safety", "backwards
compat", "i18n"). Add a dedicated axis only when the concern has its **own
measurable gate KPI that no default axis already gates** — otherwise fold it into
the nearest default (`risk`, `correctness`, …) rather than duplicating. An added
plan-phase axis that needs evidence to score honestly can be marked
`spikes: true` to drive a spike, the same way `feasibility` and `risk` do.

## Plan phase

- *spec-fit* — does the plan actually solve the issue?
- *feasibility* — can it be built as described? often the one that needs a spike; `spikes: true`
- *architecture* — macro: fits existing module boundaries, layering and dependency direction
- *design* — micro: do the intended interfaces/types/APIs make sense?
- *simplicity / Tidy-First* — smallest change that works; structural vs behavioral separated
- *risk & blast-radius* — `spikes: true`
- *testability* — can each step be verified test-first?

## Impl phase

- *correctness* — mutation-tested, not just green
- *spec-fit* — incl. no scope creep
- *test coverage* — a test must fail on pre-change behavior
- *security* — the protected domains (auth, payments, data deletion or migration, security config, infrastructure, breaking API contracts, licensing)
- *performance* — hot paths, complexity, allocations, N+1 / unnecessary work
- *architecture* — macro: boundaries, dependency direction, coupling; no cycles
- *design* — micro: type/API design, encapsulation, invariants — the unit, not the wiring
- *simplicity*
- *AI-PR failure modes* — delegate to `pr-dependency-review`'s `references/ai-pr-checks.md`

*Architecture vs design*: architecture is how the pieces are wired (boundaries, dep
direction, cycles, coupling); design is whether each piece is built right (interfaces,
types, encapsulation, invariants). They fail independently and get fixed differently.

## Purpose-built reviewers

Where a purpose-built reviewer exists, dispatch it for the axis:
`pr-review-toolkit:code-reviewer` (correctness),
`pr-review-toolkit:pr-test-analyzer` (coverage),
`pr-review-toolkit:silent-failure-hunter` (security),
`pr-review-toolkit:type-design-analyzer` (design). Every other axis gets a fresh
`general-purpose` subagent. Either way the reviewer is a separate fresh-context
agent — the `maker-checker` guarantee holds for every axis.
