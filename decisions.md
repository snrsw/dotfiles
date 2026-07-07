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
