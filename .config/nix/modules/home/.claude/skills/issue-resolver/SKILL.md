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

Orchestration runs on `Agent`-tool fan-out — the no-Workflow-engine decision is
stated in `loop-automation`. The loop runs in the
**main session** — the session that triggered this skill — which owns the gates,
the state file, and every dispatch. Fresh context comes from **`Agent`-tool
subagents**, one per role:

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

## Axes and KPIs (read at dispatch time)

Each reviewer owns one axis and anchors its score on a measured KPI — gates
(one breach files a `critical` finding, whatever the number) vs graded metrics
(distance from target drives the score). Before constructing reviewer
dispatches (procedure steps 5 and 7), read:

- `references/axes.md` — the default plan-phase and impl-phase axes, when to add
  an issue-specific axis, and which purpose-built `pr-review-toolkit` reviewer
  owns which axis.
- `references/kpis.md` — the default KPI and target per axis, gate-vs-graded
  scoring, and the rule for unmeasurable KPIs (never fabricate a pass; fall back
  to named evidence or file the axis blocked → DR).

## Verify-each-review (why the refute step matters)

A reviewer that both finds and confirms its own issue is biased toward "I was right" —
the same self-grading failure `maker-checker` warns about. So before any fix, a **fresh**
agent receives one finding and is asked to *refute* it ("assume this may be wrong"). Only
confirmed findings drive a fix. This stops the loop from acting on hallucinated issues
and from being gamed into never terminating by a reviewer that keeps inventing problems.

## Spikes (plan phase only)

When a plan axis marked `spikes: true` (defaults: *feasibility*, *risk*) cannot
be scored honestly without evidence, run up to MAX_SPIKES spike subagents in
throwaway worktrees and fold the winning **conclusion** — never the code — back
into the plan. Read `references/spikes.md` before dispatching one. Impl-phase
KPIs (perf delta, mutation score, coverage) are measured by the impl reviewer,
not a spike.

## Procedure

1. **Context.** Create a worktree for the issue (`git-wt`, branch `issue/<id>`,
   `id` = short slug). Read the issue and the related code. Start `plan.md` in the
   worktree root with the issue's acceptance criteria.
2. **Protected-domain gate.** If the issue touches a protected domain
   (`decision-required` lists them), raise a DR up front and fold the resolution
   into the plan and the PR — never decide autonomously.
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

The five rails below are shared word-for-word with `loop-automation` and
`issue-loop` — only the constants clause after each bold lead differs:

- **Open draft PRs, never merge.** A human owns every merge.
- **Bound every loop.** MAX_ROUNDS per scored loop; a stuck item is logged blocked and raised as a DR, not retried forever.
- **Cap cost — parallelism is the trap.** MAX_PARALLEL = 10 shared across all concurrent subagents; MAX_SPIKES caps exploration; spikes always run in throwaway worktrees.
- **Verify, don't self-grade.** Reviewers are separate fresh-context agents (`maker-checker`); no agent scores its own artifact.
- **Escalate, don't guess.** Protected domains and unreachable thresholds surface as DRs (`decision-required`), not autonomous decisions.

## Response style

The scored contract is machine-parsed, but its string fields are read by a human
the moment the loop stalls, and the closing report is read every time. The
`response-style` rule applies to both.

- **`reason` and `issue` strings carry one meaning each**, in plain words. A
  finding that bundles two defects splits into two findings, or the reviser fixes
  one and the score never clears.
- **Each `fix` is actionable on its own** — no back-jumps to another finding for
  the context needed to apply it.
- **A score is a fact, not a hedge.** The anchored deductions produce it, so state
  it unhedged and put genuine uncertainty in `confidence` where the refute step can
  act on it. Hedging inside `reason` hides the doubt from the loop.
- **The closing report leads with the outcome** — landed or blocked, and the PR URL
  — before axis scores and round counts.
- **The PR body itself follows `pr-body`**, which carries these rules for PR text;
  do not restate them differently here.

