# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml",
# ]
# ///
"""Tests for the pure (non-subprocess) parts of run_eval.py.

The async subprocess invocation is exercised by the end-to-end smoke step
in SKILL.md Phase 4, not here.

Run: `uv run tests/test_run_eval.py` from the skill directory.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from run_eval import (  # noqa: E402
    RunResult,
    RunSpec,
    _result_to_jsonl,
    build_specs,
    load_existing_keys,
    load_prompts,
)


def _seed(tmp: Path, *, with_off: bool = True, with_ablated: bool = True, legacy_layout: bool = False) -> Path:
    """Create a minimal eval workspace; return its path.

    Default seeds the v2 single-file prompt layout. Pass `legacy_layout=True`
    to seed the older `<rule>/on_target.yaml` + `<rule>/off_target.yaml` form
    (still supported for back-compat).
    """
    (tmp / "prompts").mkdir(parents=True)
    (tmp / "variants").mkdir()

    if legacy_layout:
        (tmp / "prompts" / "english_rewrite").mkdir()
        (tmp / "prompts" / "english_rewrite" / "on_target.yaml").write_text(
            "- id: ot_001\n  text: \"hello\"\n- id: ot_002\n  text: \"world\"\n"
        )
        if with_off:
            (tmp / "prompts" / "english_rewrite" / "off_target.yaml").write_text(
                "- id: nt_001\n  text: \"adjacent\"\n"
            )
    else:
        # v2 single-file layout with expected_fire field
        on_entries = (
            "- id: ot_001\n  text: \"hello\"\n  expected_fire: true\n"
            "- id: ot_002\n  text: \"world\"\n"  # default expected_fire: true
        )
        off_entries = (
            "- id: nt_001\n  text: \"adjacent\"\n  expected_fire: false\n"
            if with_off
            else ""
        )
        (tmp / "prompts" / "english_rewrite.yaml").write_text(on_entries + off_entries)

    (tmp / "rules.yaml").write_text(
        '- id: english_rewrite\n'
        '  source: "x"\n'
        '  text: "the rule text"\n'
        '  triggers: "always"\n'
        '  rubric: []\n'
    )
    (tmp / "variants" / "full.md").write_text("FULL")
    (tmp / "variants" / "empty.md").write_text("")
    if with_ablated:
        (tmp / "variants" / "ablated_english_rewrite.md").write_text("ABLATED")
    return tmp


def test_load_prompts_returns_two_lists():
    tmp = Path(tempfile.mkdtemp())
    _seed(tmp)
    on, off = load_prompts(tmp / "prompts", "english_rewrite")
    assert [p["id"] for p in on] == ["ot_001", "ot_002"]
    assert [p["id"] for p in off] == ["nt_001"]


def test_load_prompts_missing_off_target_is_empty():
    tmp = Path(tempfile.mkdtemp())
    _seed(tmp, with_off=False)
    on, off = load_prompts(tmp / "prompts", "english_rewrite")
    assert len(on) == 2
    assert off == []


def test_load_prompts_legacy_two_file_layout_still_works():
    tmp = Path(tempfile.mkdtemp())
    _seed(tmp, legacy_layout=True)
    on, off = load_prompts(tmp / "prompts", "english_rewrite")
    assert [p["id"] for p in on] == ["ot_001", "ot_002"]
    assert [p["id"] for p in off] == ["nt_001"]


def test_build_specs_three_variants_two_seeds():
    tmp = Path(tempfile.mkdtemp())
    _seed(tmp)
    specs = build_specs(tmp / "rules.yaml", tmp / "prompts", tmp / "variants", seeds=2)
    # 3 variants × 2 seeds × (2 on + 1 off) = 18 specs
    assert len(specs) == 18
    variants = {s.variant for s in specs}
    assert variants == {"full", "empty", "ablated_english_rewrite"}
    targets = {s.target for s in specs}
    assert targets == {"on", "off"}


def test_build_specs_skips_missing_ablated_variant():
    tmp = Path(tempfile.mkdtemp())
    _seed(tmp, with_ablated=False)
    specs = build_specs(tmp / "rules.yaml", tmp / "prompts", tmp / "variants", seeds=1)
    # 2 variants × 1 seed × 3 prompts = 6
    assert len(specs) == 6
    variants = {s.variant for s in specs}
    assert variants == {"full", "empty"}


def test_load_existing_keys_skips_malformed_rows():
    tmp = Path(tempfile.mkdtemp())
    raw = tmp / "raw.jsonl"
    rows = [
        {"variant": "full", "rule_id": "r", "prompt_id": "p1", "target": "on", "seed": 1, "x": 1},
        {"variant": "empty", "rule_id": "r", "prompt_id": "p2", "target": "on", "seed": 1, "x": 2},
    ]
    raw.write_text("\n".join(json.dumps(r) for r in rows) + "\nthis is not json\n")
    keys = load_existing_keys(raw)
    assert keys == {("full", "r", "p1", "on", 1), ("empty", "r", "p2", "on", 1)}


def test_load_existing_keys_returns_empty_for_missing_file():
    assert load_existing_keys(Path("/nonexistent/path/raw.jsonl")) == set()


def test_result_to_jsonl_round_trip():
    spec = RunSpec(
        variant="full",
        rule_id="r",
        prompt_id="p1",
        prompt_text="hello",
        target="on",
        seed=1,
    )
    result = RunResult(spec=spec, response="hi", duration_s=1.5, total_tokens=42, error=None)
    line = _result_to_jsonl(result)
    parsed = json.loads(line)
    assert parsed["variant"] == "full"
    assert parsed["response"] == "hi"
    assert parsed["total_tokens"] == 42
    assert parsed["error"] is None


if __name__ == "__main__":
    tests = [
        test_load_prompts_returns_two_lists,
        test_load_prompts_missing_off_target_is_empty,
        test_load_prompts_legacy_two_file_layout_still_works,
        test_build_specs_three_variants_two_seeds,
        test_build_specs_skips_missing_ablated_variant,
        test_load_existing_keys_skips_malformed_rows,
        test_load_existing_keys_returns_empty_for_missing_file,
        test_result_to_jsonl_round_trip,
    ]
    for test in tests:
        test()
        print(f"  ok: {test.__name__}")
    print(f"all {len(tests)} run_eval tests passed")
