# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml",
# ]
# ///
"""Tests for extract_rules.py.

The implementation has no deps, but the round-trip test imports PyYAML to
verify the rendered YAML is parseable. Run with `uv run tests/test_extract_rules.py`.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from extract_rules import (  # noqa: E402
    extract_rules,
    render_yaml,
    slugify,
    split_into_rules,
)


def test_slugify():
    assert slugify("COMMUNICATION") == "communication"
    assert slugify("ROLE AND EXPERTISE") == "role_and_expertise"
    assert slugify("CODE STYLE") == "code_style"
    assert slugify("workflow") == "workflow"
    assert slugify("  Spaced  ") == "spaced"
    assert slugify("Hyphen-Heavy") == "hyphen_heavy"
    assert slugify("With Numbers 123") == "with_numbers_123"


def test_split_into_rules_simple():
    text = "# A\nbody of A\n\n# B\nbody of B\n"
    pairs = split_into_rules(text)
    assert pairs == [("A", "body of A"), ("B", "body of B")]


def test_split_into_rules_skips_pre_h1_content():
    text = "preamble line\n\n# FIRST\ncontent\n"
    pairs = split_into_rules(text)
    assert pairs == [("FIRST", "content")]


def test_split_into_rules_keeps_subheadings_in_body():
    text = "# OUTER\nintro\n\n## inner\nnested content\n"
    pairs = split_into_rules(text)
    assert len(pairs) == 1
    heading, body = pairs[0]
    assert heading == "OUTER"
    assert "## inner" in body
    assert "nested content" in body


def test_split_into_rules_empty_file():
    assert split_into_rules("") == []
    assert split_into_rules("just text\n") == []


def test_extract_rules_end_to_end():
    tmp = Path(tempfile.mkdtemp())
    target = tmp / "claude.md"
    target.write_text("# RULE_ONE\nbody one\n\n# RULE TWO\nbody two\n")
    rules = extract_rules(target)
    assert len(rules) == 2
    assert rules[0]["id"] == "rule_one"
    assert rules[0]["text"] == "body one"
    assert rules[0]["triggers"] == ""
    assert rules[0]["rubric"] == []
    assert rules[1]["id"] == "rule_two"
    assert "claude.md" in rules[0]["source"]


def test_render_yaml_round_trip():
    rules = [
        {
            "id": "x",
            "source": "foo: bar",
            "text": "line1\nline2",
            "triggers": "",
            "rubric": [],
        },
    ]
    out = render_yaml(rules)
    try:
        import yaml
        parsed = yaml.safe_load(out)
        assert parsed[0]["id"] == "x"
        assert parsed[0]["source"] == "foo: bar"
        assert parsed[0]["text"] == "line1\nline2"
        assert parsed[0]["rubric"] == []
    except ImportError:
        # PyYAML missing — fall back to substring checks.
        assert "id: x" in out
        assert "text: |" in out
        assert "line1" in out


def test_render_yaml_handles_empty_text():
    rules = [{"id": "y", "source": "z", "text": "", "triggers": "", "rubric": []}]
    out = render_yaml(rules)
    assert 'text: ""' in out


if __name__ == "__main__":
    tests = [
        test_slugify,
        test_split_into_rules_simple,
        test_split_into_rules_skips_pre_h1_content,
        test_split_into_rules_keeps_subheadings_in_body,
        test_split_into_rules_empty_file,
        test_extract_rules_end_to_end,
        test_render_yaml_round_trip,
        test_render_yaml_handles_empty_text,
    ]
    for test in tests:
        test()
        print(f"  ok: {test.__name__}")
    print(f"all {len(tests)} extract_rules tests passed")
