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


def fan_in_changes(fi_base, fi_head, threshold):
    """Every node whose fan-in moved, largest movement first.

    The threshold flags rows (`highlighted`); it never removes them. It used to
    gate inclusion, which meant a small repo's real 1 → 2 move was simply
    absent from the JSON while the brief template required a fan-in for every
    changed node — so the number had to be recomputed by hand. A filter
    parameter must not suppress data a template treats as mandatory.
    """
    out = []
    for node in set(fi_base) | set(fi_head):
        before, after = fi_base.get(node, 0), fi_head.get(node, 0)
        if before == after:
            continue
        out.append({
            "node": node, "before": before, "after": after,
            "highlighted": max(before, after) >= threshold,
        })
    out.sort(key=lambda c: (-abs(c["after"] - c["before"]), c["node"]))
    return out


def fan_in_stats(fi):
    """Median and max fan-in over nodes that have any incoming edge.

    Calibration for the brief: "fan-in 7" means nothing to a reader who does
    not know the repo — "7 (repo median 2, max 9)" places it without grading it.
    """
    counts = sorted(fi.values())
    if not counts:
        return {"median": 0, "max": 0}
    n = len(counts)
    mid = n // 2
    median = float(counts[mid]) if n % 2 else (counts[mid - 1] + counts[mid]) / 2
    return {"median": median, "max": counts[-1]}


def short(name, maxlen=40):
    return name if len(name) <= maxlen else "…" + name[-(maxlen - 1):]


def mermaid_id(name, table):
    if name not in table:
        table[name] = f"n{len(table)}"
    return table[name]


def build_mermaid(added, removed, hot_nodes, max_nodes=30, context=None,
                  max_context=10):
    """Mermaid diff graph; `context` adds surroundings for the L0 rung.

    Context edges are unchanged head edges whose BOTH endpoints are already on
    the graph, drawn plain. They anchor the diff in existing structure without
    adding a single node — a diff-only graph floats in space otherwise.
    """
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
    if context:
        diffed = set(added) | set(removed)
        diffed_nodes = {n for e in diffed for n in e}
        # Unchanged edges touching a diffed node; neighbours may enter (within
        # the node budget), unrelated corners of the repo may not.
        candidates = [e for e in sorted(context - diffed)
                      if e[0] in diffed_nodes or e[1] in diffed_nodes]
        drawn = 0
        for a, b in candidates:
            if drawn >= max_context:
                break
            for n in (a, b):
                if n not in nodes:
                    if len(nodes) >= max_nodes:
                        break
                    mermaid_id(n, nodes)
                    lines.append(f'  {nodes[n]}["{short(n)}"]')
            if a in nodes and b in nodes:
                lines.append(f"  {nodes[a]} --> {nodes[b]}")
                drawn += 1
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

    changes = fan_in_changes(fi_base, fi_head, threshold)

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
        "fan_in_changes": changes,
        # repo-wide calibration for the numbers above (head graph)
        "fan_in_stats": fan_in_stats(fi_head),
    }
    if args.mermaid and (added or removed):
        out["mermaid"] = build_mermaid(
            added, removed, [h["node"] for h in hot_touched], context=head)

    json.dump(out, sys.stdout, indent=1)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
