---
name: pr-change-map
description: >
  Map what a Pull Request changes and how it connects — dependency edges,
  call-graph blast radius, and complexity deltas, rendered as diagrams — so a
  reader can understand the change. Use for "what does this PR do", "explain
  this PR", "map this change", "what does this touch", or when orienting
  yourself in someone else's PR before working on it. Analysis only: no
  verdict, no risk rating, no PR comment. Use `pr-dependency-review` when the
  output should be a review.
---

# PR Change Map

Build a factual map of a PR: what changed, what it connects to, what got more
complex. The reader wants to **understand** the change, not be told whether to
approve it.

**The line this skill does not cross:** report measurements and what they mean,
never a judgement about them. "`auth.service` fan-in went 3 → 7" is a map.
"`auth.service` fan-in is too high, 🔴 fix before merge" is a review — that is
`pr-dependency-review`'s job, not this skill's. No risk rating, no verdict, no
review-priority list, no `gh pr comment`.

## Core idea

Every analysis tool is normalized into one common edge-list JSON format. The
bundled scripts then do diffing, blast-radius slicing, and Mermaid generation
uniformly, whatever produced the edges:

```
source ──astgrep_extract.py──┐   (default: tree-sitter, 14 languages, one binary)
                             ├──▶ normalized JSON (base & head)
language tool ──normalize_deps.py┘  (precision upgrade, when a resolver matters)
                                               │
                          ┌────────────────────┤
                          ▼                    ▼
                    diff_deps.py        call_graph_slice.py
              (added/removed edges,    (changed-node-centric
               cycles, fan-in counts,   subgraph + Mermaid,
               Mermaid diff graph)      callers highlighted)
```

Normalized format: `{"granularity": "module|class|function", "edges": [{"from": "a", "to": "b"}]}`

The pipeline above is the right picture only when the PR's essence is *structure*
(coupling, cycles, fan-in). When the change is about *timing*, *state*, or *data
flow*, a clean "no new edges" graph maps the wrong dimension — classify what the
PR *is* and pick the diagram type before drawing (Step 2).

## Workflow

### Step 1 — Identify the change set

```bash
BASE_SHA=$(git merge-base origin/${BASE_BRANCH:-main} HEAD)
git diff --name-only $BASE_SHA HEAD          # changed files
git diff $BASE_SHA HEAD --unified=0          # to extract changed function/class names
git log --oneline $BASE_SHA..HEAD            # the author's own chunking
```

Extract the names of changed functions/classes from hunk headers and added
lines. These names feed `call_graph_slice.py` later.

The commit list is free structure: when the PR contains several logical units,
the commits are the author's own decomposition of them, and the brief's "What
changed" section presents one bullet per unit instead of forcing the reader to
un-mix an aggregate. Squashed single-commit PRs get no such help — then the
units come from reading the diff.

For a PR you did not write, also read its title and description — the map should
say what the author claims the change does, separately from what the graphs show.

### Step 2 — Classify the change archetype, then pick the visualization

First decide what the PR *is* — structural, behavioral, state-machine, or
data-flow — and pick the primary diagram type. See
`references/visualization-archetypes.md` for the selection table, rules, and
templates.

This branch decides which of the steps below you run:

