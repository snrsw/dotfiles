#!/usr/bin/env python3
"""Extract dependency edges, call edges, and complexity from source using ast-grep.

ast-grep bundles tree-sitter grammars in one static binary, so this gives real
AST analysis for ~20 languages with a single zero-install runner — no per-language
tool zoo, no grammar compilation. Output matches the normalized edge-list contract
that diff_deps.py and call_graph_slice.py consume.

Usage:
  astgrep_extract.py imports    --lang python src/       > deps-head.json
  astgrep_extract.py calls      --lang python src/       > callgraph-head.json
  astgrep_extract.py complexity --lang python src/a.py   > cc-head.json
  astgrep_extract.py defs       --lang python src/       > defs.json
  astgrep_extract.py langs

Language is inferred from file extensions when --lang is omitted and every path
resolves to the same language.

The binary is found via $ASTGREP_BIN, then `ast-grep`, then `sg` on PATH. Set
ASTGREP_BIN to a zero-install runner when it is not installed, e.g.
  ASTGREP_BIN="nix run nixpkgs#ast-grep --"
  ASTGREP_BIN="npx --yes @ast-grep/cli"

Caveat: matching is syntactic. Call edges are resolved by NAME, so same-named
symbols in different scopes are conflated, and dynamic dispatch is invisible —
the same limitation the language references note for grep-based fallbacks, but
with correct parsing of the constructs it does see.
"""
import argparse
import json
import os
import shlex
import shutil
import subprocess
import tempfile
import sys

# Node kinds below were probed with `ast-grep run --debug-query=ast` against the
# grammars ast-grep ships. `branch` lists the decision points counted for
# cyclomatic complexity (CC = 1 + branches inside the function).
LANGS = {
    "python": {
        "ext": [".py"],
        "func_def": ["function_definition"],
        "import": ["import $NAME", "from $NAME import $$$"],
        "call": ["$NAME($$$)"],
        "branch": [
            "if_statement", "elif_clause", "for_statement", "while_statement",
            "except_clause", "conditional_expression", "boolean_operator",
            "case_clause", "assert_statement",
        ],
    },
    "javascript": {
        "ext": [".js", ".jsx", ".mjs", ".cjs"],
        "func_def": ["function_declaration", "method_definition", "arrow_function"],
        "import": ['import $$$ from "$NAME"', 'require("$NAME")'],
        "call": ["$NAME($$$)"],
        "branch": [
            "if_statement", "for_statement", "for_in_statement", "while_statement",
            "do_statement", "catch_clause", "ternary_expression", "switch_case",
        ],
    },
    "typescript": {
        "ext": [".ts", ".mts", ".cts"],
        "func_def": ["function_declaration", "method_definition", "arrow_function"],
        "import": ['import $$$ from "$NAME"', 'require("$NAME")'],
        "call": ["$NAME($$$)"],
        "branch": [
            "if_statement", "for_statement", "for_in_statement", "while_statement",
            "do_statement", "catch_clause", "ternary_expression", "switch_case",
        ],
    },
    "tsx": {
        "ext": [".tsx"],
        "func_def": ["function_declaration", "method_definition", "arrow_function"],
        "import": ['import $$$ from "$NAME"', 'require("$NAME")'],
        "call": ["$NAME($$$)"],
        "branch": [
            "if_statement", "for_statement", "for_in_statement", "while_statement",
            "do_statement", "catch_clause", "ternary_expression", "switch_case",
        ],
    },
    "go": {
        "ext": [".go"],
        "func_def": ["function_declaration", "method_declaration"],
        "import": ['import "$NAME"'],
        "call": ["$NAME($$$)"],
        "branch": [
            "if_statement", "for_statement", "expression_case", "type_case",
            "select_statement", "communication_case",
        ],
    },
    "java": {
        "ext": [".java"],
        "func_def": ["method_declaration", "constructor_declaration"],
        "import": ["import $NAME;"],
        "call": ["$NAME($$$)"],
        "branch": [
            "if_statement", "for_statement", "enhanced_for_statement",
            "while_statement", "do_statement", "catch_clause",
            "ternary_expression", "switch_label",
        ],
    },
    "rust": {
        "ext": [".rs"],
        "func_def": ["function_item"],
        "import": ["use crate::$NAME::$$$", "use $NAME::$$$"],
        "call": ["$NAME($$$)"],
        "branch": [
            "if_expression", "match_arm", "for_expression", "while_expression",
            "loop_expression",
        ],
    },
    "ruby": {
        "ext": [".rb"],
        "func_def": ["method", "singleton_method"],
        "import": ['require "$NAME"', 'require_relative "$NAME"'],
        "call": ["$NAME($$$)"],
        "branch": [
            "if", "elsif", "unless", "while", "until", "for", "when", "rescue",
            "conditional",
        ],
    },
    "c": {
        "ext": [".c", ".h"],
        "func_def": ["function_definition"],
        "import": ["#include <$NAME>", '#include "$NAME"'],
        "call": ["$NAME($$$)"],
        "branch": [
            "if_statement", "for_statement", "while_statement", "do_statement",
            "case_statement", "conditional_expression",
        ],
    },
    "cpp": {
        "ext": [".cpp", ".cc", ".cxx", ".hpp"],
        "func_def": ["function_definition"],
        "import": ["#include <$NAME>", '#include "$NAME"'],
        "call": ["$NAME($$$)"],
        "branch": [
            "if_statement", "for_statement", "while_statement", "do_statement",
            "case_statement", "conditional_expression", "catch_clause",
        ],
    },
    "csharp": {
        "ext": [".cs"],
        "func_def": ["method_declaration", "constructor_declaration"],
        "import": ["using $NAME;"],
        "call": ["$NAME($$$)"],
        "branch": [
            "if_statement", "for_statement", "foreach_statement", "while_statement",
            "do_statement", "catch_clause", "conditional_expression", "switch_section",
        ],
    },
    "php": {
        "ext": [".php"],
        "func_def": ["function_definition", "method_declaration"],
        "import": ["use $NAME;", 'require "$NAME"'],
        "call": ["$NAME($$$)"],
        "branch": [
            "if_statement", "for_statement", "foreach_statement", "while_statement",
            "do_statement", "catch_clause", "conditional_expression", "case_statement",
        ],
    },
    "kotlin": {
        "ext": [".kt", ".kts"],
        "func_def": ["function_declaration"],
        "import": ["import $NAME"],
        "call": ["$NAME($$$)"],
        "branch": [
            "if_expression", "for_statement", "while_statement", "do_while_statement",
            "when_entry", "catch_block",
        ],
    },
    "swift": {
        "ext": [".swift"],
        "func_def": ["function_declaration"],
        "import": ["import $NAME"],
        "call": ["$NAME($$$)"],
        "branch": [
            "if_statement", "for_statement", "while_statement", "repeat_while_statement",
            "switch_entry", "catch_block", "guard_statement",
        ],
    },
}


