# ast-grep: the default analysis backend

Try this **before** the language-specific references. ast-grep bundles
tree-sitter grammars in one static binary, so a single zero-install runner gives
real AST analysis for every language in the table below. There is no per-language
tool to install, no grammar to compile, and nothing to thrash against in CI.

`scripts/astgrep_extract.py` wraps it and emits the normalized edge-list JSON
that `diff_deps.py` and `call_graph_slice.py` already consume.

## Getting the binary

The script looks for `$ASTGREP_BIN`, then `ast-grep`, then `sg` on PATH. When it
is installed (this repo's `home.nix` lists it in `home.packages`), nothing needs
setting. Otherwise point the variable at a zero-install runner:

```bash
export ASTGREP_BIN="nix run nixpkgs#ast-grep --"     # nix
export ASTGREP_BIN="npx --yes @ast-grep/cli"          # node
```

The kind table below was checked against **0.40.0 and 0.44.1**, which agree on
all 128 kinds. Treat any other version as unverified until `verify` says
otherwise.

Per Step 3's rule: try one runner, and if it fails go straight to
`references/generic.md`'s grep path. Do not chase installers.

## The four modes

```bash
# module-level dependency edges (Step 3/4)
python3 scripts/astgrep_extract.py imports --lang python --repo . src/ > /tmp/deps-head.json

# function-level call edges (Step 5)
python3 scripts/astgrep_extract.py calls --lang python --repo . src/ > /tmp/callgraph-head.json

# per-function cyclomatic complexity (Step 6)
python3 scripts/astgrep_extract.py complexity --lang python src/ > /tmp/cc-head.json

# every function definition, for the uncalled-exports check (Step 5)
python3 scripts/astgrep_extract.py defs --lang python --repo . src/ > /tmp/defs.json
```

`--lang` is optional when every path resolves to one language by extension.
`--repo <dir>` strips that prefix so node names are repo-relative and comparable
between the base worktree and HEAD.

Base-vs-head, the shape Step 3 asks for:

```bash
git worktree add /tmp/base-tree $BASE_SHA
python3 scripts/astgrep_extract.py imports --lang go --repo /tmp/base-tree /tmp/base-tree > /tmp/deps-base.json
python3 scripts/astgrep_extract.py imports --lang go --repo .            .              > /tmp/deps-head.json
git worktree remove /tmp/base-tree --force
python3 scripts/diff_deps.py /tmp/deps-base.json /tmp/deps-head.json --fan-in-threshold 5 --mermaid
```

Complexity feeds Step 6 directly: run `complexity` in both trees and pair the
functions by name to get before → after.

## Languages covered

| Language | Extensions | Function-definition kinds |
|---|---|---|
| python | `.py` | `function_definition` |
| javascript | `.js .jsx .mjs .cjs` | `function_declaration`, `method_definition`, `arrow_function` |
| typescript | `.ts .mts .cts` | `function_declaration`, `method_definition`, `arrow_function` |
| tsx | `.tsx` | `function_declaration`, `method_definition`, `arrow_function` |
| go | `.go` | `function_declaration`, `method_declaration` |
| java | `.java` | `method_declaration`, `constructor_declaration` |
| rust | `.rs` | `function_item` |
| ruby | `.rb` | `method`, `singleton_method` |
| c | `.c .h` | `function_definition` |
| cpp | `.cpp .cc .cxx .hpp` | `function_definition` |
| csharp | `.cs` | `method_declaration`, `constructor_declaration` |
| php | `.php` | `function_definition`, `method_declaration` |
| kotlin | `.kt .kts` | `function_declaration` |
| swift | `.swift` | `function_declaration` |

ast-grep supports more languages than this table. Adding one means adding a row
to `LANGS` in `astgrep_extract.py` with its function-definition kinds, import
patterns, and branch kinds, then running `verify` below.

## Keeping the table honest

Node kinds differ per grammar and drift between ast-grep releases. ast-grep
rejects an unknown kind at rule-parse time rather than returning fewer results,
so the table is mechanically checkable:

```bash
python3 scripts/astgrep_extract.py verify
# checked 128 kinds across 14 languages, 0 invalid
```

Run this when a language's numbers look wrong, or after upgrading ast-grep. The
extractor also aborts on a rejected rule rather than reporting a short result —
a silent undercount would show low complexity for branch-heavy code.

## What it does and does not know

Matching is **syntactic**. That is a real step up from grep, and still short of
a resolving analyser.

- **Import edges are written names, not resolved module paths.** `to` is the
  text in the import statement. Two modules that import the same name from
  different roots collapse into one node.
- **Call edges are matched by name.** Same-named methods on different classes are
  conflated, exactly as `references/generic.md` warns for its grep path. Present
  the slice as "static callers found", never as ground truth.
- **Dynamic dispatch, reflection, and DI are invisible.** Say so when the changed
  code uses them.
- **Complexity counts decision points, not paths.** CC is `1 + branches inside
  the function`, branches assigned to the innermost enclosing function. Verified
  against `lizard` on a Python fixture: both report 8 and 1 for the same two
  functions.
- **Anonymous functions** appear as `<anonymous>` when the grammar gives the node
  no name field. Common in JS/TS arrow-heavy code.

## When to prefer the language-specific reference instead

Reach past ast-grep when the PR turns on something only a resolver knows:

- module **paths** matter (monorepo aliasing, barrel files, re-exports) — use
  dependency-cruiser or pydeps from `references/javascript.md` / `python.md`
- the language's own tool already runs in this repo's CI, so its output is free
- you need type-aware call resolution across interfaces — see the DI note in
  `references/java.md`

Use both when they disagree and the disagreement is the story: a name-matched
edge that the resolver does not see is usually dynamic dispatch, and worth a line
in the brief.
