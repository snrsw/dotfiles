---
name: issue-resolver
description: >
  Drive ONE issue from raw context to a reviewed, fixed implementation behind a
  draft PR, with quality enforced by scored multi-axis review loops. Use when the
  user hands over a single issue (a GitHub issue URL/number, or a written spec) and
  wants it "done properly", "resolved end to end", "taken to a PR with quality
  gates", or "reviewed until it's actually good" — not a quick patch. Each review
  runs as a fresh subagent that owns one axis and returns a scored verdict (axis
  score, confidence, and findings each with a fix plan); the loop refines until
  every axis scores >= 80, at both the plan and the implementation stage, and
  verifies each finding before acting on it. This is the deep, single-issue
  sibling of `issue-loop` (the batch wrapper that delegates each issue here) —
  prefer this skill for one issue done thoroughly, and `issue-loop` for a batch.
---

# issue-resolver

Take a single issue and drive it to a draft PR through two **scored review loops** —
one over the plan, one over the implementation. The skill reviews **one** issue on
many axes, each scored 0–100, and keeps refining until **every axis is ≥ 80**.
Findings are independently **verified before** they are acted on, and the plan
stage can run **spikes** to resolve unknowns with evidence instead of guesswork.

## The loop's shape

```
1. get context        (issue worktree; read the issue, the repo, the related code)
2. analyze            (fan-out subagents, one per angle)
3. plan               (draft a short, testable plan)
4. refine plan  — scored loop until every plan axis >= 80:
     4.1 review: one fresh subagent per axis -> {axis, score, confidence, findings}
     4.2 verify: a fresh subagent tries to REFUTE each finding -> keep only confirmed
     4.3 fix the plan; if an axis needs evidence, spike it in a throwaway worktree,
         compare spikes, fold the conclusion back into the plan
5. implement          (subagent, test-first, in the issue worktree)
6. review+fix  — same scored loop until every impl axis >= 80:
     6.1 review: one fresh subagent per axis
     6.2 verify: refute each finding -> keep only confirmed
     6.3 fix the confirmed findings
7. open a DRAFT PR (never merge); report final scores and any blocked axis
```

## Mechanism mapping (read this first)

The loop runs in the **main session** — the session that triggered this skill —
which owns the gates, the state file, and every dispatch. It deliberately uses
plain `Agent` fan-out (the `/goal` built-in and opt-in `Workflow` tool exist —
see `loop-automation` — but this loop requires neither). Fresh context comes
from **`Agent`-tool subagents**, one per role:

| Role | Dispatch |
|---|---|
| Orchestrator (the loop, the gates, `plan.md`) | the main session itself — never a subagent, so reviewer fan-out is always available |
| Axis reviewers | one fresh subagent per axis, in parallel (one message, multiple Agent calls) |
| Finding refuters | one fresh subagent per finding, in parallel |
| Implementer | one subagent, test-first, in the issue worktree (background when the session has other work) |
| Spikes | subagents with `isolation: "worktree"` — throwaway trees |

Wired-in constants — state them in the dispatches, change them only deliberately:

- **MAX_PARALLEL = 10.** Never more than 10 concurrent subagents, shared across
  the whole loop (reviewers + refuters + background implementers). Batch the
  dispatches to stay under it.
- **MAX_ROUNDS = 3** per scored loop, **MAX_SPIKES = 2.** A stuck axis exits
  `blocked` and raises a DR — it never loops forever.
- **`plan.md` is the loop's state — mandatory, not optional.** After every round,
  record the round number, per-axis scores, and confirmed findings under
  `## Notes` (`plan-state`). A fresh session must be able to resume mid-loop from
  the file alone.
- Reviewers and refuters receive only the spec + the artifact — never the maker's
  reasoning (`maker-checker`).

## The scored review contract (prompt + parse)

Subagent output cannot be schema-constrained, so the contract is enforced by
prompt and parsed from the reply. Append this block verbatim to EVERY reviewer
dispatch:

