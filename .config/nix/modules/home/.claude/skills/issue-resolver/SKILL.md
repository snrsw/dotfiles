---
name: issue-resolver
description: >
  Drive ONE issue from raw context to a reviewed, fixed implementation behind a
  draft PR, with quality enforced by scored multi-axis review loops. Use when the
  user hands over a single issue (a GitHub issue URL/number, or a written spec) and
  wants it "done properly", "resolved end to end", "taken to a PR with quality
  gates", or "reviewed until it's actually good" — not a quick patch. Each review
  subagent owns one axis and returns {issue, confidence, fixingPlan, score}; the
  loop refines until every axis scores >= 80, at both the plan and the
  implementation stage, and verifies each finding before acting on it. This is the
  deep, single-issue sibling of `issue-loop` (a batch loop with one severity axis) —
  prefer this skill for one issue done thoroughly, and `issue-loop` for a batch.
---

# issue-resolver

Take a single issue and drive it to a draft PR through two **scored review loops** —
one over the plan, one over the implementation. Where `issue-loop` reviews a batch on
one axis (severity) until findings clear, this skill reviews **one** issue on many
axes, each scored 0–100, and keeps refining until **every axis is ≥ 80**. Findings are
independently **verified before** they are acted on, and the plan stage can run
**spikes** to resolve unknowns with evidence instead of guesswork. Like `issue-loop`,
it builds the loop at runtime from the issue you paste — it does not freeze a script.

## The loop's shape

```
1. get context        (read the issue, the repo, the related code)
2. analyze            (fan-out subagents, one per angle)
3. plan               (subagent drafts the plan)
4. refine plan  — scored loop until every plan axis >= 80:
     4.1 review: one subagent per axis -> {axis, score, confidence, findings}
     4.2 verify: a fresh agent tries to REFUTE each finding -> keep only confirmed
     4.3 fix the plan; if an axis needs evidence, spike it in a throwaway worktree,
         compare spikes, fold the conclusion back into the plan
5. implement          (subagent, test-first, in the issue worktree)
6. review+fix  — same scored loop until every impl axis >= 80:
     6.1 review: one subagent per axis -> {axis, score, confidence, findings}
     6.2 verify: refute each finding -> keep only confirmed
     6.3 fix the confirmed findings
7. open a DRAFT PR (never merge); report final scores and any blocked axis
```

## Mechanism mapping (read this first)

One issue, so there is no batch fan-out and no outer `/goal` — the whole thing is a
single **`Workflow`** script with two bounded scored `while` loops. The fan-out is
*inside* each loop: one reviewer per axis runs in `parallel`, then one verifier per
finding runs in `parallel`. Invoking this skill is the opt-in to call `Workflow`; you
do not need a separate "ultracode" trigger.

The two loops are the same shape, so they share one helper, `refineUntilScored` — only
the axis set and the "fix" action differ between plan-phase and impl-phase.

## The scored review contract

Every axis reviewer returns this. The loop treats `score` and verified findings as the
two gates — an axis passes only when its `score >= MIN_SCORE` **and** no confirmed
critical/high finding remains:

```
{ axis, score: 0-100, confidence: 0-1,
  kpi?: { name, value, target },   // the measurement that justifies the score
  findings: [{ issue, severity: 'critical'|'high'|'medium'|'low', fixingPlan, fileLine?, metric? }] }
```

`confidence` is the reviewer's own certainty; it is advisory. The real gate against
false findings is step 4.2/6.2 — an *independent* refuter, not the reviewer's self-report.

## Anchor scores on KPIs (don't score on vibes)

A 0–100 score means little unless it is anchored on something measurable. Where an axis
has a real metric, the reviewer should **measure it, report it as `kpi`, and let the
distance from target drive the score** — the same discipline `pr-dependency-review` uses
(findings carry a measured value, not an adjective). Where no hard metric fits (e.g.
spec-fit on a fuzzy issue, or any plan-phase axis before code exists), score on judgement
and say so (`kpi.name = 'judgement'`) — don't fabricate a number.

**Gates vs graded KPIs.** Some KPIs are *graded* — coverage %, complexity, perf delta —
and map smoothly onto the score (roughly: at-or-past target → ~90+, far from it → low;
state the rule you used so it is reproducible). Others are *gates* — a single breach means
the axis is not done, regardless of an otherwise high score (0 failing tests, 0 circular
deps, 0 secrets, protected-domain → DR). **File every gate breach as a `critical`
finding**, so it blocks through the "no confirmed critical/high" gate independent of the
number. A high score never buys back a gate breach. Default KPI per axis (target in
parentheses; ⛔ = gate):