- **Structural** (the common case) — run Steps 3–6, then Step 7.
- **Behavioral / state-machine / data-flow** — **skip Steps 3–5** (the dependency
  pipeline: base/head worktree analysis, `diff_deps.py`, blast-radius slice). They
  measure coupling, which is not the dimension this PR changes, and mapping it
  draws attention to the wrong place. Instead drive the diagram from
  `archetype_signals.py` plus a direct read of the **full touched
  function/module, not just the diff** (the script is a diff-only lower bound —
  see the reference's blind-spot note), run Step 6 (complexity) only if it adds
  signal, and go to Step 7. Lead with the matching diagram and state what it
  cannot show; demote the dependency graph to one line or drop it if it
  degenerates.

  **Exception — new or substantial module (any archetype):** "skip Steps 3–5"
  means skip the *cross-module coupling diff* (Steps 3–4), NOT the *function-level
  call graph* (Step 5). When the PR adds a new module/file or a large unit
  (rule of thumb: >10 functions or >200 lines in one file), still run Step 5 on
  its **internal** call graph. For new code that graph is the comprehension map —
  the single most useful artifact this skill produces — and it is not a coupling
  measurement, so the "skip" rationale does not apply. Degeneracy is **per-scope**:
  a new leaf module is degenerate at the module-to-module scope (fan-in 0, no
  cycles) yet rich at the intra-module function scope. Judge each scope on its own
  and never carry "no graph worth drawing" from one scope to the other.

Then choose analysis granularity. The structural path always reaches this table;
non-structural archetypes use only the "new/substantial module" row (per the
exception above):

| Change shape | Granularity |
|---|---|
| Many files across packages/dirs (>~10 files or >3 dirs) | Module-level only |
| Few files, localized change | Module + function-level (call graph slice) |
| New or substantial module/file (new code, not a modification) | Function-level **internal** call graph — regardless of archetype |
| Refactoring claim in PR title/description ("reduce coupling", "simplify") | Module + complexity before/after — show whether the numbers moved |
| Changes to a file with high fan-in | Always add function-level slice for that file |

### Step 3 — Read the language reference, run analysis on base AND head

Detect languages from changed-file extensions, then read the matching
reference file for exact tool commands and normalization invocations.

**Start with `references/ast-grep.md`.** ast-grep ships tree-sitter grammars in
one static binary, so a single zero-install runner gives real AST analysis for 14
languages — imports, call edges, and cyclomatic complexity — with no
per-language tool to install. `scripts/astgrep_extract.py` emits the normalized
JSON directly. This is the default path; the references below are the precision
upgrade, not the starting point.

Reach for a language-specific reference when the PR turns on something only a
resolver knows (module path aliasing, barrel files, type-aware dispatch), or when
that tool already runs in this repo's CI:

- `references/javascript.md` — JS / TypeScript (dependency-cruiser, madge, ts-morph)
- `references/python.md` — Python (pydeps, code2flow, pyreverse, radon)
- `references/go.md` — Go (go list, go-callvis/callgraph, gocyclo)
- `references/java.md` — Java / Kotlin (jdeps, java-callgraph, PMD)
- `references/generic.md` — grep-based last resort, for languages ast-grep does
  not cover or when no runner is reachable

Run the analysis **twice**: once at `$BASE_SHA`, once at HEAD. Use
`git stash` / `git worktree add` so the working tree isn't disturbed:

```bash
git worktree add /tmp/base-tree $BASE_SHA
# run tools in /tmp/base-tree → /tmp/deps-base.json (normalized)
# run tools in repo root      → /tmp/deps-head.json (normalized)
git worktree remove /tmp/base-tree --force
```

If a tool is missing, try **one** zero-install runner (`nix run` / `npx` /
`pipx run` / `go run`) — then stop. Do not thrash through a chain of system
installers (`pip install`, `comma`, `go install`): in CI and sandboxes most of
these are absent or need a TTY, and chasing them burns the bulk of the time for
no gain. For the ast-grep path that runner is `ASTGREP_BIN`; if it isn't there,
go **straight** to `references/generic.md`'s grep path — and record the tool as
unavailable in the brief's "What this map does not show" section. The map must
never block on tooling.

### Step 4 — Diff the graphs

```bash
python scripts/diff_deps.py /tmp/deps-base.json /tmp/deps-head.json \
  --fan-in-threshold 5 --mermaid > /tmp/deps-diff.json
```

Output includes: added/removed edges, new/resolved cycles, nodes whose
fan-in crossed the threshold, changed files that touch high-fan-in nodes,
`fan_in_stats` (repo median and max), and a Mermaid diff graph (added = green,
removed = dashed gray, high-fan-in touched = red, plus **plain context edges**:
unchanged edges touching a changed node, so the diff sits inside its existing
structure instead of floating in space — this graph is the brief's L0 rung).

The threshold is a **highlighting** parameter, not a pass/fail line. Report the
count it surfaced with its calibration — `fan-in 3 → 7 (repo median 2, max 9)`
from `fan_in_stats` — not a judgement about the count. The calibration is what
lets a reader who does not know the repo place the number; that reader is
exactly who the map is for.

### Step 5 — Boundary delta and blast radius (when granularity includes function level)

First the **boundary**: what did the component's promises to its neighbours do?

```bash
python scripts/astgrep_extract.py defs --lang <lang> --repo /tmp/base-tree /tmp/base-tree > /tmp/defs-base.json
python scripts/astgrep_extract.py defs --lang <lang> --repo . . > /tmp/defs-head.json
python scripts/interface_diff.py /tmp/defs-base.json /tmp/defs-head.json > /tmp/iface.json
```

Added, removed, and signature-changed functions, with before/after signature
text. This is the brief's L1 rung. Two rules attach to it:

- **The empty result is a finding, not a non-result.** `surface_unchanged:
  true` becomes the sentence "public surface unchanged (verified)" — the
  single most load-reducing fact a brief can carry, because it licenses the
  reader to skip everything outside the component.
- **A changed hand-off gets a sequence diagram, whatever the archetype.** When
  a signature gains or loses a parameter that carries data across the
  boundary, or the call order / sync-async shape changes, draw the
  before/after sequence at L1 (template in
  `references/visualization-archetypes.md`). A dependency edge cannot show
  what a call now carries; a sequence diagram can.

Also state the test-correspondence **fact**: of the changed public functions,
how many have test changes in this PR (the Step 1 file list includes test
files). A fact, not a flag — the reader decides what to do with it.

Then the **blast radius**:

```bash
python scripts/call_graph_slice.py /tmp/callgraph-head.json \
  --changed "funcA,ClassB.method,parse_config" --depth 2 --mermaid \
  > /tmp/blast.json
```

This BFS-walks callers (and callees, depth-limited) of every changed
symbol. Changed nodes are red, transitive callers yellow. This answers the
reader's real question: *if I touch this, what else is in scope?*

For **new modules**, also map the opposite direction: list public functions with
intra-module fan-in = 0. `astgrep_extract.py defs` gives the full definition
inventory; subtract the `to` side of the call edges to get the uncalled set.
Report them as "uncalled exports" and say plainly which ones have tests in this
PR and which do not — both are facts the reader needs to place the module's
public surface.

### Step 6 — Complexity delta

```bash
python3 scripts/astgrep_extract.py complexity --lang <lang> <changed files>
```

Run it in the base worktree and at HEAD, then pair functions by name to get
before → after. Only surface functions whose complexity changed or that sit
above 10 — that keeps the table readable; the number is a reporting filter, not
a threshold the PR passes or fails.

`lizard` from the language reference is the alternative and agrees with the
above (both report CC 8 and 1 for the same two functions on the Python fixture
used to check it). Use whichever is already reachable.

If neither is available, don't skip this step: for the handful of changed
functions, compute CC by hand — `1 + count(if/elif/for/while/and/or/except/
case/ternary)` — and label the table "hand-computed". The changed set is small
by definition, so this is cheap.

### Step 7 — Write the brief

Read `references/brief-template.md` and use its exact structure: a **resolution
ladder** that raises the zoom level section by section —

- **L0 — where it sits**: the collapsed module graph with context edges; the
  change placed in the codebase around it.
- **L1 — how the boundary changes**: the interface delta, the hand-off
  sequence diagram when the protocol moved, the test-correspondence fact.
- **L2 — inside the component**: the call-graph slice and the complexity
  table.

A reader may stop after any rung and still hold a correct, coarser picture —
that is conclusion-first applied to diagrams. Each rung is judged for
degeneracy **at its own scope** (the per-scope rule below): a degenerate rung
becomes its one-sentence summary ("all changes inside module X" / "public
surface unchanged (verified)"), never an empty diagram and never silently
absent. The archetype from Step 2 decides which rung carries its special
diagram — data-flow at L1, state-machine at L2 — not whether the ladder is
used.

Present the markdown to the user in chat. **Do not post it to the PR** — this
skill produces a map for a reader, not a comment for an author. If the user
explicitly asks to post it, say that `pr-dependency-review` is the skill that
writes PR comments, and post only if they confirm they want the map itself
posted.

## Practical rules

- Keep Mermaid graphs under ~30 nodes. If larger, collapse to directory
  level or show only the changed-node neighborhood. A huge graph is worse
  than no graph.
- Every Mermaid diagram must have a legend line immediately after its closing
  fence. Readers cannot decode color-coded graphs without one.
- Every claim about size or shape carries its measured number (fan-in = N,
  CC = N, cycle path, edge counts). A map without numbers is an impression.
- At most one diagram per ladder rung; a secondary archetype gets prose unless
  it earns its space (reference thresholds). Replace a degenerate graph — a
  star or a one-edge state diagram — with a sentence; never duplicate a node
  set across rungs (the L2 slice must add nodes or edges the L0 graph did not
  show, or it collapses into a sentence).
- Order by magnitude everywhere: table rows and finding bullets sorted by
  |after − before|, sign-blind. The ladder orders the sections; the size of
  the movement orders the rows. Every number carries its anchor — `file:line`
  for a function, repo median/max for a fan-in.
- "Degenerate" is **per-scope**. Before you drop a dependency graph, name the
  scope you actually judged — module-to-module vs intra-module function-level. A
  new leaf module is degenerate at the module scope (fan-in 0, no cycles) but its
  internal call graph can be rich (shared helpers, deep call chains). A conclusion
  at one scope never licenses skipping the other.
- Match the diagram to the change: a call graph for a race maps the wrong
  dimension. Draw where the change actually lives, not the one the pipeline
  defaults to.
- Static call graphs miss dynamic dispatch / DI. Say so when relevant —
  present the slice as "static callers found", not ground truth.
- Never abandon the whole map because one tool failed; report what worked
  and list what was skipped.
- Token discipline: feed yourself the *diff* JSON and *slice* JSON, not the
  full repo graphs.
- When the PR is huge (>50 files), do module-level only and say explicitly
  that function-level analysis was skipped due to size.

## Response style

The `response-style` rule applies to every output. The brief template fixes the
structure; these govern the prose inside it.

- **Lead with the conclusion.** The first line of "What changed" says what the PR
  does in one sentence. A reader who stops there must still have the right idea.
- **One term per node, everywhere.** The name in the prose, the node label in the
  Mermaid diagram, and the row in the Complexity table must be the same string.
  A module called `auth.service` in one place and `AuthService` in another reads
  as two modules.
- **Table columns hold one kind of content.** `Before` and `After` hold
  measurements only — never a measurement in one row and a comment in the next.
- **Measured values are fact; the rest is inference.** A fan-in count or CC number
  is unhedged. A claim about *why* something changed, or what it implies, is
  marked as inference — the same discipline as "static callers found, not ground
  truth".
- **Describe, don't grade.** Write "fan-in 3 → 7, all seven callers are in
  `checkout/`", not "worryingly high fan-in". Adjectives of severity belong to
  `pr-dependency-review`.
- **The table must agree with the prose.** Readers skim the Complexity table
  before reading anything else, and trust it over the text.
