---
name: plan-spike
description: Run a throwaway prototype to validate assumptions before committing to a plan. Use when requirements are uncertain, a technical approach is unproven, you need to explore an API or library, or the user says "spike", "prototype", or "explore". Code is discarded; knowledge is retained.
---

# Plan Spike

## Instructions

A spike is a time-boxed throwaway experiment. The goal is learning, not production code.

### When to Spike

- Requirements are vague and need concrete exploration
- A technical approach (library, API, algorithm) is unproven
- The user is unsure whether something is feasible
- Before creating plan.md, to inform what the plan should contain

### Spike Protocol

1. **Define the question**: State the single question this spike answers.
   Write it at the top of `spike-log.md`:
   ```
   ## Spike: <title>
   **Question**: <what are we trying to learn?>
   **Time-box**: <estimated duration, default 30 min>
   ```

2. **Implement fast**: Write the quickest code that answers the question.
   - No tests required (this is throwaway)
   - No commit discipline required
   - No tidy-first separation required
   - Hardcoded values, shortcuts, copy-paste — all acceptable
   - Use a scratch branch or worktree (`git wt spike-<name>`) to isolate

3. **Record findings**: Update `spike-log.md` with:
   ```
   **Findings**:
   - <what worked>
   - <what didn't>
   - <surprising discoveries>
   - <performance/feasibility observations>

   **Conclusion**: <answer to the original question>

   **Recommendation**: <proceed to plan-execute / revise approach / need another spike>
   ```

4. **Discard code**: Delete the spike branch/worktree.
   The spike-log.md is the only artifact that survives.

### Key Principles

- **Code is disposable, knowledge is permanent**: Never promote spike code to production
- **One question per spike**: If you discover new questions, log them for separate spikes
- **Time-boxed**: If the spike is taking too long, stop and log what you learned so far
- **No TDD**: This is the one context where TDD does not apply

### Integration

- After a spike, use findings to create or refine `plan.md`
- Then switch to `plan-driven-workflow` or `plan-execute` for real implementation
- Reference spike-log.md in plan.md for decision context