| Axis | KPI (target) |
|---|---|
| correctness | ⛔ tests green & a test fails on pre-change behavior; mutation score (≥ 70%) |
| coverage | diff coverage % (≥ 80); ⛔ new uncovered branches (0) |
| security | ⛔ SAST + secret-scan + dependency-vuln findings (0); protected-domain change → DR |
| performance | benchmark present → latency/throughput delta (≤ budget); else complexity of changed hot paths + query count; ⛔ added N+1 (0) |
| architecture | ⛔ new circular deps (0); ⛔ dependency-direction / layering violations (0); fan-in/out vs threshold (reuse `pr-dependency-review`) |
| design | encapsulation / invariant-expression / enforcement ratings (`type-design-analyzer`); ⛔ unintended public-API surface change (0) |
| simplicity | cyclomatic complexity per changed fn (≤ 10); max nesting depth; duplication |
| testability (plan) | plan steps with a defined test (100%) |
| feasibility (plan) | unresolved feasibility unknowns (0 — spike to resolve) |
| risk (plan) | blast-radius modules; ⛔ reversibility (irreversible op / data migration → DR); protected domains → DR |
| spec-fit | acceptance criteria addressed (100%); out-of-scope changes (0) — judgement if criteria fuzzy |
| ai-pr-checks | ⛔ AI-PR failure-mode hits (0) |

These are the *defaults*; a reviewer may report a better axis-specific metric for the
issue at hand. The point is that the number is earned, not asserted.

## Default axes (hybrid: these + any issue-specific ones)

Start from these and **add** axes the issue obviously needs (e.g. "migration safety",
"backwards compat", "i18n"). Each axis maps to a purpose-built reviewer where one exists.

- **Plan phase** — *spec-fit* (does the plan actually solve the issue?), *feasibility*
  (can it be built as described? often the one that needs a spike), *architecture* (macro:
  fits existing module boundaries, layering and dependency direction), *design* (micro: do
  the intended interfaces/types/APIs make sense?), *simplicity / Tidy-First* (smallest
  change that works; structural vs behavioral separated), *risk & blast-radius*,
  *testability* (can each step be verified test-first?).
- **Impl phase** — *correctness* (mutation-tested, not just green), *spec-fit* (incl. no
  scope creep), *test coverage* (`tdd`; a test must fail on pre-change behavior),
  *security* (the protected domains in `decision-required`),
  *performance* (hot paths, complexity, allocations, N+1 / unnecessary work),
  *architecture* (macro: boundaries, dependency direction, coupling; no cycles), *design*
  (micro: type/API design, encapsulation, invariants — the unit, not the wiring),
  *simplicity*, *AI-PR failure modes* (delegate to `pr-dependency-review`'s
  `references/ai-pr-checks.md`: hallucinated correctness, reinvented utilities, phantom
  imports, scope creep, weakened CI, comprehension debt).

  *Architecture vs design*: architecture is how the pieces are wired (boundaries, dep
  direction, cycles, coupling); design is whether each piece is built right (interfaces,
  types, encapsulation, invariants). They fail independently and get fixed differently.

## Verify-each-review (why the refute step matters)

A reviewer that both finds and confirms its own issue is biased toward "I was right" —
the same self-grading failure `maker-checker` warns about. So before any fix, a **fresh**
agent receives one finding and is asked to *refute* it ("assume this may be wrong"). Only
confirmed findings drive a fix. This stops the loop from acting on hallucinated issues
and from being gamed into never terminating by a reviewer that keeps inventing problems.

## Spikes (plan phase only)

When a lagging axis — usually *feasibility* or *risk* — cannot be scored honestly without
evidence ("will this approach be fast enough / fit the existing API?"), spawn 1–N spike
agents, each in a **throwaway** worktree, to build the smallest prototype that answers the
question and measure it against a stated metric. Compare the spikes, fold the winning
**conclusion** into the plan, and discard the spike code — only the conclusion survives.
Cap the number of spikes (`MAX_SPIKES`) so this does not balloon.

## Workflow script template

Adapt this — change schemas, axes, models, `MIN_SCORE`, `MAX_ROUNDS`, `MAX_SPIKES`.

