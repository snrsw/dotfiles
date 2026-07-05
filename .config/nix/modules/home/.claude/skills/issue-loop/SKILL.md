---
name: issue-loop
description: >
  Run a batch of issues/tasks through a per-issue dev loop and open a draft PR for
  each. Use when the user supplies several issues or tasks in the prompt and wants
  each one analyzed, planned, implemented, reviewed, and fixed until clean, in its
  own worktree, ending in a draft PR — then summarized. Triggers on "run my loop",
  "work through these issues", "dispatch a workflow for each of these", or any batch
  of tasks meant to each reach a draft PR. Builds the loop dynamically via the
  Workflow tool, with /goal as the outer until-done loop. Each issue is driven by the
  `issue-resolver` skill (scored multi-axis review loops); use `issue-resolver`
  directly for a single issue done deeply.
---

# issue-loop

Take a batch of issues — given free-form in the prompt — and drive each one to a
draft PR, in parallel, in isolated worktrees. The per-issue body is the
**`issue-resolver`** skill: it analyzes, plans, then refines both the plan and the
implementation through scored multi-axis review loops (every axis ≥ 80, each finding
verified before it drives a fix), and opens the draft PR. `issue-loop` is the batch
wrapper around it. The skill does not freeze a script; it builds one at runtime from
whatever issues you paste, then runs it.

## The loop's shape

```
/goal until no actionable item
1. collect issues (parsed from the prompt)
2. for each issue (fan-out): run issue-resolver — analyze → scored plan-refine →
   implement (test-first) → scored impl-review → draft PR, in its own worktree
3. summarize the work (final scores + any blocked issue/axis)
```

For large or triage-grade batches where the full scored loop is too costly, a
**lightweight mode** keeps the old single-axis "review until no critical/high" body
inline instead of delegating (see *Lightweight alternative* below).

## Mechanism mapping (read this first)

`/goal` is a built-in **session-level** loop — *one goal per session*, and subagents
do not carry it. So the loops use two mechanisms:

| Loop | Mechanism | Why |
|---|---|---|
| Outer "until no actionable item" | a real `/goal` on this session | session-level fits "keep going until every issue is handled" |
| Per-issue fan-out | the **`Workflow`** tool | deterministic fan-out; each issue is delegated to **issue-resolver** via the `workflow()` hook (one level of nesting — allowed) |
| Inner scored plan/impl loops | **inside issue-resolver** | bounded `while` loops live in the child, not here |

`/goal` **cannot nest**, and `workflow()` nests **only one level** — which is exactly
why the inner scored loops live inside `issue-resolver` (it never calls `workflow()`
itself, so the single nesting level is spent here, on the delegation).

## Procedure

1. **Parse** the free-form issues into a concrete work-list:
   `[{ id, title, spec, issueRef }]`. `id` is a short slug (used for the branch). If
   the list or any spec is ambiguous, confirm it with the user before dispatching.
2. **Materialize the resolver** (deep mode): copy the Workflow script template from the
   `issue-resolver` skill's SKILL.md into a file (e.g. `<session-dir>/issue-resolver.mjs`)
   and note its path as `resolver`. This is the script `workflow()` will run per issue.
3. **Set the outer goal** (optional but recommended):
   `/goal every issue in the work-list has a draft PR or is logged as blocked`.
4. **Dispatch** the `Workflow` tool with the template below, passing
   `{ issues, resolver }` as `args` (real JSON, not stringified).
5. **Relay** the returned summary. Call out every blocked issue/axis and any DR raised.

Invoking this skill is the opt-in to call `Workflow` — no separate "ultracode" trigger.

## Workflow script template (deep — delegates to issue-resolver)

