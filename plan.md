# Skills loop-engineering refactor

A loop-engineering review scored the skill set on 6 axes — loop closure, termination & triggers, state & resumability, measurability, composability, overhead (baseline 72/58/66/60/63/70). This plan raises every axis to ≥ 80. All 5 DRs are resolved — see decisions.md.

The C-wave (2026-07-30) applies the Claude 5 context-engineering rules (trust judgment, no anchoring examples, progressive disclosure, dedup, expressive descriptions) to the same 18 skills + rules + CLAUDE.md. Its 4 DRs are resolved — see decisions.md. Target: ~2450 skill lines → ~1500 with no genuine constraint lost.

## Done

- [x] W0 — mechanism inventory verified: no `/goal`; the harness has since gained a `Workflow` tool, which C3 rewords as a standing decision not to use rather than a claim it does not exist; real engines are Agent fan-out, ralph-loop, /loop+ScheduleWakeup, CronCreate, Routines, Tasks — verified in this environment via ToolSearch; re-confirm the subagent-nesting fast path interactively before relying on it
- [x] W1+W6 — issue-resolver and issue-loop rebuilt on Agent fan-out (prompt+parse contract, MAX_PARALLEL=10, main-session orchestration, mandatory plan.md state, explicit outer stop predicate); dead Workflow JS deleted — 8e2c579
- [x] W2 — replay-prompt dangling references fixed — 913c2fc
- [x] W3 — loop-automation engine table updated (ralph-loop, /loop; stale wording refreshed) — 388260b
- [x] C0 — measured the response-style restatements (executor A/B, blind graders): load-bearing in template skills (pr-body gap 10.8 pts, critical item 4/4 vs 1/4), dead weight in free-form skills (debug scored higher without). Deleted the sections in debug and maker-checker only; template skills keep theirs; verdict + scores in decisions.md — f5fc601
- [x] C1 — progressive disclosure done: issue-resolver 300→224 (references/ kpis, axes, spikes), pr-dependency-review 305→234 (comment-template), replay-prompt 179→130 (examples; Golden Rules section deleted), extract-skill-from-session 160→116 (examples; Anti-patterns merged into Negative indicators), debug 130→85 (examples), document-style 148→129 (verification-loop, with a sync note naming issue-resolver's shared protocol constants). All references/ paths verified resolving. Counts sit above the plan's optimistic targets for issue-resolver/pr-dependency-review; C3+C4 cut further — 25e8681
- [x] C4 — the 4 keyword-dump descriptions trimmed (issue-resolver 859→~420 ch, pr-dependency-review 831→~400, extract-skill-from-session 643→~330, issue-loop 594→~380), sibling disambiguation kept. Routing probe: 8/8 prompts route correctly, including the issue-loop↔issue-resolver split and two controls
- [x] C5 — W11 spec amended with the context-engineering lint checks (line budget warn > 150, description warn > 600 ch, canonical-sentence duplication check, references/ path resolution); W11 itself still open
- [x] C3 — duplicates single-sourced: safety rails word-identical ×3 with per-skill constants (grep: each bold lead in exactly 3 files); "no workflow engine" false claim replaced by the fan-out decision stated once in loop-automation, issue-loop/issue-resolver point at it; ai-pr-checks enumeration survives only in the lazy comment-template.md; protected-domain inline lists → `decision-required` pointers (grep: zero inline copies); content-free Integration entries pruned in loop-automation, issue-loop, issue-resolver (section deleted), maker-checker, debug (section deleted), plan-state, git-wt. Deviation from the plan line: the scored-loop protocol stays in document-style's own references/verification-loop.md with a sync note naming issue-resolver's constants, instead of a cross-skill file dependency — efe8661's successor commit
- [x] C2 + W7 — overconstraint relaxed: tdd 115→37 (repeats, generic quality bullets, Add(2,3) example deleted; defect two-test protocol + signature carve-out kept verbatim), tidy-first 138→54 (13-step walkthroughs + Go examples deleted; thesis and Red-commit carve-out kept; the fixed pattern-to-emoji list became a judgment call deferring to commit-message's mechanical-vs-boundary rule, which resolved a contradiction the list had with that rule for Extract/Move/Inline Method; now sole owner of the commit gate — tdd defers, satisfying W7), replay-prompt 128 (model:"opus" hardcode removed; 2–4 variants and eval-phase are judgment calls), pr-body 92→70 (tie-break chain → "type carrying the PR's primary value"; worked example dropped; emoji table deferred to commit-message). Keep-list greps all pass

## Next

- [ ] W4 — adopt safe-lib-upgrade into the nix-managed skills dir. Delete the hand-dropped `~/.claude/skills/safe-lib-upgrade/` first: real files collide with home-manager's recursive linking ("existing file in the way")
- [ ] W8 — japanese-technical-writing: append a revise loop — write → checklist pass per section → fix → repeat until a pass finds no new violation; fresh-context checker for book manuscripts
- [ ] W9 — plan-state: bound retries — item fails → switch to debug (existing path) → fix fails twice → Blocked/DR, move on
- [ ] W10 — evals.json (3 scenarios each, incl. 1 near-miss) for issue-loop, maker-checker, plan-state, debug, loop-automation, replay-prompt. Check: process-skill eval coverage ≥ 80%
- [ ] W11 — skill-lint script + read-only GitHub Action (DR approved). Checks: frontmatter name = dir; description with trigger phrases; skill-name refs resolve; referenced tools/mechanisms exist; required sections for process skills (stop condition, verification step); SKILL.md line budget warn > 150; description length warn > 600 chars; canonical-sentence duplication check (the five rail leads appear in exactly 3 files; every other canonical passage in exactly 1 — seed list from the C3 commit); references/ paths named in a SKILL.md resolve; evals present. KPIs: dangling refs = 0, eval coverage %, budget violations

## Blocked / DR

- (none — all 5 DRs resolved 2026-07-06, logged in decisions.md)

## Notes

- MAX_PARALLEL = 10 is a user decision (DR); do NOT "correct" it back to 4.
- Do NOT: reintroduce Workflow-tool or /goal-based orchestration in any skill.
- Do NOT: touch golang-pr-review (user instruction — excluded from scope: no adopt, no refactor, no evals).
- Deferred deliberately (not unfinished work): pr-body self-check; the `.agents/skills` codex-portability *content* rewrite — the delivery plumbing landed 2026-09-02 (all 21 skills and the three rules now load in Codex; see decisions.md), so what remains is rewording the 7 skills that name Claude-only tools; the superpowers plugin's 9 trigger-competing skills (DR 2026-07-30 — separate follow-up).
- Deferred: safety rails stay inline in all three loop skills (an unattended issue-resolver run never loads loop-automation); C3 made the five leads word-identical so drift is grep-checkable. Do NOT "finish" this by collapsing them to one file.
- Deferred: `replay-prompt/references/examples.md` deliberately drops the old worked example's invented eval scores ("Minimal 17/25, …"). Fabricated numbers anchor a fresh session; Phase 5's deliverable #3 is described in the skill body instead. Do NOT restore them.
- empirical-prompt-tuning stays third-party-pinned (home.nix:127); skill-lint must whitelist it.
- Final projected axis scores after the full plan: 86/83/82/82/83/84.
