# Loop-engineering review rubric

KPI rubric for the skills loop-engineering review (see plan.md). Frozen at the start of a review session; scores are comparable at the axis level across waves. Axis names match the wave-1 baseline (72/58/66/60/63/70).

## Scoring

- Each axis has 5 checks. Each check scores 0 (fails), 10 (partial), or 20 (holds across the skill set).
- Axis score = sum of its checks (0–100). Gate: every axis ≥ 80.
- Two scores per axis each round:
  - **current** — the skill set as it is on disk today.
  - **plan** — projected state if every item in plan.md `## Next` lands as written.
- Reviewers are fresh-context subagents, one per axis (maker-checker). Output contract: one fenced json block — `{"axis", "current_score", "plan_score", "confidence" (0-1), "checks": [{"id", "current", "plan", "evidence"}], "findings": [{"summary", "evidence", "fix", "effort"}]}`. One re-ask on parse failure, then the axis is blocked for the round.
- Stop: all six plan scores ≥ 80. Hard cap: 4 rounds, then report honestly with gaps.

## Axes

### 1. Loop closure

Every process skill that opens an iterate cycle actually closes it: do → check → fix → re-check.

- LC1: Each loop skill's cycle ends by re-running the same check that opened it — not a one-shot review.
- LC2: Findings and fixes feed the next iteration; no fire-and-forget review steps.
- LC3: Production is separated from verification where correctness matters (maker-checker applied or referenced).
- LC4: Loops that produce artifacts persist them every iteration, not only at the end.
- LC5: No skill describes a loop it cannot drive with mechanisms that exist here (Agent fan-out, ralph-loop, /loop + ScheduleWakeup, CronCreate, Routines, Tasks).

### 2. Termination & triggers

Loops stop on objective predicates; skills fire when they should.

- TT1: Every loop skill states an explicit stop predicate (threshold, all-items-done, zero-new-findings).
- TT2: Every loop skill bounds iterations or retries — a hard cap or an escalation path; no unbounded grind.
- TT3: Stuck paths are defined: what happens when the gate never passes (block, DR, honest report).
- TT4: Frontmatter descriptions carry concrete trigger phrases, and anti-triggers where confusable.
- TT5: Overlapping triggers between sibling skills are disambiguated — each names when to use the other.

### 3. State & resumability

Iteration state survives compaction, /clear, and session death.

- SR1: Loop skills mandate on-disk state (plan.md via plan-state), not conversation memory.
- SR2: The state format lets a fresh session resume without re-planning.
- SR3: Dead ends and decisions are recorded (Do NOT / DR conventions) so loops do not relive them.
- SR4: Long or unattended loops handle compaction explicitly (re-read state each iteration).
- SR5: Handoff paths between contexts exist and are cross-referenced correctly (plan.md same-repo; replay-prompt cross-repo/machine).

### 4. Measurability

Gates are machine-checkable or checklist-anchored, never vibes.

- ME1: Scored reviews use a defined schema (score, confidence, findings) with a parse contract.
- ME2: Thresholds are explicit numbers, consistent across skills.
- ME3: Rubrics are checklist-anchored — what earns the score is written down.
- ME4: Skills that need evals have them (evals/ dir with scenarios incl. a near-miss), per the W10 convention.
- ME5: Deterministic checks (lint, CI) replace LLM judgment wherever possible (W11).

### 5. Composability

Skills reference each other correctly and chain cleanly.

- CO1: Zero dangling skill references — every referenced skill exists in the set, plugins, or built-ins.
- CO2: Each loop skill states what it composes with, and the division of labor is non-overlapping.
- CO3: Every rule has exactly one owner (single-source; e.g. commit gates), others link to it.
- CO4: Overlap with installed plugins (superpowers, pr-review-toolkit, ralph-loop, crit) is acknowledged and disambiguated.
- CO5: Orchestration locus is consistent: the main session dispatches subagents; nothing assumes unverified nesting.

### 6. Overhead

Skills are lean; ceremony is proportional to value.

- OH1: Line budget respected (≤ 300 lines per SKILL.md).
- OH2: No dead or stale content (removed mechanisms, duplicated sections).
- OH3: Cost proportional to frequency: often-fired skills are short; long ones are rarely-needed depth.
- OH4: No skill duplicates a built-in or plugin that already does the job.
- OH5: Redundant skills are identified with a justified keep/remove call.

## Standing constraints (user decisions — findings must respect these)

- MAX_PARALLEL = 10 is a user decision; do not report it as a defect.
- No Workflow-tool or /goal orchestration anywhere.
- golang-pr-review is out of scope entirely.
- empirical-prompt-tuning stays third-party-pinned; quirks are accepted (DR 2026-07-06).
- Deliberate deferrals (pr-body self-check; safety-rails ×3 cross-referencing; .agents/skills codex portability) are not gaps.