```js
export const meta = {
  name: 'issue-resolver',
  description: 'One issue: context → analyze → plan → scored refine → implement → scored review → draft PR',
  phases: [
    { title: 'Context' }, { title: 'Plan' }, { title: 'RefinePlan' },
    { title: 'Implement' }, { title: 'ReviewImpl' }, { title: 'PR' },
  ],
}
// args = { id, title, spec, issueRef }  — ONE issue (id is a slug used for the branch)
const issue = args
const MIN_SCORE = 80, MAX_ROUNDS = 3, MAX_SPIKES = 2

const REVIEW_SCHEMA = {
  type: 'object', required: ['axis', 'score', 'confidence', 'findings'],
  properties: {
    axis: { type: 'string' },
    score: { type: 'number' }, confidence: { type: 'number' },
    findings: { type: 'array', items: {
      type: 'object', required: ['issue', 'severity', 'fixingPlan'],
      properties: {
        issue: { type: 'string' }, severity: { enum: ['critical', 'high', 'medium', 'low'] },
        fixingPlan: { type: 'string' }, fileLine: { type: 'string' },
      } } },
  },
}
const VERDICT_SCHEMA = { type: 'object', required: ['confirmed', 'why'],
  properties: { confirmed: { type: 'boolean' }, why: { type: 'string' } } }

// ---- shared scored-refinement loop (plan-phase and impl-phase use the same engine) ----
// axes: [{ key, prompt, agentType? }]; makeReviewPrompt(axis, round) -> string;
// fixWith(confirmedFindings, laggingAxes, round) -> Promise (applies the fix)
async function refineUntilScored(label, axes, makeReviewPrompt, fixWith, phaseName) {
  let round = 0
  while (round < MAX_ROUNDS) {
    // review: one fresh reviewer per axis, in parallel (never sees the maker's reasoning)
    const reviews = (await parallel(axes.map(a => () =>
      agent(makeReviewPrompt(a, round),
        { label: `${label}:review:${a.key}:r${round}`, phase: phaseName,
          schema: REVIEW_SCHEMA, agentType: a.agentType })))).filter(Boolean)

    // verify: refute each finding with a fresh agent; keep only confirmed ones
    const flat = reviews.flatMap(r => r.findings.map(f => ({ ...f, axis: r.axis })))
    const verified = (await parallel(flat.map(f => () =>
      agent(`Try to REFUTE this review finding — assume it may be wrong, default to ` +
            `confirmed=false if unsure. Finding: ${JSON.stringify(f)}.`,
        { label: `${label}:verify:${f.axis}:r${round}`, phase: phaseName, schema: VERDICT_SCHEMA })
        .then(v => ({ ...f, confirmed: !!(v && v.confirmed) }))))).filter(Boolean)
    const confirmed = verified.filter(f => f.confirmed)

    const lagging = reviews.filter(r => r.score < MIN_SCORE)
    const blocking = confirmed.filter(f => f.severity === 'critical' || f.severity === 'high')
    const min = Math.min(...reviews.map(r => r.score))
    log(`${label} r${round}: min=${min} lagging=[${lagging.map(r => r.axis)}] confirmed=${confirmed.length}`)
    if (lagging.length === 0 && blocking.length === 0) return { passed: true, scores: reviews, round }

    await fixWith(confirmed, lagging, round)
    round++
  }
  return { passed: false, blocked: true, round }  // bounded exit → mark blocked + raise a DR
}

// 1. context  +  2. analyze (fan-out by angle)
phase('Context')
const wt = await agent(
  `Create a git worktree for issue ${issue.id} on branch issue/${issue.id} (git-wt skill). ` +
  `Read the issue (${issue.issueRef}) and the related code. Return {worktree, branch, context}.`,
  { label: 'context', phase: 'Context',
    schema: { type: 'object', required: ['worktree', 'branch', 'context'],
      properties: { worktree: { type: 'string' }, branch: { type: 'string' }, context: { type: 'string' } } } })
const ANGLES = ['root cause & affected components', 'constraints & protected domains',
                'existing utilities to reuse', 'edge cases & failure modes']
const analysis = (await parallel(ANGLES.map(a => () =>
  agent(`Analyze issue "${issue.title}" from this angle: ${a}. ` +
    `Spec: ${issue.spec}. Context: ${wt.context}. Return concise findings.`,
    { label: `analyze:${a}`, phase: 'Context' })))).filter(Boolean).join('\n\n')

// 3. plan
phase('Plan')
let plan = await agent(
  `Write a short, testable implementation plan for issue "${issue.title}". ` +
  `Spec: ${issue.spec}. Analysis:\n${analysis}\nFavor the smallest change that works (Tidy-First).`,
  { label: 'plan', phase: 'Plan' })

// 4. refine the plan until every plan axis >= 80 (with spikes when feasibility/risk lags)
const PLAN_AXES = [
  { key: 'spec-fit',     prompt: 'Does the plan resolve the issue, nothing missing or extra? KPI: acceptance criteria addressed (target 100%; judgement if fuzzy).' },
  { key: 'feasibility',  prompt: 'Can this be built as described against the real codebase/APIs? KPI: unresolved feasibility unknowns (target 0 — spike to resolve).' },
  { key: 'architecture', prompt: 'Macro: fits existing boundaries, layering, dependency direction? KPI (judgement, pre-code): planned circular deps / direction violations (target 0).' },
  { key: 'design',       prompt: 'Micro: do the intended interfaces/types/APIs make sense (encapsulation, invariants, cohesion)? KPI (judgement, pre-code): unsound interface/type choices (target 0).' },
  { key: 'simplicity',   prompt: 'Smallest change that works? Structural vs behavioral separated? KPI (judgement): net new abstractions/modules beyond need (target: none speculative).' },
  { key: 'risk',         prompt: 'Blast radius, protected domains, rollback. KPI: blast-radius modules; reversibility (irreversible op / data migration → DR); protected domains → DR.' },
  { key: 'testability',  prompt: 'Can each step be verified test-first? KPI: plan steps with a defined test (target 100%).' },
]
const planResult = await refineUntilScored('plan', PLAN_AXES,
  (a) => `Review this PLAN on the "${a.key}" axis. ${a.prompt}\nPlan:\n${plan}\n` +
         `Return {axis:'${a.key}', score, confidence, findings}.`,
  async (confirmed, lagging, round) => {
    const needsSpike = lagging.some(r => r.axis === 'feasibility' || r.axis === 'risk')
    if (needsSpike) {
      const spikes = (await parallel(Array.from({ length: MAX_SPIKES }, (_, i) => () =>
        agent(`Spike approach #${i} for: ${issue.spec}. In a THROWAWAY git worktree (git-wt), ` +
          `build the smallest prototype that answers the open feasibility/risk question and ` +
          `measure it. Return {approach, evidence}.`,
          { label: `plan:spike:${i}:r${round}`, phase: 'RefinePlan' })))).filter(Boolean)
      plan = await agent(`Compare these spikes, pick the best by evidence, and fold the ` +
        `conclusion into the plan while addressing ${JSON.stringify(confirmed)}. ` +
        `Discard the spike code — keep only the conclusion. Spikes: ${JSON.stringify(spikes)}\n` +
        `Old plan:\n${plan}\nReturn the revised plan.`, { label: `plan:fix:r${round}`, phase: 'RefinePlan' })
    } else {
      plan = await agent(`Revise the plan to address these findings: ${JSON.stringify(confirmed)}\n` +
        `Old plan:\n${plan}\nReturn the revised plan.`, { label: `plan:fix:r${round}`, phase: 'RefinePlan' })
    }
  }, 'RefinePlan')

