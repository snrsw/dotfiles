# decisions.md

DR log for the skills loop-engineering refactor (see plan.md), plus the
platform-support decisions below.

## Linux support (2026-07-31)

User answers when the config was extended to a second platform. A later session
should not "correct" these without asking.

- **Target: non-NixOS distro, standalone home-manager.** Not NixOS, not WSL. This
  is why `targets.genericLinux.enable` and nixGL are needed at all — on NixOS both
  would be wrong.
- **Architecture: x86_64-linux only.** aarch64-linux was offered and declined, so
  `systems` lists two entries. Adding arm64 later means adding its `mo` and
  `newrelic-cli` release assets to the per-system tables in flake.nix.
- **Scope: full desktop parity** — VS Code, ghostty, and fonts are ported, not just
  the CLI set. This is what pulls in nixGL and `fonts.fontconfig.enable`.
- **nixGL wrapper: `mesa`** (nixGL's `nixGLIntel`, which covers Intel and AMD).
  Chosen as the safe default because the target machine's GPU was not specified.
  An NVIDIA host needs `defaultWrapper = "nvidia"`, which is untested here.
- **Layout: separate module files** (`home.nix` shared + `darwin.nix` / `linux.nix`)
  rather than `lib.mkIf` guards inside one file.
- Do NOT: reintroduce `vscode` into `home.packages`. `programs.vscode` installs it,
  and on Linux that package is nixGL-wrapped — a second copy collides on `bin/code`.
- Not verified: no x86_64-linux build was run. Verification was cross-evaluation
  from darwin (catches option/type/attribute errors) plus a byte-identical darwin
  closure. First real Linux `switch` may still surface build-time breakage.

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

## C0 verdict: response-style restatements are load-bearing only in template skills
- **Date**: 2026-07-30
- **Method**: Blind executor A/B runs (skill text with vs without its Response Style section), fixed 6-item checklist graded by fresh blind graders. pr-body: n=4 per variant; debug: n=2 per variant. Checklists and the decision rule (delete only if the without-variant lands within 10 points and its critical-item failures do not exceed the with-variant's) were fixed before any run. One grading round was discarded and redone because the grader's source material omitted a clause the executors had seen.
- **Scores**: pr-body with 77.3 / without 66.5 — gap 10.8, and the critical "lead with the conclusion" item passed 4/4 with vs 1/4 without (executors without the restatement reproduced the commit message's 60-word causal chain as the opening sentence). debug with 83.0 / without 87.5 — the without-variant scored higher with all critical items passing.
- **Decision**: Keep restatements in skills that hand over a fixed output template (pr-body, commit-message, pr-dependency-review, issue-loop, issue-resolver, plan-state, extract-skill-from-session, replay-prompt). Delete them in free-form-artifact skills: debug (measured) and maker-checker (same artifact class — a free-form verdict; extended by analogy, not measured).
- **Rationale**: The e86fd32 hypothesis ("a foregrounded format spec beats passive background context") is confirmed exactly where a format spec exists and refuted where none does. The always-loaded rules/response-style.md carries free-form outputs on its own.

## DR: Superpowers plugin skill overlap
- **Date**: 2026-07-30
- **Context**: 9 superpowers skills compete with local skills (tdd, debug, git-wt, maker-checker, plan-state, issue-resolver) for the same triggers — the largest single context cost found in the audit.
- **Decision**: Out of C-wave scope; handle as a separate follow-up task.
- **Rationale**: Third-party plugin configuration is a different change surface (settings.json) with its own trade-offs; bundling it would blur the C-wave's verification.

## DR: Codex parity for skills and rules
- **Date**: 2026-09-02
- **Context**: `~/.codex/AGENTS.md` and `~/.agents/skills` were already wired, but Codex loaded only 1 of the 21 skills and none of the three rules. Measured with `codex debug prompt-input` on codex-cli 0.151.0, which renders the model-visible prompt.
- **Root cause**: Codex does not follow a symlinked `SKILL.md`. `recursive = true` on `home.file.".agents/skills"` produces exactly that — a real directory holding one symlink per file. `terminal-browser` was the only skill Codex saw because darwin.nix declares it as a whole-directory symlink. Isolated with three probe skills: real dir + real file loads, symlinked dir loads, real dir + symlinked file does not.
- **Decision**: One `home.file` entry per skill, generated from `builtins.readDir ./.claude/skills`, so each skill directory is symlinked as a unit. Not a single non-recursive `.agents/skills` link — that would collide with darwin.nix's `terminal-browser` entry and block adding third-party skills individually.
- **Decision**: `~/.codex/AGENTS.md` is a generated concatenation of `CLAUDE.md` plus `rules/*.md`. Codex has no equivalent of `~/.claude/rules`, and `~/.codex/rules/` is a sandbox-permission file, not instructions. The rules stay separate files on disk, so Claude Code's own loading is unchanged.
- **Decision**: Own skills only. The four nix-pinned third-party skills (eli5, grilling, grill-me, empirical-prompt-tuning) stay Claude-only — they are written for Claude Code and untested on Codex.
- **Decision**: No per-skill exclusion list. `loop-automation` is largely about Claude Code Routines, but it also covers GitHub Actions, and an exclusion list is one more thing to keep in sync.
- **Verified**: All 21 skills and all three rules appear in Codex's prompt; nothing was truncated by the skills context budget. Darwin builds, Linux cross-evaluates. Rewording the 7 skills that name Claude-only tools is still deferred — see plan.md.
