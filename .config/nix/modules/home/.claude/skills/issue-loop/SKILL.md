---
name: issue-loop
description: >
  Run a batch of issues/tasks through a per-issue dev loop — each analyzed,
  implemented, and reviewed in its own worktree, ending in a draft PR — then
  summarized. Triggers on "run my loop", "work through these issues", or any
  batch of tasks meant to each reach a draft PR. The batch wrapper around
  `issue-resolver`; use that skill directly for a single issue done deeply.
---

# issue-loop

Take a batch of issues — given free-form in the prompt — and drive each one to a
draft PR in its own worktree. The per-issue body is the **`issue-resolver`** skill
(scored multi-axis review loops, every axis ≥ 80, each finding verified before it
drives a fix, draft PR at the end); `issue-loop` is the batch wrapper: it parses
the batch, runs the outer until-done loop, and summarizes.

## Mechanism mapping (read this first)

Orchestration runs on `Agent`-tool fan-out — the no-Workflow-engine decision is stated in `loop-automation`. The mechanisms:

| Loop | Mechanism | Why |
|---|---|---|
| Outer "until no actionable item" | **/loop** (ScheduleWakeup) — armed with the stop predicate below. For a small batch, plain sequential grinding in this session is fine | the outer loop must survive many turns without re-prompting |
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
3. **Arm the outer loop** (/loop) with the stop predicate above.
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

The five rails below are shared word-for-word with `loop-automation` and
`issue-resolver` — only the constants clause after each bold lead differs:

- **Open draft PRs, never merge.** A human owns every merge.
- **Bound every loop.** The outer loop exits on the stop predicate and the per-issue loops on issue-resolver's MAX_ROUNDS; a stuck item is logged blocked and raised as a DR, not retried forever.
- **Cap cost — parallelism is the trap.** MAX_PARALLEL = 10 shared across everything; split very large batches across runs, or use lightweight mode.
- **Verify, don't self-grade.** Reviewers are separate fresh-context agents (`maker-checker`); no agent scores its own artifact.
- **Escalate, don't guess.** Protected domains (auth, payments, data deletion or migration, security config, infrastructure, breaking API contracts, licensing) and unreachable thresholds surface as DRs, not autonomous decisions.

## Response style

The batch summary from step 5 is what the user actually reads after an unattended
run.

- **Lead with the batch outcome** — how many issues reached a draft PR, how many
  are blocked — before the per-issue detail.
- **Present the per-issue results as a table**, since they are parallel items. One
  kind of content per column: PR URL, lowest final axis score, blocked axes, DR
  link.
- **Status values come from a small closed set** — use the same vocabulary as
  `plan.md` (`done` / `blocked`), one meaning each. Do not invent per-run labels
  like "done (needs adjustment)"; put the nuance in a notes column.
- **The table must agree with the prose**, and both must agree with `plan.md`. The
  user skims the table and trusts it over the surrounding text.
- **No planning jargon** in the summary — issue slugs are fine, internal axis
  numbering and round counts are not, unless a score is below threshold.

## Integration

- **loop-automation** — to run this batch unattended on a schedule, that skill is
  the heartbeat (a Routine); this skill is the per-issue body it runs.
