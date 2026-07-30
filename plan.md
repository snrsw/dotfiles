# Skills loop-engineering refactor

A loop-engineering review scored the skill set on 6 axes — loop closure, termination & triggers, state & resumability, measurability, composability, overhead (baseline 72/58/66/60/63/70). This plan raises every axis to ≥ 80. All 5 DRs are resolved — see decisions.md.

The C-wave (2026-07-30) applies the Claude 5 context-engineering rules (trust judgment, no anchoring examples, progressive disclosure, dedup, expressive descriptions) to the same 18 skills + rules + CLAUDE.md. Its 4 DRs are resolved — see decisions.md. Target: ~2450 skill lines → ~1500 with no genuine constraint lost.

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
- [ ] C0 — measure whether the generic response-style restatements in 10 skills are load-bearing: run executor subagents on pr-body and debug tasks with and without the generic bullets, grade outputs against the response-style checklist with fresh graders. Delete the generic bullets (~140 lines) only if the without-variant scores comparably; keep the artifact-specific specializations (pr-body checkbox rule, plan-state closed set, issue-resolver confidence rule) either way. Check: verdict + scores logged in decisions.md
- [ ] C1 — progressive disclosure: move to references/ — pr-dependency-review comment template (305→~130); issue-resolver KPI table, axes, spikes (300→~120); replay-prompt examples + merge its duplicate Quality Checklist into Golden Rules (179→~90); extract-skill-from-session examples + merge Anti-patterns into Negative indicators (160→~110); debug worked examples (149→~100); document-style verification loop (148→~120). Check: each SKILL.md at/below target, all references/ paths resolve
- [ ] C2 — relax overconstraint: tdd deletes intra-file repeats, generic Code Quality bullets, Add(2,3) example, keeps defect two-test protocol + signature carve-out (115→~40); tidy-first deletes the two 13-step git walkthroughs and both Go examples, keeps thesis + ♻️/🧹 rule + Red-commit carve-out (138→~55); replay-prompt unhardcodes model/200-word cap and makes 3-variants and eval-phase judgment calls; pr-body replaces emoji tie-break chain with judgment and drops the worked example. Check: every keep-list constraint still present verbatim
- [ ] C3 — single-source duplicates: commit gate → tidy-first owns (this is W7); emoji table → commit-message canonical, pr-body/tidy-first point; scored-review-loop → issue-resolver references/ file, document-style points; maker-checker + issue-resolver stop enumerating the ai-pr-checks list they delegate; protected-domain inline copies → "trigger a DR" pointers; safety rails stay inline ×3 but word-identical with only constants differing; "no workflow engine" claim reworded as decision ("orchestrate via Agent fan-out — user decision") stated once in loop-automation; prune content-free Integration entries across 11 skills. Check: each canonical passage appears in exactly one file (rails: three identical copies)
- [ ] C4 — trim the 4 keyword-dump descriptions (issue-resolver 859ch, pr-dependency-review 831, extract-skill-from-session 643, issue-loop 594) to expressive triggers, implementation detail into the body; keep the issue-loop↔issue-resolver disambiguation. Check: trigger probes still route each of the 4 correctly
- [ ] C5 — amend the W11 item spec with context-engineering lint checks: SKILL.md line budget warn > 150, description length warn > 600 chars, canonical-sentence duplication check. Check: W11 item text updated (no code — W11 itself is still open)

## Blocked / DR

- (none — all 5 DRs resolved 2026-07-06, logged in decisions.md)

## Notes

- MAX_PARALLEL = 10 is a user decision (DR); do NOT "correct" it back to 4.
- Do NOT: reintroduce Workflow-tool or /goal-based orchestration in any skill.
- Do NOT: touch golang-pr-review (user instruction — excluded from scope: no adopt, no refactor, no evals).
- Deferred deliberately (not unfinished work): pr-body self-check; safety-rails ×3 dedup (cross-referenced on purpose); .agents/skills codex-portability rewrite.
- empirical-prompt-tuning stays third-party-pinned (home.nix:127); skill-lint must whitelist it.
- Final projected axis scores after the full plan: 86/83/82/82/83/84.
