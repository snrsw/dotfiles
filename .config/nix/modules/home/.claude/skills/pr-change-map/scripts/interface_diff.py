#!/usr/bin/env python3
"""Diff two function-definition inventories: the L1 boundary delta.

Input: two JSON files as produced by `astgrep_extract.py defs`
({"functions": [{"file", "name", "line", "signature"}]}), one at BASE_SHA and
one at HEAD. Output: which functions were added, removed, or changed their
signature — the facts a reader needs to know whether the component's promises
to its neighbours moved.

  interface_diff.py /tmp/defs-base.json /tmp/defs-head.json > /tmp/iface.json

The most valuable result is often the empty one: added, removed, and changed
all empty means "public surface unchanged, verified" — which licenses a reader
to skip everything outside the component.

Limits: functions are keyed by (file, name), so a rename — and a move across
files — reports as removed + added, not as a change. Overloads sharing a name
compare as the set of their signatures.
"""
import argparse
import json
import sys
from collections import defaultdict


def _by_key(defs):
    """Group definitions by (file, name) → sorted signature list."""
    table = defaultdict(list)
    for d in defs:
        table[(d["file"], d["name"])].append(d)
    return table


def _entry(d):
    return {"file": d["file"], "name": d["name"],
            "line": d["line"], "signature": d["signature"]}


def diff_defs(base, head):
    """Added / removed / signature-changed functions between two inventories."""
    b, h = _by_key(base), _by_key(head)

    added = [_entry(d) for key in sorted(h.keys() - b.keys()) for d in h[key]]
    removed = [_entry(d) for key in sorted(b.keys() - h.keys()) for d in b[key]]

    changed, unchanged = [], 0
    for key in sorted(b.keys() & h.keys()):
        before = sorted(d["signature"] for d in b[key])
        after = sorted(d["signature"] for d in h[key])
        if before == after:
            unchanged += 1
        else:
            changed.append({
                "file": key[0], "name": key[1],
                "line": min(d["line"] for d in h[key]),
                "before": before, "after": after,
            })

    return {"added": added, "removed": removed,
            "changed": changed, "unchanged": unchanged}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("base", help="defs JSON at BASE_SHA")
    ap.add_argument("head", help="defs JSON at HEAD")
    args = ap.parse_args()

    with open(args.base, encoding="utf-8") as f:
        base = json.load(f).get("functions", [])
    with open(args.head, encoding="utf-8") as f:
        head = json.load(f).get("functions", [])

    out = diff_defs(base, head)
    out["summary"] = {
        "added": len(out["added"]), "removed": len(out["removed"]),
        "changed": len(out["changed"]), "unchanged": out["unchanged"],
        "surface_unchanged": not (out["added"] or out["removed"] or out["changed"]),
    }
    json.dump(out, sys.stdout, indent=1)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
