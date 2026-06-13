#!/usr/bin/env python3
"""Containment-aware structural detectors for a PR (Python, stdlib ast).

Flat per-level dependency graphs miss problems that only show up when you keep
the module -> class -> function nesting. This emits three text findings (no
graph) from a diff:

  1. encapsulation_leaks  — a changed file imports a private/underscore symbol
                            from another module (reaches past its public surface)
  2. moves                — a top-level symbol kept its name but changed container
                            module/class (the refactor-move signal edge-diffs miss)
  3. misplaced            — a changed function's references point mostly at one
                            *other* module (a move candidate)

Heuristic, not ground truth: confirm each. Renamed-while-moved symbols and
dynamic dispatch are out of scope.

Usage:
  containment_detect.py --base BASE_SHA --head HEAD_SHA [--repo .] \
      [--min-refs 3] [--ratio 0.6] > findings.json
"""
import argparse
import ast
import json
import subprocess
import sys


def git(repo, *args):
    p = subprocess.run(["git", "-C", repo, *args],
                       capture_output=True, text=True)
    return p.stdout if p.returncode == 0 else None


def changed_py_files(repo, base, head):
    out = git(repo, "diff", "--name-only", f"{base}..{head}", "--", "*.py")
    return [l for l in (out or "").splitlines() if l.strip()]


def added_lines(repo, base, head, path):
    """Return the set of new-file line numbers added for `path`."""
    out = git(repo, "diff", f"{base}..{head}", "--unified=0", "--", path) or ""
    lines, new_no = set(), 0
    import re
    for ln in out.splitlines():
        m = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", ln)
        if m:
            new_no = int(m.group(1))
            continue
        if ln.startswith("+") and not ln.startswith("+++"):
            lines.add(new_no)
            new_no += 1
        elif not ln.startswith("-") and not ln.startswith("@@"):
            new_no += 1
    return lines


def module_name(path):
    p = path[:-3] if path.endswith(".py") else path
    return p.replace("/", ".").removeprefix("backend.").removeprefix("src.")


def parse(src):
    try:
        return ast.parse(src)
    except (SyntaxError, ValueError):
        return None


def containment(src, mod):
    """{simple_name: container} for top-level defs and methods."""
    tree = parse(src)
    if tree is None:
        return {}
    out = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out[node.name] = mod
        if isinstance(node, ast.ClassDef):
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out[f"{node.name}.{sub.name}"] = f"{mod}::{node.name}"
    return out


def import_table(tree):
    """{local_name: source_module} and a list of (lineno, module, name, private)."""
    table, leaks = {}, []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            base = node.module or ""
            for a in node.names:
                local = a.asname or a.name
                table[local] = base
                private = (a.name.startswith("_") and not a.name.startswith("__")) \
                    or any(p.startswith("_") for p in base.split("."))
                if private and base.startswith(("app", "src", ".")):
                    leaks.append((node.lineno, base, a.name))
        elif isinstance(node, ast.Import):
            for a in node.names:
                table[a.asname or a.name.split(".")[0]] = a.name
    return table, leaks


# shared-type modules everyone legitimately imports — using them is not misplacement
_SHARED = {"base", "types", "type", "schemas", "schema", "models", "model",
           "constants", "const", "enums", "enum", "config", "settings",
           "exceptions", "errors", "dto", "interfaces", "protocols"}


def _first_party(mod):
    """Project logic modules only — skip stdlib/typing and shared-type packages."""
    if not (mod.startswith(("app", "src")) or mod.startswith(".")):
        return False
    return not any(seg in _SHARED for seg in mod.split("."))


def is_test(path):
    base = path.rsplit("/", 1)[-1]
    return "/tests/" in path or "/test/" in path \
        or base.startswith("test_") or base.endswith("_test.py")


def func_refs(tree, table):
    """[(func_name, lineno, end, {module: count})] for top-level funcs + methods."""
    out = []

    def refs(node):
        counts = {}
        for n in ast.walk(node):
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
                mod = table.get(n.id)
                if mod and _first_party(mod):
                    counts[mod] = counts.get(mod, 0) + 1
        return counts

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.append((node.name, node.lineno, node.end_lineno, refs(node)))
        if isinstance(node, ast.ClassDef):
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out.append((f"{node.name}.{sub.name}", sub.lineno,
                                sub.end_lineno, refs(sub)))
    return out


def detect(repo, base, head, min_refs, ratio):
    files = changed_py_files(repo, base, head)
    base_map, head_map = {}, {}
    leaks, misplaced = [], []

    for path in files:
        if is_test(path):  # tests legitimately reach into privates / their target module
            continue
        mod = module_name(path)
        b_src = git(repo, "show", f"{base}:{path}")
        h_src = git(repo, "show", f"{head}:{path}")
        if b_src:
            base_map.update(containment(b_src, mod))
        if not h_src:
            continue
        head_map.update(containment(h_src, mod))
        tree = parse(h_src)
        if tree is None:
            continue
        table, file_leaks = import_table(tree)
        for lineno, src_mod, name in file_leaks:
            leaks.append({"file": path, "line": lineno,
                          "imports": f"{src_mod}.{name}",
                          "why": "imports a private (_underscore) symbol"})
        adds = added_lines(repo, base, head, path)
        for fname, lo, hi, counts in func_refs(tree, table):
            if hi and adds and not any(lo <= n <= hi for n in adds):
                continue  # only functions that the PR actually touched
            total = sum(counts.values())
            if total < min_refs:
                continue
            top_mod, top = max(counts.items(), key=lambda x: x[1])
            if top / total >= ratio and not top_mod.startswith(mod) \
                    and mod not in top_mod:
                misplaced.append({"file": path, "function": fname,
                                  "leans_on": top_mod,
                                  "refs": f"{top}/{total}"})

    moves = []
    for name, head_ctr in head_map.items():
        base_ctr = base_map.get(name)
        if base_ctr and base_ctr != head_ctr:
            moves.append({"symbol": name, "from": base_ctr, "to": head_ctr})

    return {
        "summary": {"changed_py_files": len(files),
                    "encapsulation_leaks": len(leaks),
                    "moves": len(moves), "misplaced": len(misplaced)},
        "encapsulation_leaks": leaks,
        "moves": moves,
        "misplaced": misplaced,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", required=True)
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--min-refs", type=int, default=3)
    ap.add_argument("--ratio", type=float, default=0.6)
    args = ap.parse_args()
    out = detect(args.repo, args.base, args.head, args.min_refs, args.ratio)
    json.dump(out, sys.stdout, indent=1)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
