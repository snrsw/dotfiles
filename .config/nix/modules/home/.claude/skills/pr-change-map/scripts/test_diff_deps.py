"""Tests for diff_deps.py additions: calibration stats, context edges, ordering."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diff_deps import build_mermaid, fan_in, fan_in_stats


class FanInStatsTest(unittest.TestCase):
    def test_median_and_max_over_nodes_with_incoming_edges(self):
        edges = {("a", "x"), ("b", "x"), ("c", "x"), ("a", "y")}
        # fan-in: x=3, y=1 → median 2.0, max 3
        self.assertEqual(fan_in_stats(fan_in(edges)), {"median": 2.0, "max": 3})

    def test_single_target(self):
        edges = {("a", "x")}
        self.assertEqual(fan_in_stats(fan_in(edges)), {"median": 1.0, "max": 1})

    def test_empty_graph_gives_zeros(self):
        self.assertEqual(fan_in_stats(fan_in(set())), {"median": 0, "max": 0})


class ContextEdgesTest(unittest.TestCase):
    """L0 needs surroundings: unchanged edges touching a diffed node, plain.

    Without them a diff-only graph floats in space. `jobs -->|added| auth`
    explains fan-in 1 → 2 only when the reader also sees the pre-existing
    `api --> auth`. Neighbour nodes may enter for that; unrelated corners of
    the repo may not.
    """

    def test_existing_neighbour_of_a_diffed_node_is_drawn_plain(self):
        added = [("jobs", "auth")]
        head = {("jobs", "auth"), ("api", "auth")}
        m = build_mermaid(added, [], [], context=head)
        self.assertIn("-->|added|", m)
        self.assertIn('["api"]', m)  # neighbour brought in as context
        plain = [l for l in m.splitlines() if "-->" in l and "added" not in l]
        self.assertEqual(len(plain), 1, m)

    def test_edge_touching_no_diffed_node_is_excluded(self):
        added = [("jobs", "auth")]
        head = {("jobs", "auth"), ("x", "y")}  # x→y is another corner of the repo
        m = build_mermaid(added, [], [], context=head)
        self.assertNotIn('"x"', m)
        self.assertNotIn('"y"', m)

    def test_added_edges_are_never_duplicated_as_context(self):
        added = [("jobs", "auth")]
        head = {("jobs", "auth")}  # the added edge is also in head, of course
        m = build_mermaid(added, [], [], context=head)
        self.assertEqual(m.count("-->"), 1, m)  # drawn once, as added only

    def test_context_edge_count_is_capped(self):
        added = [("jobs", "auth")]
        head = {("jobs", "auth")} | {(f"dep{i}", "auth") for i in range(20)}
        m = build_mermaid(added, [], [], context=head, max_context=3)
        plain = [l for l in m.splitlines() if "-->" in l and "added" not in l]
        self.assertEqual(len(plain), 3, m)

    def test_node_budget_still_holds_with_context(self):
        added = [("jobs", "auth")]
        head = {("jobs", "auth")} | {(f"dep{i}", "auth") for i in range(40)}
        m = build_mermaid(added, [], [], context=head, max_nodes=5, max_context=99)
        self.assertLessEqual(m.count('["'), 5, m)

    def test_without_context_behaviour_is_unchanged(self):
        m = build_mermaid([("a", "b")], [], [])
        self.assertIn("-->|added|", m)


if __name__ == "__main__":
    unittest.main()
