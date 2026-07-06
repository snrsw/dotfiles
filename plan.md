# Skills loop-engineering refactor

A loop-engineering review scored the skill set on 6 axes — loop closure, termination & triggers, state & resumability, measurability, composability, overhead (baseline 72/58/66/60/63/70). This plan raises every axis to ≥ 80. All 5 DRs are resolved — see decisions.md.

## Done

- [x] W0 — mechanism inventory verified: no `Workflow` tool, no `/goal`; real engines are Agent fan-out, ralph-loop, /loop+ScheduleWakeup, CronCreate, Routines, Tasks — verified in this environment via ToolSearch; re-confirm the subagent-nesting fast path interactively before relying on it
- [x] W1+W6 — issue-resolver and issue-loop rebuilt on Agent fan-out (prompt+parse contract, MAX_PARALLEL=10, main-session orchestration, mandatory plan.md state, explicit outer stop predicate); dead Workflow JS deleted — 8e2c579
- [x] W2 — replay-prompt dangling references fixed — 913c2fc
- [x] W3 — loop-automation engine table updated (ralph-loop, /loop; stale wording refreshed) — 388260b

## Next

- [ ] W4 — adopt safe-lib-upgrade into the nix-managed skills dir. Delete the hand-dropped `~/.claude/skills/safe-lib-upgrade/` first: real files collide with home-manager's recursive linking ("existing file in the way")
- [ ] W7 — single-source the commit gates in tidy-first (it owns the never-commit-standalone-Red rule); tdd links to it; commit-message stays format-only. Check: the three gate conditions appear in exactly one file
- [ ] W8 — japanese-technical-writing: append a revise loop — write → checklist pass per section → fix → repeat until a pass finds no new violation; fresh-context checker for book manuscripts
- [ ] W9 — plan-state: bound retries — item fails → switch to debug (existing path) → fix fails twice → Blocked/DR, move on
- [ ] W10 — evals.json (3 scenarios each, incl. 1 near-miss) for issue-loop, maker-checker, plan-state, debug, loop-automation, replay-prompt. Check: process-skill eval coverage ≥ 80%
- [ ] W11 — skill-lint script + read-only GitHub Action (DR approved). Checks: frontmatter name = dir; description with trigger phrases; skill-name refs resolve; referenced tools/mechanisms exist; required sections for process skills (stop condition, verification step); line budget warn > 300; evals present. KPIs: dangling refs = 0, eval coverage %, budget violations

## Blocked / DR

- (none — all 5 DRs resolved 2026-07-06, logged in decisions.md)

## Notes

- MAX_PARALLEL = 10 is a user decision (DR); do NOT "correct" it back to 4.
- Do NOT: reintroduce Workflow-tool or /goal-based orchestration in any skill.
- Do NOT: touch golang-pr-review (user instruction — excluded from scope: no adopt, no refactor, no evals).
- Deferred deliberately (not unfinished work): pr-body self-check; safety-rails ×3 dedup (cross-referenced on purpose); .agents/skills codex-portability rewrite.
- empirical-prompt-tuning stays third-party-pinned (home.nix:127); skill-lint must whitelist it.
- Final projected axis scores after the full plan: 86/83/82/82/83/84.