# ---------------------------------------------------------------- pure helpers

def lang_for_path(path):
    """Map a file path to a LANGS key, or None when the extension is unknown."""
    ext = os.path.splitext(path)[1]
    if not ext:
        return None
    for lang, spec in LANGS.items():
        if ext in spec["ext"]:
            return lang
    return None


def build_rule(lang, kinds, capture_name=False):
    """Build an ast-grep inline rule (YAML) matching any of `kinds`."""
    lines = [f"id: extract", f"language: {lang}", "rule:", "  any:"]
    for kind in kinds:
        lines.append(f"    - kind: {kind}")
    if capture_name:
        # Re-express as an `all` so the name capture applies to whichever kind hit.
        lines = [f"id: extract", f"language: {lang}", "rule:", "  all:", "    - any:"]
        for kind in kinds:
            lines.append(f"        - kind: {kind}")
        lines += [
            "    - has:",
            "        field: name",
            "        pattern: $NAME",
        ]
    return "\n".join(lines) + "\n"


def _byte_range(m):
    off = m["range"]["byteOffset"]
    return off["start"], off["end"]


def _innermost_container(containers, m):
    """The smallest container whose byte range encloses `m`, same file. None if outside."""
    bs, be = _byte_range(m)
    best, best_size = None, None
    for c in containers:
        if c["file"] != m["file"]:
            continue
        cs, ce = _byte_range(c)
        if cs <= bs and be <= ce:
            size = ce - cs
            if best_size is None or size < best_size:
                best, best_size = c, size
    return best


def _name_of(m):
    return m.get("metaVariables", {}).get("single", {}).get("NAME", {}).get("text")


def assign_complexity(func_matches, branch_matches):
    """Cyclomatic complexity per function: 1 + branches inside it.

    A branch counts once, for the innermost function enclosing it. Branches at
    module level (outside every function) are ignored.
    """
    counts = {id(f): 0 for f in func_matches}
    for b in branch_matches:
        owner = _innermost_container(func_matches, b)
        if owner is not None:
            counts[id(owner)] += 1
    out = [
        {
            "file": f["file"],
            "name": _name_of(f) or "<anonymous>",
            "line": f["range"]["start"]["line"] + 1,
            "complexity": 1 + counts[id(f)],
        }
        for f in func_matches
    ]
    out.sort(key=lambda r: (-r["complexity"], r["file"], r["name"]))
    return out


