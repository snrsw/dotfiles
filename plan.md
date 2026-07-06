# Skills loop-engineering refactor

A loop-engineering review of the 17 nix-managed skills, run as a scored loop: six frozen axes with checklist KPIs (review-rubric.md), fresh-context reviewer subagents per axis (maker-checker), plan refactored each round, stop when every axis's plan-projected score is ≥ 80 (hard cap 4 rounds). Round 1 measured the pre-refactor plan at 2 failing axes; `## Next` below is the refactored plan responding to round-1 findings. All DRs resolved — see decisions.md.

## Review scores (gate: every plan-projected axis ≥ 80)

| axis | wave-1 baseline | R1 current | R1 plan (pre-refactor) | R2 plan |
|---|---|---|---|---|
| loop closure | 72 | 70 | 90 | — |
| termination & triggers | 58 | 50 | **50 ✗** | — |
| state & resumability | 66 | 90 | 80 (regression from 90) | — |
| measurability | 60 | 60 | **70 ✗** | — |
| composability | 63 | 80 | 90 | — |
| overhead | 70 | 70 | 80 | — |

Scores are measured by fresh reviewer subagents against review-rubric.md each round — never hand-edited. The R1 plan column scored the old W4–W11; the refactor below answers it.

## Done

- [x] W0 — mechanism inventory verified: no `Workflow` tool, no `/goal`; real engines are Agent fan-out, ralph-loop, /loop+ScheduleWakeup, CronCreate, Routines, Tasks — verified in this environment via ToolSearch; re-confirm the subagent-nesting fast path interactively before relying on it
- [x] W1+W6 — issue-resolver and issue-loop rebuilt on Agent fan-out (prompt+parse contract, MAX_PARALLEL=10, main-session orchestration, mandatory plan.md state, explicit outer stop predicate); dead Workflow JS deleted — 8e2c579
- [x] W2 — replay-prompt dangling references fixed — 913c2fc
- [x] W3 — loop-automation engine table updated (ralph-loop, /loop; stale wording refreshed) — 388260b
- [x] R1 — round-1 six-axis review (6 fresh reviewer subagents, facts-only inventory as shared ground truth); 2 axes below gate; plan refactored: W4/W8/W10/W11 sharpened, W12–W16 added — this commit

## Next

