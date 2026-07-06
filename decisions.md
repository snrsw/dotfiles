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

## DR: Plugin-sibling overlap — disambiguate in text, decide per pair, never auto-disable
- **Date**: 2026-07-06
- **Context**: Round-1 review (3 of 6 axes independently) found tdd/debug/git-wt/plan-state/maker-checker collide with same-named installed plugin skills (superpowers, pr-review-toolkit) with zero disambiguation — nondeterministic skill selection.
- **Decision**: W12 — each repo skill gains a one-line `Overlap:` anti-trigger naming its twin and when to prefer each; one keep/remove DR per pair records what the repo skill adds. Disabling a plugin twin is only ever a DR recommendation to the user, never an action taken by the plan.
- **Rationale**: The repo skills encode user-specific conventions (Kent-Beck CLAUDE.md workflow, git-wt CLI, plan.md contract), so removal is not obviously right; text disambiguation is cheap, reversible, and lintable (W11 sibling map). Settings changes are the user's domain.

## DR: Scored-verdict contract scope — maker-checker yes, replay-prompt advisory
- **Date**: 2026-07-06
- **Context**: R1 measurability found maker-checker's checker verdict and replay-prompt's Phase-4 eval lack the fenced-json parse contract the earlier DR established for ≥ 80 gates.
- **Decision**: maker-checker's checker adopts the full fenced-json + one-re-ask contract (it is a pass/fail gate). replay-prompt's Phase-4 stays lightweight: scores marked advisory-only with a deterministic pick rule (max total; tie → shorter prompt), never aggregated across contexts.
- **Rationale**: Contracts belong on gates. Phase-4 only picks among 3 local variants; full ceremony there would cost more overhead than the decision is worth (overhead axis), while the pick rule keeps it reproducible.

## DR: skill-lint as a GitHub Action
- **Date**: 2026-07-06
- **Context**: W11's deterministic gate only closes the loop if it fires without anyone remembering. A workflow file is an infrastructure change (protected domain).
- **Decision**: Yes — read-only Action (`permissions: contents: read`) on pull requests plus a weekly off-peak cron, with `workflow_dispatch` as the kill switch. Lands with W11.
- **Rationale**: A gate that depends on being remembered is not a gate.
