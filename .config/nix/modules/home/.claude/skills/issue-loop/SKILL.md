---
name: issue-loop
description: >
  Run a batch of issues/tasks through a per-issue dev loop and open a draft PR for
  each. Use when the user supplies several issues or tasks in the prompt and wants
  each one analyzed, planned, implemented, reviewed, and fixed until clean, in its
  own worktree, ending in a draft PR — then summarized. Triggers on "run my loop",
  "work through these issues", "dispatch a workflow for each of these", or any batch
  of tasks meant to each reach a draft PR. Builds the loop dynamically via the
  Workflow tool, with /goal as the outer until-done loop.
---

# issue-loop

Take a batch of issues — given free-form in the prompt — and drive each one to a
draft PR through the same per-issue loop, in parallel, in isolated worktrees. The
skill does not freeze a script; it builds one at runtime from whatever issues you
paste, then runs it.

## The loop's shape

```
/goal until no actionable item
1. collect issues (parsed from the prompt)
2. for each issue (fan-out, one worktree each):
   2.1 until no critical/high problem:
       analyze → plan → implement → review → address review comments
   2.2 open a draft PR
3. summarize the work
```

## Mechanism mapping (read this first)

`/goal` is a built-in **session-level** loop — *one goal per session*, and
subagents do not carry it. So the two nested loops above use two mechanisms:

| Loop | Mechanism | Why |
|---|---|---|
| Outer "until no actionable item" | a real `/goal` on this session | session-level fits "keep going until every issue is handled" |
| Per-issue fan-out + inner "until no critical/high" | the **`Workflow`** tool | deterministic fan-out, per-item pipeline, and a bounded `while` loop for the inner review cycle |

`/goal` **cannot nest**. The inner "until no critical/high" loop is therefore a
bounded `while` loop inside the Workflow script, not a second `/goal`.

## Procedure

1. **Parse** the free-form issues in the prompt into a concrete work-list:
   `[{ id, title, spec }]`. `id` is a short slug (used for the branch). If the list
   or any spec is ambiguous, confirm it with the user before dispatching.
2. **Set the outer goal** (optional but recommended):
   `/goal every issue in the work-list has a draft PR or is logged as blocked`.
3. **Dispatch** the `Workflow` tool with a script adapted from the template below,
   passing the work-list as `args` (a real JSON array, not a stringified one).
4. **Relay** the returned summary. Call out every blocked issue and any DR raised.

Invoking this skill is the opt-in to call `Workflow` — you do not need a separate
"ultracode" trigger.

## Workflow script template

Adapt this — change schemas, models, and `MAX_REVIEW_ROUNDS` to fit the batch.

```js
export const meta = {
  name: 'issue-loop',
  description: 'Per-issue: worktree → analyze/plan → implement → review-until-clean → draft PR',
  phases: [{ title: 'Plan' }, { title: 'Implement' }, { title: 'Review' }, { title: 'PR' }],
}
// args = [{ id, title, spec }, ...]  — the parsed work-list
const MAX_REVIEW_ROUNDS = 3

const results = await pipeline(
  args,
  // Stage 1: isolate + analyze + plan. One worktree per issue — distinct
  // branch/path per id, so concurrent `git worktree add` does not conflict.
  (issue) => agent(
    `Create a git worktree for issue ${issue.id} on branch issue/${issue.id} ` +
    `(use the git-wt skill). Analyze and write a short plan for: ${issue.spec}. ` +
    `Return {worktree, branch, plan}.`,
    { label: `plan:${issue.id}`, phase: 'Plan', schema: PLAN_SCHEMA }),

  // Stage 2: implement in that worktree, test-first.
  (p, issue) => agent(
    `In worktree ${p.worktree}, implement this plan test-first (tdd skill): ${p.plan}. ` +
    `Return {worktree: '${p.worktree}', branch: '${p.branch}', changedFiles}.`,
    { label: `impl:${issue.id}`, phase: 'Implement', schema: IMPL_SCHEMA }),

  // Stage 3: inner loop — review until no critical/high, bounded. The reviewer
  // is a fresh agent that never sees the maker's justification (maker-checker).
  async (impl, issue) => {
    let round = 0, findings = []
    while (round < MAX_REVIEW_ROUNDS) {
      const review = await agent(
        `Review the diff in worktree ${impl.worktree} against this spec: ${issue.spec}. ` +
        `Do not assume the author was right. Report only critical/high findings, ` +
        `each with file:line.`,
        { label: `review:${issue.id}:r${round}`, phase: 'Review',
          schema: REVIEW_SCHEMA, agentType: 'pr-review-toolkit:code-reviewer' })
      findings = review.findings.filter(f => f.severity === 'critical' || f.severity === 'high')
      if (findings.length === 0) break
      await agent(
        `In worktree ${impl.worktree}, address these review findings, keeping the ` +
        `spec fixed: ${JSON.stringify(findings)}.`,
        { label: `fix:${issue.id}:r${round}`, phase: 'Review' })
      round++
    }
    return { ...impl, residualFindings: findings }
  },

  // Stage 4: open a DRAFT PR (pr-body skill for the description). Never merge.
  (r, issue) => agent(
    `In worktree ${r.worktree} on branch ${r.branch}, push and open a DRAFT PR ` +
    `(gh pr create --draft) with a body following the pr-body skill. ` +
    `${r.residualFindings.length ? 'List the unresolved findings in the PR body.' : ''} ` +
    `Return {url, blocked: ${r.residualFindings.length > 0}}.`,
    { label: `pr:${issue.id}`, phase: 'PR', schema: PR_SCHEMA }),
)

return {
  issues: results.filter(Boolean),
  blocked: results.filter(Boolean).filter(r => r.blocked),
}
```

Why it is shaped this way:

- **`pipeline`, not `parallel`** — issues flow through stages independently; a slow
  reviewer on one issue does not stall another. No barrier unless you need one.
- **`while`, not a fixed pass** — the inner loop re-reviews until clean, but
  `MAX_REVIEW_ROUNDS` caps it. Residual findings mark the PR `blocked` instead of
  looping forever.
- **One worktree per issue** — distinct branch/path per `id`, so parallel edits
  never collide. The whole per-issue chain shares that one worktree.
- **Fresh reviewer** — Stage 3's reviewer gets the spec + diff only, never the
  maker's reasoning (`maker-checker`).

## Safety rails

Reuses `loop-automation`'s rails — an unattended fan-out makes unattended mistakes:

- **Draft PRs only — never merge.** A human owns every merge.
- **Bound the inner loop.** Stop at `MAX_REVIEW_ROUNDS`; log the rest as blocked.
- **Cap parallelism.** Workflow caps concurrent agents, but a huge work-list still
  burns tokens — split very large batches across runs.
- **Verify, don't self-grade.** The reviewer is a separate agent (`maker-checker`).
- **Escalate, don't guess.** A protected-domain conflict (auth, payments, data
  migration, infra…) surfaces as a DR (`decision-required`), not an autonomous fix.

## Integration

- **git-wt** — one worktree per issue (Stage 1).
- **tdd** — implement test-first (Stage 2).
- **maker-checker** + **pr-review-toolkit:code-reviewer** / **silent-failure-hunter** —
  the review-until-clean loop (Stage 3).
- **pr-body** — the draft PR description (Stage 4).
- **loop-state** — record progress in `plan.md` if the batch spans sessions; the
  outer `/goal` can resume from it.
- **loop-automation** — if this loop should run unattended on a schedule, that skill
  is the heartbeat; this skill is the per-issue body it runs.
- **decision-required** — escalation path for ambiguous or protected-domain calls.
