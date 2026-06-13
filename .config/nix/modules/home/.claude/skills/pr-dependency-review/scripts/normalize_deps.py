#!/usr/bin/env python3
"""Normalize dependency/call-graph tool outputs into a common edge-list JSON.

Common format:
  {"granularity": "module|class|function", "edges": [{"from": "a", "to": "b"}]}

Supported input formats (--format):
  depcruise   dependency-cruiser JSON (npx depcruise src --output-type json)
  madge       madge JSON            (npx madge --json src)
  pydeps      pydeps JSON           (pydeps pkg --show-deps --no-output)
  gomod       `go mod graph` text
  golist      `go list -deps -json ./...` output (module-internal package deps)
  dot         any Graphviz DOT file (code2flow, go-callvis, pyreverse,
              java-callgraph wrappers, ts call-graph tools, ...)
  edges       plain text, one "from -> to" or "from to" per line

Usage:
  normalize_deps.py INPUT --format depcruise --granularity module > out.json
  cat graph.dot | normalize_deps.py - --format dot --granularity function
"""
import argparse
import json
import re
import sys


def read_input(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def parse_depcruise(text: str):
    data = json.loads(text)
    edges = []
    for mod in data.get("modules", []):
        src = mod.get("source", "")
        for dep in mod.get("dependencies", []):
            dst = dep.get("resolved") or dep.get("module")
            if src and dst:
                edges.append((src, dst))
    return edges


def parse_madge(text: str):
    data = json.loads(text)
    return [(src, dst) for src, deps in data.items() for dst in deps]


def parse_pydeps(text: str):
    data = json.loads(text)
    edges = []
    for name, info in data.items():
        for imp in (info.get("imports") or []):
            edges.append((name, imp))
    return edges


def parse_gomod(text: str):
    edges = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 2:
            edges.append((parts[0], parts[1]))
    return edges


def parse_golist(text: str):
    # `go list -deps -json ./...` emits a stream of JSON objects
    decoder = json.JSONDecoder()
    idx, objs = 0, []
    text = text.strip()
    while idx < len(text):
        try:
            obj, offset = decoder.raw_decode(text[idx:])
        except json.JSONDecodeError:
            break
        idx += offset
        while idx < len(text) and text[idx] in " \r\n\t":
            idx += 1
        objs.append(obj)
    stdlib = {o.get("ImportPath") for o in objs if o.get("Standard")}
    edges = []
    for obj in objs:
        if obj.get("Standard"):
            continue
        pkg = obj.get("ImportPath", "")
        for imp in obj.get("Imports") or []:
            if imp not in stdlib:
                edges.append((pkg, imp))
    return edges


DOT_EDGE = re.compile(
    r'^\s*"?([^"\->\s][^"\->]*?)"?\s*->\s*"?([^"\[;]+?)"?\s*(?:\[[^\]]*\])?\s*;?\s*$'
)

# A node-definition line carrying a name= attribute (code2flow puts the real
# "file::func" symbol there while using an opaque node_xxxx id). pyreverse uses
# label=<HTML record> with no name=, so it never matches and its ids stand.
DOT_NODE_NAME = re.compile(r'^\s*"?([^"\[\s]+)"?\s*\[[^\]]*\bname="([^"]*)"')


def parse_dot(text: str):
    id_to_name = {}
    for line in text.splitlines():
        if "->" in line:
            continue
        m = DOT_NODE_NAME.match(line)
        if m:
            id_to_name[m.group(1).strip()] = m.group(2).strip()

    edges = []
    for line in text.splitlines():
        if "->" not in line:
            continue
        m = DOT_EDGE.match(line)
        if m:
            a, b = m.group(1).strip(), m.group(2).strip()
            edges.append((id_to_name.get(a, a), id_to_name.get(b, b)))
    return edges


def parse_edges(text: str):
    edges = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "->" in line:
            a, _, b = line.partition("->")
        else:
            parts = line.split()
            if len(parts) != 2:
                continue
            a, b = parts
        edges.append((a.strip(), b.strip()))
    return edges


PARSERS = {
    "depcruise": parse_depcruise,
    "madge": parse_madge,
    "pydeps": parse_pydeps,
    "gomod": parse_gomod,
    "golist": parse_golist,
    "dot": parse_dot,
    "edges": parse_edges,
}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", help="input file or - for stdin")
    ap.add_argument("--format", required=True, choices=sorted(PARSERS))
    ap.add_argument("--granularity", default="module",
                    choices=["module", "class", "function"])
    ap.add_argument("--strip-prefix", default="",
                    help="prefix to strip from node names (e.g. repo path)")
    ap.add_argument("--exclude", default="node_modules,vendor,dist,build",
                    help="comma-separated substrings; edges touching them are dropped")
    args = ap.parse_args()

    raw = PARSERS[args.format](read_input(args.input))
    excludes = [e for e in args.exclude.split(",") if e]
    seen, edges = set(), []
    for a, b in raw:
        if args.strip_prefix:
            a = a.removeprefix(args.strip_prefix)
            b = b.removeprefix(args.strip_prefix)
        if a == b:
            continue
        if any(x in a or x in b for x in excludes):
            continue
        key = (a, b)
        if key in seen:
            continue
        seen.add(key)
        edges.append({"from": a, "to": b})

    json.dump({"granularity": args.granularity, "edges": edges},
              sys.stdout, indent=1)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
