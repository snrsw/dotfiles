# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml",
# ]
# ///
"""Aggregate graded.jsonl into per-rule metrics and render report.md.

Run with `uv run scripts/analyze.py …` — uv resolves PyYAML automatically.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class RuleMetrics:
    """One row of the scorecard."""

    rule_id: str
    adherence: float                       # full variant on on-target prompts
    false_trigger: float | None            # full variant on off-target prompts; None if rule has no off-target set
    marginal_contribution: float | None    # adherence(full) − adherence(ablated_<rule>); None if no ablated runs
    baseline: float                        # adherence with empty CLAUDE.md
    variance: float                        # std dev of per-seed adherence (full, on)
    token_cost: int                        # rule text token count (approximate, chars/4)
    n_runs: int                            # total graded rows used for this rule
    recommendation: str                    # "keep" | "rewrite" | "delete" | "narrow_scope"
    rationale: str                         # one-line explanation of the recommendation


def _row_passed(row: dict) -> bool | None:
    """True if all rubric checks passed; None if the row was never graded."""
    rubric = row.get("rubric")
    if not rubric or not isinstance(rubric, dict):
        return None
    return all(bool(v) for v in rubric.values())


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _mean(values: list[bool]) -> float:
    return sum(values) / len(values) if values else float("nan")


def _approx_tokens(text: str) -> int:
    """Rough char/4 estimate. Good enough for relative comparisons across rules."""
    return len(text) // 4


def classify(metrics: RuleMetrics) -> tuple[str, str]:
    """Apply default decision rules → (recommendation, rationale).

    Order matters: first matching branch wins. The marginal-contribution check
    runs first so a rule that the model already follows from training (low
    marginal contribution) gets flagged for deletion even if its adherence
    looks high — high adherence on its own only means Claude does the thing,
    not that the rule is what's making Claude do the thing.
    """
    if metrics.marginal_contribution is not None and metrics.marginal_contribution < 0.10:
        return (
            "delete",
            f"marginal contribution {metrics.marginal_contribution:.2f} < 0.10 — rule isn't moving the needle vs ablated baseline",
        )
    if metrics.adherence < 0.80:
        return (
            "rewrite",
            f"adherence {metrics.adherence:.2f} < 0.80 — currently unreliable",
        )
    if metrics.false_trigger is not None and metrics.false_trigger > 0.20:
        return (
            "narrow_scope",
            f"false-trigger {metrics.false_trigger:.2f} > 0.20 — fires on adjacent prompts that should not trigger",
        )
    return ("keep", "metrics within healthy ranges")


def compute_metrics(graded_jsonl: Path, rules_yaml: Path) -> list[RuleMetrics]:
    """Pivot graded.jsonl by (rule_id, variant, target), compute metrics per rule."""
    rows = _read_jsonl(graded_jsonl)
    with rules_yaml.open() as f:
        rules = yaml.safe_load(f) or []

    buckets: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for row in rows:
        passed = _row_passed(row)
        if passed is None:
            continue
        key = (row["rule_id"], row["variant"], row["target"])
        buckets[key].append({"passed": passed, "seed": row.get("seed", 0)})

    metrics_out: list[RuleMetrics] = []
    for rule in rules:
        rid = rule["id"]
        full_on = [r["passed"] for r in buckets.get((rid, "full", "on"), [])]
        full_off = [r["passed"] for r in buckets.get((rid, "full", "off"), [])]
        ablated_on = [r["passed"] for r in buckets.get((rid, f"ablated_{rid}", "on"), [])]
        empty_on = [r["passed"] for r in buckets.get((rid, "empty", "on"), [])]

        adherence = _mean(full_on)
        false_trigger = _mean(full_off) if full_off else None
        ablated = _mean(ablated_on) if ablated_on else None
        marginal = (adherence - ablated) if ablated is not None else None
        baseline = _mean(empty_on) if empty_on else float("nan")

        per_seed: dict[int, list[bool]] = defaultdict(list)
        for r in buckets.get((rid, "full", "on"), []):
            per_seed[r["seed"]].append(r["passed"])
        seed_means = [_mean(v) for v in per_seed.values()]
        variance = statistics.stdev(seed_means) if len(seed_means) >= 2 else 0.0

        m = RuleMetrics(
            rule_id=rid,
            adherence=adherence,
            false_trigger=false_trigger,
            marginal_contribution=marginal,
            baseline=baseline,
            variance=variance,
            token_cost=_approx_tokens(rule.get("text", "")),
            n_runs=len(full_on) + len(full_off) + len(ablated_on) + len(empty_on),
            recommendation="",
            rationale="",
        )
        m.recommendation, m.rationale = classify(m)
        metrics_out.append(m)

    return metrics_out


def _fmt_opt(v: float | None) -> str:
    return "n/a" if v is None else f"{v:.2f}"


def render_report(metrics: list[RuleMetrics], out_md: Path) -> None:
    """Write a markdown scorecard."""
    lines: list[str] = ["# Eval report", ""]

    lines.append("## Summary")
    lines.append("")
    lines.append(
        "| Rule | Adherence | False-trigger | Marginal | Baseline | Variance | Tokens | n_runs | Recommendation |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for m in metrics:
        lines.append(
            f"| {m.rule_id} "
            f"| {m.adherence:.2f} "
            f"| {_fmt_opt(m.false_trigger)} "
            f"| {_fmt_opt(m.marginal_contribution)} "
            f"| {m.baseline:.2f} "
            f"| {m.variance:.2f} "
            f"| {m.token_cost} "
            f"| {m.n_runs} "
            f"| **{m.recommendation}** |"
        )
    lines.append("")

    lines.append("## Per-rule rationale")
    lines.append("")
    for m in metrics:
        lines.append(f"### {m.rule_id} → {m.recommendation}")
        lines.append("")
        lines.append(f"- {m.rationale}")
        lines.append("")

    lines.append("## How to read this report")
    lines.append("")
    lines.append(
        "- **Adherence** is mean rubric-pass rate on prompts where the rule should fire, "
        "with the full CLAUDE.md present."
    )
    lines.append(
        "- **Marginal contribution** is the delta vs. the ablated CLAUDE.md (full minus the named rule). "
        "A near-zero value means Claude does the behavior anyway — the rule isn't earning its tokens."
    )
    lines.append(
        "- **Baseline** is adherence with no CLAUDE.md at all. A high baseline + low marginal means the rule "
        "was redundant from the start."
    )
    lines.append(
        "- **False-trigger** is rubric-pass rate on adjacent prompts where the rule should NOT fire. "
        "High values mean the rule's trigger conditions are too broad."
    )
    lines.append("")

    out_md.write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graded", type=Path, required=True, help="graded.jsonl from judge.py")
    parser.add_argument("--rules", type=Path, required=True, help="rules.yaml")
    parser.add_argument("--out", type=Path, required=True, help="path to write report.md")
    args = parser.parse_args()

    metrics = compute_metrics(args.graded, args.rules)
    render_report(metrics, args.out)
    print(f"wrote report for {len(metrics)} rule(s) to {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
