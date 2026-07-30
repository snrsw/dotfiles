# KPI anchoring for scored reviews

Read this when constructing reviewer dispatches — it defines how a reviewer
earns its score instead of asserting it.

A 0–100 score means little unless it is anchored on something measurable. Where an axis
has a real metric, the reviewer should **measure it, report it as `kpi`, and let the
distance from target drive the score** — the same discipline `pr-dependency-review` uses
(findings carry a measured value, not an adjective). Where no hard metric fits (e.g.
spec-fit on a fuzzy issue, or any plan-phase axis before code exists), score on judgement
and say so (`kpi.name = 'judgement'`) — don't fabricate a number.

## Gates vs graded KPIs

Some KPIs are *graded* — coverage %, complexity, perf delta —
and map smoothly onto the score (roughly: at-or-past target → ~90+, far from it → low;
state the rule you used so it is reproducible). Others are *gates* — a single breach means
the axis is not done, regardless of an otherwise high score (0 failing tests, 0 circular
deps, 0 secrets, protected-domain → DR). **File every gate breach as a `critical`
finding**, so it blocks through the "no confirmed critical/high" gate independent of the
number. A high score never buys back a gate breach.

## Default KPI per axis (target in parentheses; ⛔ = gate)

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

## When a KPI needs an environment you may not have

Some KPIs require a runtime the repo may lack — a browser engine (Safari/WebKit), a
specific OS, a populated DB, a mutation runner. If the metric cannot be measured, do
**not** fabricate a pass: fall back to the named evidence (a test that exercises the
exact path), and if even that is impossible, score on judgement and file the axis
**blocked → DR** rather than green. An unverifiable gate is not a passed gate.

These are the *defaults*; a reviewer may report a better axis-specific metric for the
issue at hand. The point is that the number is earned, not asserted.
