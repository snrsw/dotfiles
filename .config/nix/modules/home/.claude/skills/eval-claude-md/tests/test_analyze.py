# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml",
# ]
# ///
"""Tests for analyze.py.

Run: `uv run tests/test_analyze.py` from the skill directory.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from analyze import (  # noqa: E402
    RuleMetrics,
    _row_passed,
    classify,
    compute_metrics,
    render_report,
)


def _mk_metrics(**kwargs) -> RuleMetrics:
    """Construct a RuleMetrics with sensible defaults; override via kwargs."""
    defaults = dict(
        rule_id="x",
        adherence=0.95,
        false_trigger=0.05,
        marginal_contribution=0.40,
        baseline=0.30,
        variance=0.05,
        token_cost=100,
        n_runs=180,
        recommendation="",
        rationale="",
    )
    defaults.update(kwargs)
    return RuleMetrics(**defaults)


def test_row_passed_all_true():
    assert _row_passed({"rubric": {"a": True, "b": True}}) is True


def test_row_passed_partial_fail():
    assert _row_passed({"rubric": {"a": True, "b": False}}) is False


def test_row_passed_missing_rubric():
    assert _row_passed({"variant": "full"}) is None
    assert _row_passed({"rubric": None}) is None
    assert _row_passed({"rubric": {}}) is None


def test_classify_keep():
    rec, _ = classify(_mk_metrics())
    assert rec == "keep"


def test_classify_delete_when_marginal_low():
    m = _mk_metrics(adherence=0.95, marginal_contribution=0.05, baseline=0.90)
    rec, _ = classify(m)
    assert rec == "delete"


def test_classify_rewrite_when_adherence_low():
    m = _mk_metrics(adherence=0.50, marginal_contribution=0.30)
    rec, _ = classify(m)
    assert rec == "rewrite"


def test_classify_narrow_when_false_trigger_high():
    m = _mk_metrics(adherence=0.90, false_trigger=0.40, marginal_contribution=0.30)
    rec, _ = classify(m)
    assert rec == "narrow_scope"


def test_classify_marginal_takes_precedence_over_adherence():
    """Low marginal beats low adherence — delete trumps rewrite."""
    m = _mk_metrics(adherence=0.50, marginal_contribution=0.05)
    rec, _ = classify(m)
    assert rec == "delete"


def test_compute_metrics_smoke():
    """Synthetic dataset — verify the math against known inputs."""
    tmp = Path(tempfile.mkdtemp())

    rules_yaml = tmp / "rules.yaml"
    rules_yaml.write_text(
        '- id: rule_one\n'
        '  source: "test"\n'
        '  text: "hello world"\n'
        '  triggers: "always"\n'
        '  rubric:\n'
        '    - id: c1\n'
        '      check: "test"\n'
        '      type: binary\n'
    )

    rows = [
        # full+on: 4 pass → adherence 1.0
        {"variant": "full", "rule_id": "rule_one", "prompt_id": "p1", "target": "on", "seed": 1, "rubric": {"c1": True}},
        {"variant": "full", "rule_id": "rule_one", "prompt_id": "p2", "target": "on", "seed": 1, "rubric": {"c1": True}},
        {"variant": "full", "rule_id": "rule_one", "prompt_id": "p3", "target": "on", "seed": 1, "rubric": {"c1": True}},
        {"variant": "full", "rule_id": "rule_one", "prompt_id": "p4", "target": "on", "seed": 1, "rubric": {"c1": True}},
        # ablated+on: 0 pass → ablated_adherence 0.0 → marginal 1.0
        {"variant": "ablated_rule_one", "rule_id": "rule_one", "prompt_id": "p1", "target": "on", "seed": 1, "rubric": {"c1": False}},
        {"variant": "ablated_rule_one", "rule_id": "rule_one", "prompt_id": "p2", "target": "on", "seed": 1, "rubric": {"c1": False}},
        # empty+on: 0 pass → baseline 0.0
        {"variant": "empty", "rule_id": "rule_one", "prompt_id": "p1", "target": "on", "seed": 1, "rubric": {"c1": False}},
        {"variant": "empty", "rule_id": "rule_one", "prompt_id": "p2", "target": "on", "seed": 1, "rubric": {"c1": False}},
    ]
    graded = tmp / "graded.jsonl"
    graded.write_text("\n".join(json.dumps(r) for r in rows) + "\n")

    metrics = compute_metrics(graded, rules_yaml)
    assert len(metrics) == 1
    m = metrics[0]
    assert m.rule_id == "rule_one"
    assert abs(m.adherence - 1.0) < 1e-6
    assert m.false_trigger is None  # no off-target rows
    assert m.marginal_contribution is not None
    assert abs(m.marginal_contribution - 1.0) < 1e-6
    assert abs(m.baseline - 0.0) < 1e-6
    assert m.recommendation == "keep"  # adherence high, marginal high, no false triggers


def test_render_report_smoke():
    tmp = Path(tempfile.mkdtemp())
    metrics = [
        _mk_metrics(rule_id="rule_one", adherence=0.95, false_trigger=None, recommendation="keep", rationale="ok"),
    ]
    out = tmp / "report.md"
    render_report(metrics, out)
    text = out.read_text()
    assert "rule_one" in text
    assert "0.95" in text
    assert "keep" in text
    assert "n/a" in text  # false_trigger=None should render as n/a


if __name__ == "__main__":
    tests = [
        test_row_passed_all_true,
        test_row_passed_partial_fail,
        test_row_passed_missing_rubric,
        test_classify_keep,
        test_classify_delete_when_marginal_low,
        test_classify_rewrite_when_adherence_low,
        test_classify_narrow_when_false_trigger_high,
        test_classify_marginal_takes_precedence_over_adherence,
        test_compute_metrics_smoke,
        test_render_report_smoke,
    ]
    for test in tests:
        test()
        print(f"  ok: {test.__name__}")
    print(f"all {len(tests)} analyze tests passed")