// 5. implement test-first in the issue worktree
phase('Implement')
await agent(`In worktree ${wt.worktree} on branch ${wt.branch}, implement this plan ` +
  `test-first (tdd skill): ${plan}. Return when tests pass.`, { label: 'impl', phase: 'Implement' })

// 6. review + fix the implementation until every impl axis >= 80
const IMPL_AXES = [
  { key: 'correctness',  prompt: 'Does it do what the spec promises, including edge cases? KPI: tests green AND a test fails on pre-change behavior (gates); mutation score (target >= 70%).',
    agentType: 'pr-review-toolkit:code-reviewer' },
  { key: 'spec-fit',     prompt: 'Anything missing or out of scope vs the issue? KPI: acceptance-criteria coverage (target 100%) and out-of-scope changes (target 0).' },
  { key: 'coverage',     prompt: 'Tests adequate; a test fails on pre-change behavior? KPI: diff coverage % (target >= 80) and new uncovered branches (gate, target 0).',
    agentType: 'pr-review-toolkit:pr-test-analyzer' },
  { key: 'security',     prompt: 'Protected domains, unsafe handling? KPI: SAST + secret-scan + dependency-vuln findings (gate, target 0); protected-domain change → DR.',
    agentType: 'pr-review-toolkit:silent-failure-hunter' },
  { key: 'performance',  prompt: 'Hot paths, complexity, allocations, N+1? KPI: if a benchmark exists, latency/throughput delta vs baseline (<= budget); else complexity of changed hot paths + DB query count; added N+1 (gate, target 0).' },
  { key: 'architecture', prompt: 'Macro: fits boundaries and dependency direction; no leaky coupling? KPI: new circular deps (gate, 0), dependency-direction/layering violations (gate, 0), fan-in/out vs threshold (reuse pr-dependency-review).' },
  { key: 'design',       prompt: 'Micro: interface/type/API quality, encapsulation, invariants, cohesion? KPI: encapsulation/invariant/enforcement ratings; unintended public-API surface change (gate, 0).',
    agentType: 'pr-review-toolkit:type-design-analyzer' },
  { key: 'simplicity',   prompt: 'Smallest clear implementation; no needless abstraction? KPI: cyclomatic complexity per changed fn (target <= 10), max nesting depth, duplication.' },
  { key: 'ai-pr-checks', prompt: 'Run pr-dependency-review references/ai-pr-checks.md failure modes. KPI: failure-mode hits (target 0).' },
]
const implResult = await refineUntilScored('impl', IMPL_AXES,
  (a) => `Review the diff in worktree ${wt.worktree} against spec "${issue.spec}" on the ` +
         `"${a.key}" axis. ${a.prompt} Do not assume the author was right. ` +
         `Return {axis:'${a.key}', score, confidence, findings:[{issue,severity,fixingPlan,fileLine}]}.`,
  async (confirmed) => {
    await agent(`In worktree ${wt.worktree}, address these VERIFIED findings, keeping the spec ` +
      `fixed: ${JSON.stringify(confirmed)}.`, { label: 'impl:fix', phase: 'ReviewImpl' })
  }, 'ReviewImpl')

