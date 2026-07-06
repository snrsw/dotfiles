---
name: issue-loop
description: >
  Run a batch of issues/tasks through a per-issue dev loop and open a draft PR for
  each. Use when the user supplies several issues or tasks in the prompt and wants
  each one analyzed, planned, implemented, reviewed, and fixed until clean, in its
  own worktree, ending in a draft PR — then summarized. Triggers on "run my loop",
  "work through these issues", "dispatch a workflow for each of these", or any
  batch of tasks meant to each reach a draft PR. Each issue is driven by the
  `issue-resolver` skill (scored multi-axis review loops); use `issue-resolver`
  directly for a single issue done deeply.
---

# issue-loop

Take a batch of issues — given free-form in the prompt — and drive each one to a
draft PR in its own worktree. The per-issue body is the **`issue-resolver`** skill
(scored multi-axis review loops, every axis ≥ 80, each finding verified before it
drives a fix, draft PR at the end); `issue-loop` is the batch wrapper: it parses
the batch, runs the outer until-done loop, and summarizes.

## Mechanism mapping (read this first)

There is no workflow-script engine and no `/goal` built-in. The mechanisms:

| Loop | Mechanism | Why |
|---|---|---|
| Outer "until no actionable item" | **ralph-loop**, or **/loop** (ScheduleWakeup) — armed with the stop predicate below. For a small batch, plain sequential grinding in this session is fine | the outer loop must survive many turns without re-prompting |
| Per-issue body | the **issue-resolver** procedure, orchestrated from THIS session | reviewer fan-out needs the main session (see issue-resolver's mechanism mapping) |
| Per-issue isolation | one `git-wt` worktree per issue, branch `issue/<id>` | parallel edits never collide |
| Batch state | one batch-level `plan.md` (`plan-state`) | the loop's memory across turns and sessions |

**Stop predicate (the outer loop's only exit):** every issue in the work-list has
either a draft-PR URL or a `Blocked / DR` entry in the batch `plan.md`. Hitting
the predicate always ends the loop; nothing else ends it early.

**Concurrency.** MAX_PARALLEL = 10 subagents, shared with the per-issue loops.
Work the issues with **bounded interleaving**: while one issue's implementer runs
in the background, review another issue's finished artifacts from this session.
True issue-level parallelism (one orchestrator subagent per issue, fanning out
internally) requires nested subagent dispatch — verify it actually works in your
environment before relying on it; interleaving from this session is the safe
default, because a subagent that cannot fan out degrades to reviewing its own
work.

## Procedure

1. **Parse** the free-form issues into a concrete work-list:
   `[{ id, title, spec, issueRef }]`. `id` is a short slug (used for the branch).
   If the list or any spec is ambiguous, confirm it with the user before starting.
2. **Write the batch `plan.md`** (`plan-state`): every issue under `## Next`, with
   its acceptance criteria on the spec line.
3. **Arm the outer loop** (ralph-loop or /loop) with the stop predicate above.
4. **Per issue:** run `issue-resolver` end to end — worktree → analyze → scored
   plan loop → implement test-first → scored impl loop → draft PR. Record the PR
   URL (or the blocked reason and DR link) in the batch `plan.md` and move the
   item to `## Done` or `## Blocked / DR`.
5. **Summarize** when the predicate holds: per issue — PR URL, lowest final axis
   score, blocked axes, and any DR raised.

## Lightweight mode (single severity axis, for large or triage batches)

When the full scored loop costs more than the batch is worth: per issue, skip the
multi-axis loops and run plan → implement → a bounded review loop (at most 3
rounds). Each round, a **fresh** `pr-review-toolkit:code-reviewer` subagent
reviews the diff against the spec ("do not assume the author was right") and
reports only critical/high findings; fix them and re-review until none remain —
then open the draft PR. Cheaper, but it reviews on one axis (severity) with a
boolean pass/fail: use it for triage, and the full resolver when correctness
matters.

## Safety rails

Reuses `loop-automation`'s rails — an unattended batch makes unattended mistakes:

- **Draft PRs only — never merge.** A human owns every merge.
- **Bound every loop.** The outer loop exits on the stop predicate; the per-issue
  loops are bounded by issue-resolver's MAX_ROUNDS; a stuck issue or axis is
  logged `Blocked / DR`, not retried forever.
- **Cap cost.** MAX_PARALLEL = 10 shared across everything; split very large
  batches across runs, or use lightweight mode.
- **Verify, don't self-grade.** Reviewers and refuters are separate fresh-context
  agents (`maker-checker`) inside issue-resolver; lightweight mode's reviewer is a
  fresh subagent each round.
- **Escalate, don't guess.** Protected domains and unreachable thresholds surface
  as DRs (`decision-required`), not autonomous fixes.

## Integration

- **issue-resolver** — the per-issue body; this skill only batches it.
- **git-wt** — one worktree per issue (created inside issue-resolver).
- **tdd**, **maker-checker**, **pr-review-toolkit**, **pr-body** — all used
  *inside* issue-resolver; lightweight mode uses the code-reviewer directly.
- **plan-state** — the batch `plan.md` is the loop's state and the resume point.
- **loop-automation** — to run this batch unattended on a schedule, that skill is
  the heartbeat (a Routine); this skill is the per-issue body it runs.
- **decision-required** — escalation path for ambiguous or protected-domain calls.
