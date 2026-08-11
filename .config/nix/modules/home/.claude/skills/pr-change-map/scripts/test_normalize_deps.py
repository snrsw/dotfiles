"""Tests for normalize_deps.py DOT parsing."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from normalize_deps import parse_dot


class ParseDotTest(unittest.TestCase):
    def test_code2flow_synthetic_ids_resolve_to_name_attribute(self):
        # code2flow emits opaque node ids and carries the real symbol in name=.
        # The edge must come back as the human-readable names, not the ids, so
        # call_graph_slice's substring matching on changed symbols can hit.
        dot = (
            "digraph G {\n"
            'node_0af [name="src/orders::compute_total" shape="rect"];\n'
            'node_1bc [name="src/discount::apply_discount" shape="rect"];\n'
            "node_0af -> node_1bc;\n"
            "}\n"
        )
        self.assertEqual(
            parse_dot(dot),
            [("src/orders::compute_total", "src/discount::apply_discount")],
        )

    def test_pyreverse_meaningful_ids_preserved(self):
        # pyreverse node ids are already the dotted names; label= is an HTML
        # record we must NOT substitute in. Edges stay as the ids.
        dot = (
            'digraph "classes" {\n'
            '"src.shop.Order" [label=<{Order|total}>, shape="record"];\n'
            '"src.shop.Catalog" [label=<{Catalog|price}>, shape="record"];\n'
            '"src.shop.Order" -> "src.shop.Catalog" [arrowhead="empty"];\n'
            "}\n"
        )
        self.assertEqual(
            parse_dot(dot),
            [("src.shop.Order", "src.shop.Catalog")],
        )


if __name__ == "__main__":
    unittest.main()
