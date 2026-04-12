---
name: plan-execute
description: Autonomous plan execution loop with quality gates, progress logging, and structured escalation. Use when the user says "execute the plan", "run the plan", "auto-execute", or wants hands-off implementation from an existing plan.md. Reads plan.md, executes tasks, logs progress, self-corrects, and creates a PR.
---

# Plan Execute

## Instructions

Autonomously execute tasks from plan.md with quality gates and structured escalation.
This skill orchestrates other skills (tdd, tidy-first, commit-message, pr-body) in a
continuous loop.

### Prerequisites

- A `plan.md` must exist in the project root with tasks marked `[ ]`
- The user has explicitly requested autonomous execution

### Execution Loop

For each uncompleted task in plan.md:

1. **Read plan.md** — identify the next `[ ]` task
2. **Log start** — append to `worklog.md`:
   ```
   ## <timestamp> — Starting: <task description>
   ```
3. **Execute the task** using the appropriate skills:
   - Structural changes → use `tidy-first`
   - New behavior → use `tdd` (Red → Green → Refactor)
   - Use `impl-auditor` agent after Green phase to verify minimality
   - Use `tidy-guard` agent before structural commits
4. **Quality gate** — after each task:
   - Run linter/formatter (detect from project config)
   - Run full test suite
   - If failures: self-correct up to 3 attempts, then trigger DR
5. **Commit** — use `commit-message` skill
6. **Log completion** — append to `worklog.md`:
   ```
   ## <timestamp> — Completed: <task description>
   - Changes: <brief summary>
   - Tests: <pass/fail count>
   - Decisions: <any DRs triggered, with references>
   ```
7. **Update plan.md** — mark task `[x]`
8. **Proceed to next task**

### Worklog (worklog.md)

The worklog serves as session memory and progress tracker:

- Created automatically at start of execution
- Append-only during execution
- Records: task start/end, changes made, test results, decisions, blockers
- Enables context recovery if session is interrupted
- Located in project root alongside plan.md

### Quality Gates

Before proceeding to the next task, ALL must pass:

- [ ] All existing tests pass
- [ ] New tests pass
- [ ] Linter passes (auto-fix if possible)
- [ ] Formatter passes (auto-fix if possible)
- [ ] impl-auditor PASS (no over-engineering)

If a gate fails:
1. Attempt self-correction (max 3 attempts)
2. Log each attempt in worklog.md
3. If still failing after 3 attempts → trigger DR with options

### Self-Review

After all tasks are complete:

1. Review the full diff against the base branch
2. Check for:
   - Consistency across all changes
   - Missing edge cases
   - Proper error handling at system boundaries
   - Documentation updates needed
3. Log review findings in worklog.md
4. Fix any issues found (new tasks, appended to plan.md and executed)

### PR Creation

After self-review passes:

1. Use `pr-body` skill to draft the PR
2. Include worklog summary in PR body
3. Create PR via `gh pr create`
4. Log PR URL in worklog.md

### Guardrails

Execution automatically pauses (triggers DR) when:

- A task touches a protected domain (see decision-required rule)
- Test failures persist after 3 self-correction attempts
- A task requires creating or modifying files outside the project
- The implementation diverges significantly from plan.md
- A dependency or API behaves differently than expected

### Session Continuity

plan.md is the Single Source of Truth for what needs to be done.
worklog.md is the Single Source of Truth for what has been done.

On session resume:
1. Read plan.md — understand remaining tasks
2. Read worklog.md — understand completed work and context
3. Read decisions.md — understand past judgment calls
4. Continue from the first uncompleted `[ ]` task

### Relationship to Other Modes

- `plan-driven-workflow`: manual, one task at a time, user says "go" each step
- `plan-execute`: autonomous, executes all tasks, pauses only for DRs and guardrails

Both read from the same plan.md format. You can start with plan-driven-workflow
for sensitive tasks, then switch to plan-execute for straightforward ones.
