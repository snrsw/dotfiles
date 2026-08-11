#!/usr/bin/env python3
"""Diff two normalized dependency graphs (base vs head).

Reports: added/removed edges, new & resolved cycles, fan-in per node,
high-fan-in nodes touched by the change, and an optional Mermaid diff graph.

Usage:
  diff_deps.py base.json head.json --fan-in-threshold 5 \
      [--changed-files file1,file2] [--mermaid] > diff.json
"""
import argparse
import json
import sys
from collections import defaultdict


def load(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {(e["from"], e["to"]) for e in data.get("edges", [])}


def find_cycles(edges, limit=20):
    """Return up to `limit` simple cycles (as node tuples, canonicalized)."""
    graph = defaultdict(set)
    for a, b in edges:
        graph[a].add(b)
    cycles, seen = [], set()
    WHITE, GRAY, BLACK = 0, 1, 2
    color = defaultdict(int)
    stack = []

    def dfs(node):
        if len(cycles) >= limit:
            return
        color[node] = GRAY
        stack.append(node)
        for nxt in graph[node]:
            if color[nxt] == GRAY:
                i = stack.index(nxt)
                cyc = tuple(stack[i:])
                # canonicalize: rotate so smallest element first
                k = cyc.index(min(cyc))
                canon = cyc[k:] + cyc[:k]
                if canon not in seen:
                    seen.add(canon)
                    cycles.append(canon)
            elif color[nxt] == WHITE:
                dfs(nxt)
        stack.pop()
        color[node] = BLACK

    for n in list(graph):
        if color[n] == WHITE:
            dfs(n)
    return cycles


def fan_in(edges):
    fi = defaultdict(int)
    for _, b in edges:
        fi[b] += 1
    return fi


def short(name, maxlen=40):
    return name if len(name) <= maxlen else "…" + name[-(maxlen - 1):]


def mermaid_id(name, table):
    if name not in table:
        table[name] = f"n{len(table)}"
    return table[name]


def build_mermaid(added, removed, hot_nodes, max_nodes=30):
    nodes = {}
    lines = ["graph LR"]
    shown_edges = list(added)[: max_nodes] + list(removed)[: max_nodes // 2]
    involved = []
    for a, b in shown_edges:
        for n in (a, b):
            if n not in nodes and len(nodes) < max_nodes:
                involved.append(n)
                mermaid_id(n, nodes)
    for n in involved:
        lines.append(f'  {nodes[n]}["{short(n)}"]')
    for a, b in added:
        if a in nodes and b in nodes:
            lines.append(f"  {nodes[a]} -->|added| {nodes[b]}")
    for a, b in removed:
        if a in nodes and b in nodes:
            lines.append(f"  {nodes[a]} -.->|removed| {nodes[b]}")
    for n in hot_nodes:
        if n in nodes:
            lines.append(f"  style {nodes[n]} fill:#f88,stroke:#900")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("base")
    ap.add_argument("head")
    ap.add_argument("--fan-in-threshold", type=int, default=5)
    ap.add_argument("--changed-files", default="",
                    help="comma-separated changed file paths/symbols; "
                         "matched as substrings against node names")
    ap.add_argument("--mermaid", action="store_true")
    args = ap.parse_args()

    base, head = load(args.base), load(args.head)
    added = sorted(head - base)
    removed = sorted(base - head)

    base_cycles = set(find_cycles(base))
    head_cycles = set(find_cycles(head))
    new_cycles = [list(c) for c in head_cycles - base_cycles]
    resolved_cycles = [list(c) for c in base_cycles - head_cycles]

    fi_base, fi_head = fan_in(base), fan_in(head)
    threshold = args.fan_in_threshold
    high_fan_in = {n: c for n, c in fi_head.items() if c >= threshold}

    changed = [c for c in args.changed_files.split(",") if c.strip()]
    hot_touched = []
    for node, count in sorted(high_fan_in.items(), key=lambda x: -x[1]):
        if any(c in node or node in c for c in changed):
            dependents = sorted(a for a, b in head if b == node)
            hot_touched.append(
                {"node": node, "fan_in": count, "dependents": dependents})

    fan_in_changes = []
    for node in set(fi_base) | set(fi_head):
        b, h = fi_base.get(node, 0), fi_head.get(node, 0)
        if b != h and max(b, h) >= threshold:
            fan_in_changes.append({"node": node, "before": b, "after": h})
    fan_in_changes.sort(key=lambda x: -(x["after"] - x["before"]))

    out = {
        "summary": {
            "edges_base": len(base), "edges_head": len(head),
            "added": len(added), "removed": len(removed),
            "new_cycles": len(new_cycles),
            "resolved_cycles": len(resolved_cycles),
            "high_fan_in_nodes_touched": len(hot_touched),
        },
        "added_edges": [{"from": a, "to": b} for a, b in added],
        "removed_edges": [{"from": a, "to": b} for a, b in removed],
        "new_cycles": new_cycles,
        "resolved_cycles": resolved_cycles,
        "high_fan_in_touched": hot_touched,
        "fan_in_changes": fan_in_changes,
    }
    if args.mermaid and (added or removed):
        out["mermaid"] = build_mermaid(
            added, removed, [h["node"] for h in hot_touched])

    json.dump(out, sys.stdout, indent=1)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
