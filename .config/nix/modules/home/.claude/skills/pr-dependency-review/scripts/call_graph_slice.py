#!/usr/bin/env python3
"""Extract a blast-radius slice of a call graph around changed symbols.

BFS from each changed symbol: callers (reverse edges) up to --depth, and
callees (forward) up to --callee-depth. Outputs the sliced edge list plus a
Mermaid graph with changed nodes red and transitive callers yellow.

Usage:
  call_graph_slice.py callgraph.json --changed "funcA,Cls.method" \
      --depth 2 --callee-depth 1 --mermaid > blast.json

Node matching is substring-based, so "parse_config" matches
"src/config.py::parse_config".
"""
import argparse
import json
import sys
from collections import defaultdict, deque


def load(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return [(e["from"], e["to"]) for e in data.get("edges", [])]


def bfs(start_nodes, adjacency, depth):
    dist = {n: 0 for n in start_nodes}
    q = deque(start_nodes)
    while q:
        cur = q.popleft()
        if dist[cur] >= depth:
            continue
        for nxt in adjacency[cur]:
            if nxt not in dist:
                dist[nxt] = dist[cur] + 1
                q.append(nxt)
    return dist


def short(name, maxlen=45):
    return name if len(name) <= maxlen else "…" + name[-(maxlen - 1):]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("graph", help="normalized call-graph JSON")
    ap.add_argument("--changed", required=True,
                    help="comma-separated changed symbol names (substring match)")
    ap.add_argument("--depth", type=int, default=2, help="caller depth")
    ap.add_argument("--callee-depth", type=int, default=1)
    ap.add_argument("--max-nodes", type=int, default=30)
    ap.add_argument("--mermaid", action="store_true")
    args = ap.parse_args()

    edges = load(args.graph)
    fwd, rev = defaultdict(set), defaultdict(set)
    nodes = set()
    for a, b in edges:
        fwd[a].add(b)
        rev[b].add(a)
        nodes.update((a, b))

    patterns = [p.strip() for p in args.changed.split(",") if p.strip()]
    changed = {n for n in nodes if any(p in n for p in patterns)}
    unmatched = [p for p in patterns if not any(p in n for n in nodes)]

    callers = bfs(changed, rev, args.depth)
    callees = bfs(changed, fwd, args.callee_depth)
    keep = set(callers) | set(callees)

    sliced = [(a, b) for a, b in edges if a in keep and b in keep]
    direct_callers = sorted(
        {a for a, b in edges if b in changed and a not in changed})

    out = {
        "changed_symbols_matched": sorted(changed),
        "patterns_not_found": unmatched,
        "direct_callers": direct_callers,
        "transitive_caller_count": len(
            [n for n in callers if n not in changed]),
        "sliced_edges": [{"from": a, "to": b} for a, b in sliced],
    }

    if args.mermaid:
        ranked = sorted(
            keep, key=lambda n: (n not in changed,
                                 callers.get(n, 99), callees.get(n, 99)))
        shown = set(ranked[: args.max_nodes])
        ids, lines = {}, ["graph TD"]
        for n in ranked:
            if n in shown:
                ids[n] = f"n{len(ids)}"
                lines.append(f'  {ids[n]}["{short(n)}"]')
        for a, b in sliced:
            if a in shown and b in shown:
                lines.append(f"  {ids[a]} --> {ids[b]}")
        for n in shown:
            if n in changed:
                lines.append(f"  style {ids[n]} fill:#f88,stroke:#900")
            elif n in callers:
                lines.append(f"  style {ids[n]} fill:#ffd966,stroke:#b8860b")
        out["mermaid"] = "\n".join(lines)
        out["mermaid_truncated"] = len(keep) > len(shown)

    json.dump(out, sys.stdout, indent=1)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