```
End your reply with exactly one fenced json block:
{"axis":"<axis>","score":<0-100>,"confidence":<0-1>,
 "kpi":{"name":"...","value":"...","target":"..."},
 "findings":[{"issue":"...","severity":"critical|high|medium|low",
              "fixingPlan":"...","fileLine":"..."}]}
Gate-vs-grade: anchor the score on the measured KPI and state your mapping.
File any GATE breach (failing test, new uncovered branch, SAST/secret/vuln hit,
new circular dep, unintended public-API surface change, added N+1,
protected-domain change, or any per-axis gate) as a `critical` finding even if
the score is otherwise high — a high score never buys back a gate breach.
If no hard metric fits, set kpi.name="judgement" and say so.
```

Parse the final fenced json block of the reply. If it fails to parse, re-ask that
reviewer once ("return only the json block"); on a second failure, mark the axis
blocked for this round. An axis passes only when its `score >= 80` **and** no
confirmed critical/high finding remains. `confidence` is the reviewer's
self-report and advisory only — the refute step is the real gate against false
findings.

Refuter dispatch, one finding per subagent:

```
Try to REFUTE this review finding — assume it may be wrong; default to not
confirmed if unsure. Finding: <finding json>.
End your reply with exactly one fenced json block:
{"confirmed":true|false,"why":"..."}
```

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

**When a KPI needs an environment you may not have.** Some KPIs require a runtime the repo
may lack — a browser engine (Safari/WebKit), a specific OS, a populated DB, a mutation
runner. If the metric cannot be measured, do **not** fabricate a pass: fall back to the
named evidence (a test that exercises the exact path), and if even that is impossible, score
on judgement and file the axis **blocked → DR** rather than green. An unverifiable gate is
not a passed gate.

These are the *defaults*; a reviewer may report a better axis-specific metric for the
issue at hand. The point is that the number is earned, not asserted.

## Default axes (hybrid: these + any issue-specific ones)

Start from these and **add** axes the issue obviously needs (e.g. "migration safety",
"backwards compat", "i18n"). Add a dedicated axis only when the concern has its **own
measurable gate KPI that no default axis already gates** — otherwise fold it into the
nearest default (`risk`, `correctness`, …) rather than duplicating. An added plan-phase
axis that needs evidence to score honestly can be marked `spikes: true` to drive a
spike, the same way `feasibility` and `risk` do.

- **Plan phase** — *spec-fit* (does the plan actually solve the issue?), *feasibility*
  (can it be built as described? often the one that needs a spike; `spikes: true`),
  *architecture* (macro: fits existing module boundaries, layering and dependency
  direction), *design* (micro: do the intended interfaces/types/APIs make sense?),
  *simplicity / Tidy-First* (smallest change that works; structural vs behavioral
  separated), *risk & blast-radius* (`spikes: true`), *testability* (can each step be
  verified test-first?).
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

Where a purpose-built reviewer exists, dispatch it for the axis:
`pr-review-toolkit:code-reviewer` (correctness),
`pr-review-toolkit:pr-test-analyzer` (coverage),
`pr-review-toolkit:silent-failure-hunter` (security),
`pr-review-toolkit:type-design-analyzer` (design). Every other axis gets a fresh
`general-purpose` subagent. Either way the reviewer is a separate fresh-context
agent — the `maker-checker` guarantee holds for every axis.

## Verify-each-review (why the refute step matters)

A reviewer that both finds and confirms its own issue is biased toward "I was right" —
the same self-grading failure `maker-checker` warns about. So before any fix, a **fresh**
agent receives one finding and is asked to *refute* it ("assume this may be wrong"). Only
confirmed findings drive a fix. This stops the loop from acting on hallucinated issues
and from being gamed into never terminating by a reviewer that keeps inventing problems.

## Spikes (plan phase only)

When a lagging axis — usually *feasibility* or *risk* — cannot be scored honestly without
evidence ("will this approach be fast enough / fit the existing API?"), spawn 1–N spike
subagents (`Agent` with `isolation: "worktree"`), each in a **throwaway** worktree, to
build the smallest prototype that answers the question and measure it against a stated
metric. Compare the spikes, fold the winning **conclusion** into the plan, and discard the
spike code — only the conclusion survives. Cap the number of spikes (`MAX_SPIKES`) so this
does not balloon. Which axes may trigger a spike is explicit: an axis drives one when it
is marked `spikes: true` (defaults: *feasibility*, *risk*) — an issue-specific axis opts
in the same way.

