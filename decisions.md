# decisions.md

DR log for the skills loop-engineering refactor (see plan.md).

## DR: Scored review contract without a schema parameter
- **Date**: 2026-07-06
- **Context**: Rebuilding issue-resolver/issue-loop on the Agent tool, which cannot schema-constrain subagent output the way the (nonexistent) Workflow engine promised.
- **Decision**: Prompt + parse — every reviewer ends its reply with one fenced json block; one re-ask on parse failure, then the axis is blocked for the round.
- **Rationale**: Keeps the ≥ 80 gates machine-checkable. Free-text verdicts would degrade the loop to vibes.

## DR: Concurrency cap
- **Date**: 2026-07-06
- **Context**: The old cap came from the Workflow runtime; loop-automation's rails require an explicit one.
- **Decision**: MAX_PARALLEL = 10, shared across reviewers, refuters, and background implementers. (User override; the recommendation was 4.)
- **Rationale**: User call — more parallelism per round; still an explicit, stated cap.

## DR: Orchestration locus
- **Date**: 2026-07-06
- **Context**: Subagents may not be able to dispatch further subagents; whoever runs the loop must be able to fan out fresh-context reviewers.
- **Decision**: The main session orchestrates and dispatches all subagents. Nested per-issue orchestrators are a fast path only after verifying subagent nesting works in the environment.
- **Rationale**: A subagent that cannot fan out silently degrades to self-grading, which maker-checker forbids.

## DR: empirical-prompt-tuning — vendor vs keep third-party pin
- **Date**: 2026-07-06
- **Context**: The skill is nix-pinned from mizchi/skills (home.nix); it has upstream quirks (a dangling retrospective-codify reference, no ledger location, a SKILL-ja.md duplicate).
- **Decision**: Keep the pin. skill-lint (W11) whitelists the directory. Ledger convention for our own skills: `<skill>/evals/ledger.md`.
- **Rationale**: The quirks are peripheral to its value; a pin keeps maintenance at zero.

## DR: skill-lint as a GitHub Action
- **Date**: 2026-07-06
- **Context**: W11's deterministic gate only closes the loop if it fires without anyone remembering. A workflow file is an infrastructure change (protected domain).
- **Decision**: Yes — read-only Action (`permissions: contents: read`) on pull requests plus a weekly off-peak cron, with `workflow_dispatch` as the kill switch. Lands with W11.
- **Rationale**: A gate that depends on being remembered is not a gate.

## DR: Hook enforcement level for the quality gates
- **Date**: 2026-07-07
- **Context**: Wiring the automation layer (spec-first rule, routing, design-panel, checker agent) needed a call on the two settings.json hooks: does the PreToolUse test gate block `git commit` on failure, and does the Stop-hook verification nudge block the turn.
- **Decision**: Commit gate blocks (exit 2 on test failure, fail-open on unknown project shape / missing runner, `--no-verify` escape). Stop hook reminds once (exit 2 with `stop_hook_active` loop guard, fires only when the transcript shows edits but no test/verify activity).
- **Rationale**: User call ("block on commits"). A commit with failing tests is exactly what the gate exists to stop, and the block is deterministic; blocking every turn-end would nag on Q&A sessions, so the stop side stays a one-shot nudge.

## DR: Accept residual risks at the eval resource cutoff
- **Date**: 2026-07-07
- **Context**: Three-iteration empirical eval of the workflow layer ended when the org spend limit blocked the final routing probe. All criticals had passed two consecutive rounds where re-tested.
- **Decision**: Ship as-is. Accepted (all low, fail-open): heredoc/escaped-quote lexing in the commit gate, alternate git syntax evasion, the stop reminder's prose-grep suppression. Deferred one-time checks: reminder against a real transcript, design-panel name resolution from ~/.claude/workflows, and the skipped iter3 routing probe.
- **Rationale**: Severity trended down across iterations (bugs → corner cases → wording); the gate is fail-open by design, so residual misses degrade to "no gate", never a wrong block. The skill's resource-cutoff rule applies.

## DR: Response-style restatements — delete, keep, or measure first
- **Date**: 2026-07-30
- **Context**: C-wave dedup rule says eliminate the ~140 generic restatement lines across 10 skills; commit e86fd32 added them deliberately, on an admittedly unmeasured mechanism ("a foregrounded format spec beats passive background context").
- **Decision**: Measure first (C0). Delete only if executors without the restatements score comparably against the response-style checklist. Artifact-specific specializations stay either way.
- **Rationale**: Reversing a merged, reasoned decision needs evidence, not a competing article's general claim.

## DR: Safety rails duplicated in 3 loop skills
- **Date**: 2026-07-30
- **Context**: loop-automation, issue-loop, and issue-resolver each carry the five safety rails with drifted wording; plan.md had logged the duplication as deliberate.
- **Decision**: Keep the rails inline in all three (an unattended issue-resolver run never loads loop-automation), but make the five rails word-for-word identical, with only the constants (MAX_PARALLEL, MAX_ROUNDS) differing.
- **Rationale**: Rails are genuine safety constraints, exempt from the dedup rule; identical wording makes drift machine-checkable.

## DR: Stale "no workflow engine" claim
- **Date**: 2026-07-30
- **Context**: Three skills state "there is no workflow-script engine and no /goal built-in" as fact; the current harness ships a Workflow tool, so the fact is now false while the no-Workflow-orchestration decision stands.
- **Decision**: Reword from fact to decision — "orchestrate via Agent fan-out; do not use the Workflow tool even where present (user decision)" — stated once in loop-automation; the other two point at it.
- **Rationale**: A false factual claim erodes trust in the rest of the skill; the underlying user decision is unchanged.

## DR: Superpowers plugin skill overlap
- **Date**: 2026-07-30
- **Context**: 9 superpowers skills compete with local skills (tdd, debug, git-wt, maker-checker, plan-state, issue-resolver) for the same triggers — the largest single context cost found in the audit.
- **Decision**: Out of C-wave scope; handle as a separate follow-up task.
- **Rationale**: Third-party plugin configuration is a different change surface (settings.json) with its own trade-offs; bundling it would blur the C-wave's verification.
