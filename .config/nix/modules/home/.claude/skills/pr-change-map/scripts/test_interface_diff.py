"""Tests for interface_diff.py — the L1 boundary delta, pure logic."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface_diff import diff_defs


def d(file, name, signature, line=1):
    return {"file": file, "name": name, "signature": signature, "line": line}


class DiffDefsTest(unittest.TestCase):
    def test_unchanged_surface_reports_empty_and_counts(self):
        base = [d("a.py", "f", "def f(x)")]
        head = [d("a.py", "f", "def f(x)")]
        out = diff_defs(base, head)
        self.assertEqual(out["added"], [])
        self.assertEqual(out["removed"], [])
        self.assertEqual(out["changed"], [])
        self.assertEqual(out["unchanged"], 1)

    def test_new_function_is_added(self):
        out = diff_defs([], [d("a.py", "f", "def f(x)")])
        self.assertEqual(out["added"], [d("a.py", "f", "def f(x)")])

    def test_deleted_function_is_removed(self):
        out = diff_defs([d("a.py", "f", "def f(x)")], [])
        self.assertEqual(out["removed"], [d("a.py", "f", "def f(x)")])

    def test_signature_change_is_reported_with_before_and_after(self):
        base = [d("a.py", "f", "def f(x)")]
        head = [d("a.py", "f", "def f(x, retries)", line=3)]
        out = diff_defs(base, head)
        self.assertEqual(out["changed"], [{
            "file": "a.py", "name": "f", "line": 3,
            "before": ["def f(x)"], "after": ["def f(x, retries)"],
        }])
        self.assertEqual(out["added"], [])
        self.assertEqual(out["removed"], [])

    def test_same_name_in_different_files_are_distinct(self):
        base = [d("a.py", "f", "def f(x)"), d("b.py", "f", "def f(y)")]
        head = [d("a.py", "f", "def f(x)"), d("b.py", "f", "def f(y, z)")]
        out = diff_defs(base, head)
        self.assertEqual(len(out["changed"]), 1)
        self.assertEqual(out["changed"][0]["file"], "b.py")

    def test_overloads_compare_as_signature_sets(self):
        # Java-style overloads share (file, name); the set of signatures is
        # what the boundary promises.
        base = [d("A.java", "f", "void f(int x)"), d("A.java", "f", "void f(String x)")]
        head = [d("A.java", "f", "void f(int x)"), d("A.java", "f", "void f(String x)")]
        self.assertEqual(diff_defs(base, head)["changed"], [])

    def test_results_are_sorted_by_file_then_name(self):
        head = [d("b.py", "z", "def z()"), d("a.py", "m", "def m()")]
        out = diff_defs([], head)
        self.assertEqual([(e["file"], e["name"]) for e in out["added"]],
                         [("a.py", "m"), ("b.py", "z")])


if __name__ == "__main__":
    unittest.main()
