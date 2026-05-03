# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml",
# ]
# ///
"""Tests for the pure (non-subprocess) parts of judge.py.

The actual `claude -p` invocation is exercised by the end-to-end smoke step
in SKILL.md Phase 5, not here.

Run: `uv run tests/test_judge.py` from the skill directory.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from judge import (  # noqa: E402
    _strip_code_fence,
    build_judge_prompt,
    parse_judge_output,
)


_RULE = {
    "id": "english_rewrite",
    "text": "When the user writes a prompt, rewrite it in English at line 1.",
    "triggers": "every turn",
    "rubric": [
        {"id": "line_one_is_rewrite", "check": "Does line 1 begin with **Rewritten**?"},
    ],
}


def test_build_judge_prompt_includes_all_fields():
    row = {"prompt_text": "ファイルを変換", "response": "**Rewritten**: convert files"}
    prompt = build_judge_prompt(row, _RULE)
    assert "english_rewrite" not in prompt  # rule id is not surfaced; only its text/checks
    assert "When the user writes a prompt" in prompt
    assert "every turn" in prompt
    assert "line_one_is_rewrite" in prompt
    assert "ファイルを変換" in prompt
    assert "**Rewritten**: convert files" in prompt


def test_build_judge_prompt_raises_on_empty_rubric():
    row = {"prompt_text": "x", "response": "y"}
    rule = {"id": "x", "text": "...", "triggers": "...", "rubric": []}
    try:
        build_judge_prompt(row, rule)
    except ValueError:
        return
    raise AssertionError("expected ValueError for empty rubric")


def test_strip_code_fence_passes_plain_json():
    assert _strip_code_fence('{"a": true}') == '{"a": true}'


def test_strip_code_fence_strips_basic_fence():
    s = "```\n{\"a\": true}\n```"
    assert _strip_code_fence(s) == '{"a": true}'


def test_strip_code_fence_strips_language_tagged_fence():
    s = "```json\n{\"a\": true}\n```"
    assert _strip_code_fence(s) == '{"a": true}'


def test_parse_judge_output_basic():
    outer = json.dumps({"result": '{"line_one_is_rewrite": true}'})
    verdict = parse_judge_output(outer, ["line_one_is_rewrite"])
    assert verdict == {"line_one_is_rewrite": True}


def test_parse_judge_output_strips_fences():
    outer = json.dumps({"result": '```json\n{"line_one_is_rewrite": false}\n```'})
    verdict = parse_judge_output(outer, ["line_one_is_rewrite"])
    assert verdict == {"line_one_is_rewrite": False}


def test_parse_judge_output_coerces_to_bool():
    outer = json.dumps({"result": '{"k": 1}'})
    verdict = parse_judge_output(outer, ["k"])
    assert verdict == {"k": True}


def test_parse_judge_output_raises_on_missing_key():
    outer = json.dumps({"result": '{"other": true}'})
    try:
        parse_judge_output(outer, ["expected"])
    except ValueError as e:
        assert "expected" in str(e)
        return
    raise AssertionError("expected ValueError for missing key")


def test_parse_judge_output_raises_on_non_dict():
    outer = json.dumps({"result": "[true, false]"})
    try:
        parse_judge_output(outer, ["k"])
    except ValueError:
        return
    raise AssertionError("expected ValueError for non-dict result")


def test_parse_judge_output_raises_on_invalid_json():
    outer = json.dumps({"result": "not json at all"})
    try:
        parse_judge_output(outer, ["k"])
    except json.JSONDecodeError:
        return
    raise AssertionError("expected JSONDecodeError")


if __name__ == "__main__":
    tests = [
        test_build_judge_prompt_includes_all_fields,
        test_build_judge_prompt_raises_on_empty_rubric,
        test_strip_code_fence_passes_plain_json,
        test_strip_code_fence_strips_basic_fence,
        test_strip_code_fence_strips_language_tagged_fence,
        test_parse_judge_output_basic,
        test_parse_judge_output_strips_fences,
        test_parse_judge_output_coerces_to_bool,
        test_parse_judge_output_raises_on_missing_key,
        test_parse_judge_output_raises_on_non_dict,
        test_parse_judge_output_raises_on_invalid_json,
    ]
    for test in tests:
        test()
        print(f"  ok: {test.__name__}")
    print(f"all {len(tests)} judge tests passed")
