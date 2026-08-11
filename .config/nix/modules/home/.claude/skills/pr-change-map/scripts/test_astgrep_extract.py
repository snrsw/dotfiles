"""Tests for astgrep_extract.py — pure logic, no ast-grep binary required."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from astgrep_extract import (
    LANGS,
    assign_complexity,
    build_rule,
    dedupe_edges,
    dedupe_matches,
    lang_for_path,
    matches_to_call_edges,
    matches_to_import_edges,
)


def match(file, start, end, name=None, line=0, text=""):
    """Build a minimal ast-grep JSON match."""
    m = {
        "file": file,
        "text": text,
        "range": {
            "byteOffset": {"start": start, "end": end},
            "start": {"line": line, "column": 0},
        },
        "metaVariables": {"single": {}},
    }
    if name is not None:
        m["metaVariables"]["single"]["NAME"] = {"text": name}
    return m


class LangTableTest(unittest.TestCase):
    def test_every_language_defines_the_four_kind_groups(self):
        for lang, spec in LANGS.items():
            for key in ("ext", "func_def", "import", "branch"):
                self.assertIn(key, spec, f"{lang} is missing {key}")
            self.assertTrue(spec["branch"], f"{lang} has no branch kinds")

    def test_extensions_are_unique_across_languages(self):
        seen = {}
        for lang, spec in LANGS.items():
            for ext in spec["ext"]:
                self.assertNotIn(ext, seen, f"{ext} claimed by {seen.get(ext)} and {lang}")
                seen[ext] = lang

    def test_kinds_verified_against_real_grammars(self):
        # Each kind below was probed with `ast-grep run --debug-query=ast`. A
        # language may list more kinds (Go has methods as well as functions);
        # what must not drift is the probed kind disappearing from the table.
        probed = {
            "python": "function_definition",
            "go": "function_declaration",
            "java": "method_declaration",
            "rust": "function_item",
            "ruby": "method",
            "typescript": "function_declaration",
        }
        for lang, kind in probed.items():
            self.assertIn(kind, LANGS[lang]["func_def"], f"{lang} lost its probed kind")


class LangForPathTest(unittest.TestCase):
    def test_known_extension_resolves(self):
        self.assertEqual(lang_for_path("src/a.py"), "python")
        self.assertEqual(lang_for_path("src/a.rs"), "rust")
        self.assertEqual(lang_for_path("a/b/c.tsx"), "tsx")

    def test_unknown_extension_returns_none(self):
        self.assertIsNone(lang_for_path("README.md"))
        self.assertIsNone(lang_for_path("noext"))


class BuildRuleTest(unittest.TestCase):
    def test_rule_names_every_kind_in_an_any_block(self):
        rule = build_rule("python", ["if_statement", "for_statement"])
        self.assertIn("language: python", rule)
        self.assertIn("kind: if_statement", rule)
        self.assertIn("kind: for_statement", rule)
        self.assertIn("any:", rule)

    def test_single_kind_still_produces_a_valid_any_block(self):
        rule = build_rule("rust", ["function_item"])
        self.assertIn("kind: function_item", rule)

    def test_capture_name_adds_a_name_field_matcher(self):
        rule = build_rule("python", ["function_definition"], capture_name=True)
        self.assertIn("field: name", rule)
        self.assertIn("$NAME", rule)


class AssignComplexityTest(unittest.TestCase):
    def test_complexity_is_one_plus_contained_branches(self):
        funcs = [match("a.py", 0, 100, name="f", line=1)]
        branches = [match("a.py", 10, 20), match("a.py", 30, 40)]
        out = assign_complexity(funcs, branches)
        self.assertEqual(out, [{"file": "a.py", "name": "f", "line": 2, "complexity": 3}])

    def test_function_with_no_branches_has_complexity_one(self):
        funcs = [match("a.py", 0, 50, name="plain", line=0)]
        self.assertEqual(assign_complexity(funcs, [])[0]["complexity"], 1)

    def test_branch_outside_any_function_is_ignored(self):
        funcs = [match("a.py", 0, 50, name="f")]
        branches = [match("a.py", 80, 90)]  # module-level branch
        self.assertEqual(assign_complexity(funcs, branches)[0]["complexity"], 1)

    def test_nested_function_takes_the_branch_from_its_parent(self):
        outer = match("a.py", 0, 200, name="outer")
        inner = match("a.py", 50, 150, name="inner")
        branches = [match("a.py", 60, 70)]
        out = {f["name"]: f["complexity"] for f in assign_complexity([outer, inner], branches)}
        self.assertEqual(out["inner"], 2)
        self.assertEqual(out["outer"], 1, "branch must count once, for the innermost function")

    def test_ranges_are_not_matched_across_different_files(self):
        funcs = [match("a.py", 0, 100, name="f")]
        branches = [match("b.py", 10, 20)]
        self.assertEqual(assign_complexity(funcs, branches)[0]["complexity"], 1)

    def test_output_is_sorted_by_descending_complexity(self):
        funcs = [match("a.py", 0, 100, name="low"), match("a.py", 200, 300, name="high")]
        branches = [match("a.py", 210, 220), match("a.py", 230, 240)]
        self.assertEqual([f["name"] for f in assign_complexity(funcs, branches)], ["high", "low"])


class ImportEdgesTest(unittest.TestCase):
    def test_module_name_metavariable_becomes_the_edge_target(self):
        ms = [match("src/a.py", 0, 10, name="auth")]
        self.assertEqual(
            matches_to_import_edges(ms), [{"from": "src/a.py", "to": "auth"}]
        )

    def test_match_without_the_metavariable_is_skipped(self):
        ms = [match("src/a.py", 0, 10)]
        self.assertEqual(matches_to_import_edges(ms), [])

    def test_repo_prefix_is_stripped_from_the_source_node(self):
        ms = [match("/repo/src/a.py", 0, 10, name="auth")]
        self.assertEqual(
            matches_to_import_edges(ms, repo="/repo"), [{"from": "src/a.py", "to": "auth"}]
        )


class CallEdgesTest(unittest.TestCase):
    def test_caller_is_the_enclosing_function_not_the_file(self):
        funcs = [match("a.py", 0, 100, name="handler")]
        calls = [match("a.py", 10, 20, name="verify")]
        self.assertEqual(
            matches_to_call_edges(funcs, calls), [{"from": "handler", "to": "verify"}]
        )

    def test_call_at_module_level_is_attributed_to_the_file(self):
        calls = [match("a.py", 10, 20, name="verify")]
        self.assertEqual(
            matches_to_call_edges([], calls), [{"from": "a.py", "to": "verify"}]
        )

    def test_self_recursive_call_is_dropped(self):
        funcs = [match("a.py", 0, 100, name="walk")]
        calls = [match("a.py", 10, 20, name="walk")]
        self.assertEqual(matches_to_call_edges(funcs, calls), [])


class DedupeMatchesTest(unittest.TestCase):
    """Several patterns per language can hit the same source span.

    Rust's `use crate::$NAME::$$$` and `use $NAME::$$$` both match
    `use crate::auth::verify`, yielding `auth` and `crate::auth` as two edges.
    That double-counts one import and inflates fan-in, so the more specific
    pattern (listed first) must win.
    """

    def test_same_span_keeps_only_the_first_pattern(self):
        first = match("a.rs", 0, 24, name="auth")
        second = match("a.rs", 0, 24, name="crate::auth")
        self.assertEqual(dedupe_matches([first, second]), [first])

    def test_different_spans_are_both_kept(self):
        a = match("a.rs", 0, 24, name="auth")
        b = match("a.rs", 25, 45, name="db")
        self.assertEqual(dedupe_matches([a, b]), [a, b])

    def test_same_span_in_different_files_is_kept(self):
        a = match("a.rs", 0, 24, name="auth")
        b = match("b.rs", 0, 24, name="auth")
        self.assertEqual(dedupe_matches([a, b]), [a, b])


class DedupeEdgesTest(unittest.TestCase):
    def test_duplicates_collapse_and_order_is_stable(self):
        edges = [{"from": "b", "to": "c"}, {"from": "a", "to": "b"}, {"from": "b", "to": "c"}]
        self.assertEqual(
            dedupe_edges(edges), [{"from": "a", "to": "b"}, {"from": "b", "to": "c"}]
        )


if __name__ == "__main__":
    unittest.main()