def signature_of(text):
    """A function's signature, cut from its full definition text.

    Language-neutral scanner: walk the text tracking () and [] depth, stop at
    the first `{`, `:`, `;`, or newline at depth 0, then collapse whitespace.
    Newlines inside parens survive, so multi-line parameter lists compare as
    one line. Known limit: Kotlin/Swift return types (`): Int {`) are cut at
    the colon, so a return-type-only change there reads as unchanged.
    """
    depth = 0
    out = []
    for ch in text:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        elif depth == 0 and ch in "{:;\n":
            break
        out.append(ch)
    return " ".join("".join(out).split())


def _rel(path, repo):
    if repo:
        return os.path.relpath(path, repo)
    return path


def matches_to_import_edges(matches, repo=None):
    """file -> imported-module edges. Matches without a $NAME capture are skipped."""
    edges = []
    for m in matches:
        name = _name_of(m)
        if not name:
            continue
        edges.append({"from": _rel(m["file"], repo), "to": name})
    return edges


def matches_to_call_edges(func_matches, call_matches, repo=None):
    """caller -> callee edges. Caller is the enclosing function, else the file.

    Self-recursive edges are dropped: they add a self-loop to every call graph
    without telling a reader anything about coupling.
    """
    edges = []
    for c in call_matches:
        callee = _name_of(c)
        if not callee:
            continue
        owner = _innermost_container(func_matches, c)
        caller = _name_of(owner) if owner is not None else _rel(c["file"], repo)
        if caller == callee:
            continue
        edges.append({"from": caller, "to": callee})
    return edges


def dedupe_matches(matches):
    """Keep one match per source span, first pattern wins.

    A language lists several import patterns and more than one can hit the same
    line: Rust's `use crate::$NAME::$$$` and `use $NAME::$$$` both match
    `use crate::auth::verify`, giving `auth` and `crate::auth`. Left alone that
    counts one import twice and inflates the target's fan-in. Patterns are
    ordered most-specific-first, so the first hit on a span is the right one.
    """
    seen, out = set(), []
    for m in matches:
        key = (m["file"], *_byte_range(m))
        if key in seen:
            continue
        seen.add(key)
        out.append(m)
    return out


def dedupe_edges(edges):
    seen = {(e["from"], e["to"]) for e in edges}
    return [{"from": f, "to": t} for f, t in sorted(seen)]


# ------------------------------------------------------------- ast-grep driver

def astgrep_argv():
    """Resolve the ast-grep invocation, honouring $ASTGREP_BIN for zero-install runners."""
    env = os.environ.get("ASTGREP_BIN")
    if env:
        return shlex.split(env)
    for name in ("ast-grep", "sg"):
        if shutil.which(name):
            return [name]
    sys.exit(
        "ast-grep not found. Install it, or set ASTGREP_BIN to a zero-install runner:\n"
        '  ASTGREP_BIN="nix run nixpkgs#ast-grep --"\n'
        '  ASTGREP_BIN="npx --yes @ast-grep/cli"'
    )


def is_bad_rule(stderr):
    """ast-grep rejects an unknown node kind at rule-parse time, before scanning.

    That is the difference between this and a grep fallback: a wrong kind is a
    hard error, never a silently short result. Never swallow it — a silent
    undercount would report low complexity for code that is branch-heavy.
    """
    return "invalid kind" in stderr or "Cannot parse rule" in stderr


def _run(argv):
    proc = subprocess.run(argv, capture_output=True, text=True)
    if is_bad_rule(proc.stderr):
        sys.exit(
            "ast-grep rejected the rule — a node kind in the LANGS table does not\n"
            "exist in this grammar version. Run `astgrep_extract.py verify` to find\n"
            f"which one.\n\n{proc.stderr}"
        )
    if proc.returncode != 0 and not proc.stdout.strip():
        sys.stderr.write(proc.stderr)
        return []
    try:
        return json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        sys.stderr.write(f"could not parse ast-grep output: {proc.stdout[:200]}\n")
        return []


