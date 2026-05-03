---
name: eval-claude-md
description: Quantitatively evaluate a CLAUDE.md or rules file by measuring per-rule adherence, false-trigger rate, marginal contribution (vs. ablation), and variance via batch `claude -p` runs. Use this whenever the user asks to evaluate, audit, benchmark, test, or measure their CLAUDE.md, global instructions, agent rules, or skill descriptions — even if they don't say "eval" explicitly. Also use when the user asks "is rule X working?", "are my instructions doing anything?", "should I delete this rule?", "find redundant rules in my CLAUDE.md", or wants empirical evidence that a system prompt is changing model behavior.
---

# Evaluate CLAUDE.md and rules

Run a quantitative evaluation of a markdown rules file (typically a CLAUDE.md or a project-level rules file) and produce a per-rule scorecard. Wraps subscription-backed `claude -p` — runs are billed under the user's subscription, not via the Anthropic API.

## When to invoke

Trigger on any of these surfaces, even when the user doesn't explicitly say "eval":
- "evaluate / audit / benchmark / test / measure my CLAUDE.md"
- "is rule X working?", "should I delete this rule?", "find redundant rules"
- "are my instructions doing anything?", "tune my system prompt"

## Pick the smallest path that satisfies the ask

The skill has fast paths. Use the cheapest one — don't run the full eval if the user only asked for an opinion.

| User asked for… | Run only this | Primary deliverable |
|---|---|---|
| Operationalize a vague rule | `references/methodology.md` + `references/rubric_examples.md` | `rubric.md` with 2–4 candidate operationalizations + 5–10 prompts each |
| Audit / hypothesis pass (no measurement) | `scripts/extract_rules.py` + reasoning | `audit_report.md` ranking rules by suspected redundancy, citing which metric matters per rule |
| Set up scaffolding for a future eval | extract + author rules.yaml + prompts.yaml + variants/ | the artifacts + `plan.md` describing what running would look like |
| Full quantitative eval | all phases below | `report.md` with delete/rewrite/keep recommendations |

**Front-load artifacts.** When asked for the full eval, produce *one* rule + *one* prompt + *one* variant first, show the user, *then* expand. Catches schema mismatches before doing 10× the work.

## Full-eval workflow

See `references/runbook.md` for the exact commands per phase. Summary:

1. **Locate target** — default `~/.claude/CLAUDE.md`. Confirm if ambiguous.
2. **Extract rules** — `extract_rules.py` produces a `rules.yaml` skeleton with one entry per H1 section. **If an H1 section contains multiple distinct directives you want to evaluate separately** (e.g., `# COMMUNICATION` containing both an english-rewrite directive and several partnership bullets), split the entry by hand: duplicate it, give each a semantic snake_case `id` (`english_rewrite`, `push_back`), and trim the `text` field to just that directive. The `id` is the canonical key — it must match the prompts filename stem (`prompts/<id>.yaml`) and the ablation variant filename (`variants/ablated_<id>.md`). Then fill `triggers` and `rubric` (binary checks only — see `references/rubric_examples.md`).
3. **Author prompts** — one file per rule at `prompts/<rule_id>.yaml`, a list of `{id, text, expected_fire: bool, note?}`. `expected_fire: true` → on-target; `false` → off-target. Default is `true`. Skip the off-target prompts entirely for rules that fire every turn.
4. **Build variants** — `variants/full.md` (target verbatim), `variants/empty.md` (must contain a placeholder string — `claude -p --system-prompt-file` rejects empty files), `variants/ablated_<rule_id>.md` (full minus the named rule). For sub-rules within an H1 section, the ablation should remove just that paragraph/bullet, not the whole section — see `references/runbook.md` for the recipe.
5. **Run matrix** — `run_eval.py` injects each variant via `claude -p --system-prompt-file`, parallel via `asyncio.Semaphore(4)`, resumable via `raw.jsonl`.
6. **Grade** — `judge.py` calls `claude -p --output-format json` per row, applying the rubric. Same-model judge bias is real — hand-grade a 10-row sample and confirm ≥90% agreement before trusting metrics.
7. **Analyze** — `analyze.py` produces `report.md` with adherence, false-trigger, marginal contribution, baseline, and a recommendation per rule. Thresholds: adherence < 0.80 → rewrite; marginal < 0.10 → delete; false-trigger > 0.20 → narrow scope.
8. **Propose edits** — read `report.md`, propose concrete diffs per rule, **wait for user approval** before applying any. Never auto-apply.

## Reference material

- `references/methodology.md` — operationalizing vague rules. Read when the user authors `triggers`/`rubric` for a rule that's hard to make binary.
- `references/rubric_examples.md` — concrete examples of good vs bad rubric checks.
- `references/runbook.md` — exact `uv run` commands per phase, with workspace layout and resumability notes.

## Tradeoffs to keep in mind

- **CLI startup cost**: ~1–2s per `claude -p` call. A 5-rule × 6-variant × 20-prompt × 3-seed matrix is ~15 min at concurrency 4.
- **Subscription, not API**: all calls go through `claude -p`. Free under the user's subscription.
- **Same-model judge bias**: validate via hand-grading. Clean metrics on a biased judge are still wrong.
- **Snapshot, not live**: re-run after every rule edit and after model version bumps.
- **Prompt-set quality caps the eval**: bad prompts → meaningless metrics.
