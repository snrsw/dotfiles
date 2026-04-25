# Clarification Required (CR) Pattern

When the user's prompt is too ambiguous or under-specified to execute confidently — vague goal, unbounded scope, missing success criteria, or missing required inputs — do NOT guess and do NOT start work. Ask one focused round of clarifying questions first.

This is distinct from the DR pattern: DR fires during execution when *you* hit a judgment call; CR fires before execution when the *prompt itself* is missing what you need to start.

If a CR-triggered prompt also touches a DR Protected Domain (auth, payments, data deletion/migration, security config, infra/deploy, breaking API changes, license/legal), surface CR first. DR escalation still applies once defaults are accepted — accepting defaults does not bypass the protected-domain review.

## When to Trigger CR

Trigger before doing any non-trivial work if any of the following are true:

- The goal is vague or subjective with no measurable outcome ("make it better", "clean this up", "improve performance")
- Scope is unbounded and the answer materially changes the work (which files / which package / repo-wide?)
- Success criteria are absent ("done when …?") and the natural endpoint is not obvious from context
- A required input is missing or ambiguous (which file, which branch, which user, which env, which version)
- The same prompt has two or more plausible readings that lead to meaningfully different work
- A hard constraint or budget is unspecified where it matters (time, breaking-change tolerance, perf budget, allowed deps)

## When NOT to Trigger CR

Do not stall on questions you can answer yourself. Skip CR when:

- The answer is derivable from the code, git history, plan.md, CLAUDE.md, or memory
- The gap is stylistic — match the surrounding code instead
- The task is small and reversible enough that a stated assumption is cheaper than a round-trip ("Assuming X, proceeding — say if not")
- The user has already answered the same question recently in this conversation

Asking trivial confirmations ("should I really do what you asked?") is worse than guessing. The bar for CR is: *would a wrong guess waste meaningful work or produce the wrong artifact?*

## CR Format

Stop execution and present:

### CR: <short title>

**Understood**: <1-2 sentences restating the task as you currently read it>

**Gaps blocking execution**:
1. <specific gap> — <why it matters>
2. <specific gap> — <why it matters>

**Proposed defaults** (used if you say "go with defaults"):
- <gap 1>: <concrete default>
- <gap 2>: <concrete default>

Prefer concrete multiple-choice options over open-ended questions. Cap at 3 gaps per round — if more exist, surface the load-bearing ones first.

When `AskUserQuestion` is available, use it to present options rather than free text.

## After Resolution

1. Restate the resolved understanding in one line, then proceed.
2. If the clarification reveals scope larger than a single task, switch to plan-driven-workflow and write plan.md before implementing.
3. Do not re-ask the same gap later in the conversation; treat the answer as settled unless the user changes it.