```js
export const meta = {
  name: 'issue-loop',
  description: 'Batch: each issue → issue-resolver (scored plan + impl loops) → draft PR',
  phases: [{ title: 'Resolve' }],
}
// args = { issues: [{ id, title, spec, issueRef }], resolver: '<scriptPath to issue-resolver>' }
// Each issue is delegated to issue-resolver via workflow(); that child runs the scored
// plan/impl loops and opens the draft PR. One level of nesting — allowed.
const results = (await parallel(args.issues.map(issue => () =>
  workflow({ scriptPath: args.resolver }, issue)
    .then(r => ({ id: issue.id, url: r && r.pr, blocked: !!(r && r.blocked) }))
    .catch(e => ({ id: issue.id, blocked: true, error: String(e) }))))).filter(Boolean)

return { issues: results, blocked: results.filter(r => r.blocked) }
```

Why it is shaped this way:

- **`parallel` over issues** — each issue is one self-contained `workflow()` call, so
  there are no per-item stages to pipeline; the fan-out is the whole job. Concurrency is
  capped by the Workflow runtime and **shared with the children**, so a big batch
  self-throttles rather than spawning unboundedly.
- **Delegation, not duplication** — the scored plan/impl loops, the verify-each-finding
  step, spikes, and the draft PR all live in `issue-resolver`. `issue-loop` only batches.
- **`.catch` per issue** — one issue dying does not abort the batch; it is logged blocked.

## Lightweight alternative (single-axis, for large/triage batches)

When the full scored loop is too costly, skip delegation and inline the original body:
`pipeline` each issue through plan → implement → a bounded `while` loop that re-reviews
with a **fresh** reviewer (`maker-checker`) until no critical/high finding remains
(`MAX_REVIEW_ROUNDS`), then a draft PR. This is cheaper but reviews on one axis
(severity) with a boolean pass/fail — use it for triage, and deep mode when correctness
matters. The key inner loop:

```js
let round = 0, findings = []
while (round < MAX_REVIEW_ROUNDS) {
  const review = await agent(`Review the diff in ${wt} against this spec: ${spec}. ` +
    `Do not assume the author was right. Report only critical/high findings (file:line).`,
    { schema: REVIEW_SCHEMA, agentType: 'pr-review-toolkit:code-reviewer' })
  findings = review.findings.filter(f => f.severity === 'critical' || f.severity === 'high')
  if (findings.length === 0) break
  await agent(`In ${wt}, address these findings, spec fixed: ${JSON.stringify(findings)}.`)
  round++
}
```

## Safety rails

Reuses `loop-automation`'s rails — an unattended fan-out makes unattended mistakes:

- **Draft PRs only — never merge.** A human owns every merge.
- **Bound every loop.** The inner scored/severity loops are bounded; a stuck issue/axis
  is logged blocked, not retried forever.
- **Cap cost.** Deep mode is a fan-out of fan-outs (each issue runs issue-resolver's
  axis × verify × rounds × spikes). Split very large batches across runs, or use the
  lightweight mode. The shared concurrency cap throttles agents but not total tokens.
- **Verify, don't self-grade.** Reviewers/refuters are separate agents (`maker-checker`),
  inside issue-resolver.
- **Escalate, don't guess.** A protected-domain conflict, or an axis that cannot reach
  the threshold, surfaces as a DR (`decision-required`), not an autonomous fix.

## Integration

- **issue-resolver** — the per-issue body in deep mode: scored plan + impl review loops,
  one worktree per issue, ending in a draft PR. `issue-loop` is its batch wrapper.
- **git-wt** — one worktree per issue (created inside issue-resolver).
- **tdd**, **maker-checker**, **pr-review-toolkit**, **pr-body** — all used *inside*
  issue-resolver; in lightweight mode, the review loop here uses maker-checker directly.
- **plan-state** — record progress in `plan.md` if the batch spans sessions; the outer
  `/goal` can resume from it.
- **loop-automation** — if this loop should run unattended on a schedule, that skill is
  the heartbeat; this skill is the per-issue body it runs.
- **decision-required** — escalation path for ambiguous or protected-domain calls.