- [ ] W7 — single-source the commit gates in tidy-first (it owns the never-commit-standalone-Red rule); tdd links to it; commit-message stays format-only. Check: the three gate conditions appear in exactly one file
- [ ] W9 — plan-state: bound retries — item fails → switch to debug (existing path) → fix fails twice → Blocked/DR, move on. Check: the two-failure bound is stated in plan-state
- [ ] W14 — compaction-safe iteration: plan-state Execution gains step 0 "re-read plan.md at the top of every iteration (it may have been compacted or edited concurrently)"; issue-resolver (loop steps) and issue-loop (batch step) reference it. Check: all three files carry the re-read rule
- [ ] W13 — greppable termination surface: every process skill (list in W10) carries labeled `Stop:` / `Bound:` / `Stuck:` lines. tdd's become objective (Stop: test list empty ∧ suite green; Bound: same test red after 3 attempts → Stuck: switch to debug). debug gets an investigation budget (Bound: 5 hypotheses without progress or unreproducible → Stuck: DR + honest report). In issue-resolver, markers REPLACE existing prose lines (budget constraint, see Notes). Check: every process skill greps all three markers
- [ ] W15 — scored-verdict contract: maker-checker's checker returns one fenced json block (verdict pass/fail, findings with file:line, confidence) with the one-re-ask parse rule (same DR as issue-resolver); add the orchestration-locus line (the orchestrating/main session dispatches the checker; a subagent-maker hands the artifact up rather than nesting). replay-prompt Phase-4 scores are marked advisory-only with a deterministic pick rule (max total; tie → shorter prompt), never aggregated across contexts. Check: json contract + locus line present in maker-checker; "advisory" wording in replay-prompt
- [ ] W16 — replay-prompt loop closure: any Phase-5 revision re-runs the full Quality Checklist; Bound: ≤ 2 revision passes → Stuck: ship best variant with residual "no" items listed. Check: re-check loop with cap and stop present
- [ ] W12 — plugin-sibling disambiguation: add a one-line `Overlap:` note to tdd, debug, git-wt, plan-state, maker-checker naming the installed twin (superpowers:test-driven-development / systematic-debugging / using-git-worktrees / writing-plans+executing-plans; pr-review-toolkit + superpowers:requesting-code-review for maker-checker) and when to prefer each; log one keep/remove DR per pair in decisions.md recording what the repo skill adds (Kent-Beck CLAUDE.md conventions, git-wt CLI, plan.md contract, checker contract); any recommendation to disable a twin is a DR output for the user, not an action. Check: grep finds `Overlap:` in all 5 skills; decisions.md has 5 pair DRs
- [ ] W4 — adopt safe-lib-upgrade into the nix-managed skills dir (delete the hand-dropped `~/.claude/skills/safe-lib-upgrade/` first: real files collide with home-manager's recursive linking), sharpened per R1: add plan-state integration (persist breaking-change table, audit table, and addressed-gaps ledger to the repo-root plan.md so the human merge-gate pause and compaction are resumable; Integration section referencing plan-state), W13 termination markers (Stop: gaps = 0; Bound: a fix failing twice or convergence stalling → Stuck: Blocked/DR + honest report), and an `Overlap:` line vs maker-checker ("safe to merge" collision). Check: nix link works, old dir gone, skill greps Stop/Bound/Stuck + plan-state + Overlap
- [ ] W8 — japanese-technical-writing: append a revise loop with separation — a fresh-context checker subagent receives ONLY the manuscript + the section checklist (never the author's rationale) and returns violations with locations; write → check → fix → re-check; Stop: a pass with zero new violations; Bound: 3 passes → Stuck: DR + residual violations listed. Check: loop present with markers and maker-checker separation
- [ ] W10 — evals + ledgers: process-skill denominator is enumerated here = {issue-loop, issue-resolver, maker-checker, plan-state, debug, loop-automation, replay-prompt, tdd, tidy-first, japanese-technical-writing, safe-lib-upgrade}; ≤ 2 justified exclusions allowed, recorded in decisions.md (extract-skill-from-session is excluded now: proposal-only, no loop, its 6-criteria bar is its own check). Each covered skill gets `evals/evals.json` (3 scenarios, ≥ 1 near-miss, must parse) and `evals/ledger.md` (run record; runner = skill-creator plugin's eval runner). Required scenarios: plan-state "resume a half-done plan.md in fresh context without re-planning"; loop-automation near-miss "loop kept state in conversation memory and lost it on cold start". KPI: coverage = skills-with-valid-evals / denominator ≥ 80%, machine-computable. Check: coverage KPI computes green from the files alone
- [ ] W11 — skill-lint script + read-only GitHub Action (DR approved). Deterministic checks: (1) frontmatter name = dir; (2) skill-name refs resolve against a registry file checked into the repo (repo skills + managed extras + plugins + built-ins + subagent types; whitelists the empirical-prompt-tuning pin); (3) tool/mechanism refs against an allow-list config derived from the W0 inventory; (4) line budget warn > 270, fail > 300; (5) for process-skill-list members: evals.json parses with ≥ 1 near-miss and ledger.md exists; (6) termination surface: Stop/Bound/Stuck markers present (W13); (7) name-collision warn against the plugin sibling map (W12). Trigger-phrase quality stays warn-only (semantic). Action: PRs + weekly off-peak cron + workflow_dispatch kill switch, `permissions: contents: read`. KPIs emitted: dangling refs = 0, eval coverage %, budget violations, marker coverage. Check: lint green locally on the finished tree; Action lands read-only

## Blocked / DR

- (none — 7 DRs resolved 2026-07-06, logged in decisions.md)

## Notes

- MAX_PARALLEL = 10 is a user decision (DR); do NOT "correct" it back to 4.
- Do NOT: reintroduce Workflow-tool or /goal-based orchestration in any skill.
- Do NOT: touch golang-pr-review (user instruction — excluded from scope: no adopt, no refactor, no evals).
- Do NOT: change the review axes or rubric mid-loop (review-rubric.md is frozen; a moving yardstick lets the loop game itself to 80).
- Deferred deliberately (not unfinished work): pr-body self-check; safety-rails ×3 dedup (cross-referenced on purpose); .agents/skills codex-portability rewrite.
- empirical-prompt-tuning stays third-party-pinned (home.nix:127); skill-lint must whitelist it.
- Budget constraint: issue-resolver (281) and pr-dependency-review (284) sit near the 300-line cap — new content for them goes to references/, and W13 markers replace prose lines rather than adding.
- Scope rulings for scoring (R1, aggregator-confirmed): installed plugin siblings are in-scope for trigger/overlap checks; tdd and debug count as loop skills; W4 pulls safe-lib-upgrade into the managed set it is scored with.
- Review-loop artifacts: review-rubric.md (frozen axes + KPIs), decisions.md (DR log). Reviewer scores land only in the table above, from subagent JSON.