def verify_kinds():
    """Check every node kind in LANGS against the installed grammars.

    Kinds drift between ast-grep releases. This makes the table self-checking
    instead of trusting that it was right when written.
    """
    argv, bad, total = astgrep_argv(), [], 0
    with tempfile.TemporaryDirectory() as probe:
        for lang, spec in sorted(LANGS.items()):
            for group in ("func_def", "branch"):
                for kind in spec[group]:
                    total += 1
                    proc = subprocess.run(
                        argv + ["scan", "--inline-rules", build_rule(lang, [kind]),
                                "--json=compact", probe],
                        capture_output=True, text=True,
                    )
                    if is_bad_rule(proc.stderr):
                        bad.append((lang, group, kind))
    for lang, group, kind in bad:
        print(f"INVALID  {lang:<12} {group}: {kind}")
    print(f"checked {total} kinds across {len(LANGS)} languages, {len(bad)} invalid")
    return 1 if bad else 0


def scan_kinds(lang, kinds, paths, capture_name=False):
    rule = build_rule(lang, kinds, capture_name=capture_name)
    return _run(astgrep_argv() + ["scan", "--inline-rules", rule, "--json=compact", *paths])


def scan_patterns(lang, patterns, paths):
    """Run each pattern in order; a span already claimed by an earlier one is dropped."""
    matches = []
    for pat in patterns:
        matches += _run(
            astgrep_argv() + ["run", "-p", pat, "-l", lang, "--json=compact", *paths]
        )
    return dedupe_matches(matches)


# ---------------------------------------------------------------------- driver

def resolve_lang(explicit, paths):
    if explicit:
        if explicit not in LANGS:
            sys.exit(f"unsupported language {explicit!r}; try `langs`")
        return explicit
    found = {lang_for_path(p) for p in paths if os.path.isfile(p)}
    found.discard(None)
    if len(found) == 1:
        return found.pop()
    sys.exit("could not infer a single language from the paths; pass --lang")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("mode", choices=["imports", "calls", "complexity", "defs", "langs", "verify"])
    # No default here: argparse leaves an unconsumed nargs="*" at its default,
    # and merging that with the leftovers below would silently scan "." in
    # addition to the paths the caller asked for. The fallback is applied after
    # the merge instead.
    ap.add_argument("paths", nargs="*", default=[])
    ap.add_argument("--lang")
    ap.add_argument("--repo", help="strip this prefix from file paths in node names")
    # argparse cannot backfill a trailing nargs="*" positional once an optional
    # appears between it and `mode`, so `complexity --lang python src/` would be
    # rejected. Collect the leftovers as paths instead of dictating flag order.
    args, extra = ap.parse_known_args()
    unknown = [e for e in extra if e.startswith("-")]
    if unknown:
        ap.error(f"unrecognized arguments: {' '.join(unknown)}")
    args.paths = list(args.paths) + [e for e in extra if not e.startswith("-")]

    if args.mode == "verify":
        sys.exit(verify_kinds())

    if args.mode == "langs":
        for lang, spec in sorted(LANGS.items()):
            print(f"{lang:<12} {' '.join(spec['ext'])}")
        return

    paths = args.paths or ["."]
    lang = resolve_lang(args.lang, paths)
    spec = LANGS[lang]

    if args.mode == "imports":
        matches = scan_patterns(lang, spec["import"], paths)
        edges = dedupe_edges(matches_to_import_edges(matches, repo=args.repo))
        print(json.dumps({"granularity": "module", "edges": edges}, indent=1))

    elif args.mode == "calls":
        funcs = scan_kinds(lang, spec["func_def"], paths, capture_name=True)
        calls = scan_patterns(lang, spec["call"], paths)
        edges = dedupe_edges(matches_to_call_edges(funcs, calls, repo=args.repo))
        print(json.dumps({"granularity": "function", "edges": edges}, indent=1))

    elif args.mode == "complexity":
        funcs = scan_kinds(lang, spec["func_def"], paths, capture_name=True)
        branches = scan_kinds(lang, spec["branch"], paths)
        print(json.dumps({"functions": assign_complexity(funcs, branches)}, indent=1))

    elif args.mode == "defs":
        funcs = scan_kinds(lang, spec["func_def"], paths, capture_name=True)
        out = [
            {
                "file": _rel(f["file"], args.repo),
                "name": _name_of(f) or "<anonymous>",
                "line": f["range"]["start"]["line"] + 1,
                "signature": signature_of(f["text"]),
            }
            for f in funcs
        ]
        print(json.dumps({"functions": sorted(out, key=lambda r: (r["file"], r["line"]))}, indent=1))


if __name__ == "__main__":
    main()