Spikes are **plan-phase only** — they settle *pre-code* unknowns. A KPI that is only
measurable once code exists (perf delta, mutation score, coverage) is measured by the
impl-phase reviewer itself — it runs the tests/benchmark as part of its review — not by a
spike. So a perf axis spikes in the plan phase to set a baseline/target, then the impl-phase
performance reviewer measures the real change against that target.

## Procedure

1. **Context.** Create a worktree for the issue (`git-wt`, branch `issue/<id>`,
   `id` = short slug). Read the issue and the related code. Start `plan.md` in the
   worktree root with the issue's acceptance criteria.
2. **Protected-domain gate.** If the issue touches auth, payments, data deletion
   or migration, security config, infra/deployment, or a breaking API change,
   raise a DR up front (`decision-required`) and fold the resolution into the plan
   and the PR — never decide autonomously.
3. **Analyze.** Fan out one subagent per angle, in parallel: root cause & affected
   components; constraints & protected domains; existing utilities to reuse; edge
   cases & failure modes.
4. **Plan.** Draft a short, testable plan — the smallest change that works
   (Tidy-First), one verifiable step per item.
5. **Refine the plan** — scored loop, at most MAX_ROUNDS:
   1. Dispatch one reviewer per plan axis, in parallel, each with the contract
      block and its axis prompt.
   2. Dispatch one refuter per finding, in parallel; keep only confirmed findings.
   3. Every axis ≥ 80 and no confirmed critical/high left → exit the loop.
      Otherwise revise the plan against the confirmed findings. If a lagging axis
      is marked `spikes: true`, run up to MAX_SPIKES spike subagents in throwaway
      worktrees, compare their evidence, fold the winning conclusion into the
      plan, and discard the spike code.
   4. Record the round's scores and confirmed findings in `plan.md`. If the round
      limit is hit with an axis still failing, mark it blocked and raise a DR.
6. **Implement** the refined plan test-first (`tdd`) in the issue worktree — a
   subagent; run it in the background when the session has other work.
7. **Review the implementation** — the same scored loop over the impl axes; the
   fix action applies confirmed findings in the worktree, keeping the spec fixed.
8. **Draft PR.** Push the branch and open a draft PR (`pr-body`). Never merge.
   List every blocked axis and any DR in the PR body. Report the final scores.

## Safety rails

Reuses `loop-automation`'s rails — a scored loop still makes unattended mistakes:

- **Draft PR only — never merge.** A human owns the merge.
- **Bound every loop.** MAX_ROUNDS per scored loop; a stuck axis is logged blocked
  and raised as a DR, not retried forever.
- **Cap cost.** MAX_PARALLEL = 10 shared across all concurrent subagents;
  MAX_SPIKES caps exploration; spikes always run in throwaway worktrees.
- **Verify, don't self-grade.** Reviewers and refuters are separate fresh-context
  agents (`maker-checker`); the orchestrator never scores its own artifact.
- **Escalate, don't guess.** A protected-domain conflict, or an axis that cannot
  reach the threshold, surfaces as a DR (`decision-required`) — not an autonomous
  decision.

## Integration

- **git-wt** — one worktree for the issue (step 1); throwaway worktrees for spikes.
- **tdd** — implement test-first (step 6); the coverage axis checks a test fails
  on pre-change behavior.
- **maker-checker** — the discipline behind every review and the refute step.
- **pr-review-toolkit** (`code-reviewer`, `pr-test-analyzer`,
  `silent-failure-hunter`, `type-design-analyzer`) — purpose-built per-axis
  reviewers in the impl loop.
- **pr-dependency-review** — its `references/ai-pr-checks.md` is the
  *ai-pr-checks* axis.
- **pr-body** — the draft PR description (step 8).
- **plan-state** — `plan.md` in the issue worktree is the loop's mandatory state:
  per-round axis scores, confirmed findings, blocked items.
- **issue-loop** — the batch wrapper: it delegates each issue to this skill and
  adds the outer until-done loop; its lightweight triage mode reviews on a single
  severity axis instead of the full scored set. Use `issue-loop` for many issues,
  this skill for one done deeply.
- **decision-required** — escalation path for protected domains and stuck axes.