// 7. open a DRAFT PR (never merge)
phase('PR')
const blocked = !planResult.passed || !implResult.passed
const pr = await agent(`In worktree ${wt.worktree} on branch ${wt.branch}, push and open a ` +
  `DRAFT PR (gh pr create --draft) with a body following the pr-body skill. ` +
  `${blocked ? 'List the axes that did not reach the threshold in the PR body.' : ''} ` +
  `Return {url}.`, { label: 'pr', phase: 'PR' })

return { pr, planScores: planResult.scores, implScores: implResult.scores, blocked }
```

Why it is shaped this way:

- **One script, sequential stages** — there is one issue, so no `pipeline`/`/goal`. The
  concurrency is *within* a round: axis reviewers in `parallel`, then finding verifiers in
  `parallel`.
- **`while` bounded by `MAX_ROUNDS`** — the loop re-reviews until every axis is ≥ 80, but
  a stuck axis cannot loop forever: it exits `blocked` and surfaces as a DR.
- **Fresh reviewers and verifiers** — every reviewer/refuter is a separate agent that
  sees the artifact + spec only, never the maker's reasoning (`maker-checker`). An axis
  with no `agentType` still spawns the **generic workflow subagent** (fresh context) — it
  is not run in the main session; `agentType` only swaps a purpose-built reviewer in for
  the generic one. So the `maker-checker` guarantee holds for every axis, specialized or not.
- **Verify before fix** — only confirmed findings drive a change, so hallucinated issues
  neither cause churn nor block termination.

## Safety rails

Reuses `loop-automation`'s rails — a scored loop still makes unattended mistakes:

- **Draft PR only — never merge.** A human owns the merge.
- **Bound every loop.** `MAX_ROUNDS` per scored loop; a stuck axis is logged blocked, not retried forever.
- **Cap spikes.** `MAX_SPIKES` and throwaway worktrees, so exploration cannot balloon.
- **Verify, don't self-grade.** Reviewers and refuters are separate agents (`maker-checker`).
- **Escalate, don't guess.** A protected-domain conflict, or an axis that cannot reach the
  threshold, surfaces as a DR (`decision-required`) — not an autonomous decision.

## Integration

- **git-wt** — one worktree for the issue (step 1); throwaway worktrees for spikes (step 4.3).
- **tdd** — implement test-first (step 5); the coverage axis checks a test fails pre-change.
- **maker-checker** — the engine behind every review and the refute step (4.2 / 6.2).
- **pr-review-toolkit** (`code-reviewer`, `pr-test-analyzer`, `silent-failure-hunter`,
  `type-design-analyzer`) — per-axis reviewers in the impl loop.
- **pr-dependency-review** — its `references/ai-pr-checks.md` is the *ai-pr-checks* axis.
- **pr-body** — the draft PR description (step 7).
- **loop-state** — persist axis scores per round in `plan.md` if the run spans sessions.
- **issue-loop** — the batch sibling; it delegates each issue to this skill via the
  Workflow `workflow()` hook (this script takes one issue via `args` and never calls
  `workflow()` itself, so it nests cleanly). Use `issue-loop` for many issues, this skill
  for one done deeply.
- **decision-required** — escalation path for protected domains and stuck axes.
