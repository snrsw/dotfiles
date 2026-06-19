---
name: pr-dependency-review
description: >
  Analyze and visualize how a Pull Request changes code complexity and
  dependencies (module-level, class-level, and function/call-graph level),
  then produce a reviewer-friendly PR comment with Mermaid diagrams and
  risk flags. Use this skill whenever reviewing a PR (especially
  AI-generated PRs), when asked to assess the impact / blast radius of a
  change, when asked whether a PR reduces or increases complexity or
  coupling, when checking for new or removed dependencies or circular
  dependencies, or when running inside a GitHub Actions PR-review job.
  Trigger even if the user just says "review this PR" or "summarize the
  impact of these changes" — dependency and complexity analysis is the
  core of this skill. It selects the visualization type — dependency, sequence,
  state-machine, or data-flow — to match what the change is about.
---

# PR Dependency & Complexity Review

Produce a structured, visual review of how a PR changes dependencies and
complexity. The goal is to lower reviewer load: tell them *where to look*,
*what got riskier*, and *what got better*.

## Core idea

All language-specific tools are normalized into one common edge-list JSON
format. The bundled scripts then do diffing, blast-radius slicing, and
Mermaid generation uniformly:

```
language tool output ──normalize_deps.py──▶ normalized JSON (base & head)
                                               │
                          ┌────────────────────┤
                          ▼                    ▼
                    diff_deps.py        call_graph_slice.py
              (added/removed edges,    (changed-node-centric
               cycles, fan-in flags,    subgraph + Mermaid,
               Mermaid diff graph)      callers highlighted)
```

Normalized format: `{"granularity": "module|class|function", "edges": [{"from": "a", "to": "b"}]}`

The pipeline above is the right picture only when the PR's essence is *structure*
(coupling, cycles, fan-in). When the risk is *timing*, *state*, or *data flow*, a
clean "no new edges" graph is false reassurance — classify what the PR *is* and
pick the diagram type before drawing (Step 2).

## Workflow

### Step 1 — Identify the change set

```bash
BASE_SHA=$(git merge-base origin/${BASE_BRANCH:-main} HEAD)
git diff --name-only $BASE_SHA HEAD          # changed files
git diff $BASE_SHA HEAD --unified=0          # to extract changed function/class names
```

Extract the names of changed functions/classes from hunk headers and added
lines. These names feed `call_graph_slice.py` later.

### Step 2 — Classify the change archetype, then pick the visualization

First decide what the PR *is* — structural, behavioral, state-machine, or
data-flow — and pick the primary diagram type. See
`references/visualization-archetypes.md` for the selection table, rules, and
templates.

This branch decides which of the steps below you run:

- **Structural** (the common case) — run Steps 3–6, then Step 7.
- **Behavioral / state-machine / data-flow** — **skip Steps 3–5** (the dependency
  pipeline: base/head worktree analysis, `diff_deps.py`, blast-radius slice). They
  measure coupling, which is not where this PR's risk lives, and a clean graph is
  false reassurance. Instead drive the diagram from `archetype_signals.py` plus a
  direct read of the **full touched function/module, not just the diff** (the
  script is a diff-only lower bound — see the reference's blind-spot note), run
  Step 6 (complexity) only if it adds signal, and go to Step 7. Lead with the matching diagram and state what it cannot
  certify; demote the dependency graph to one line or drop it if it degenerates.

  **Exception — new or substantial module (any archetype):** "skip Steps 3–5"
  means skip the *cross-module coupling diff* (Steps 3–4), NOT the *function-level
  call graph* (Step 5). When the PR adds a new module/file or a large unit
  (rule of thumb: >10 functions or >200 lines in one file), still run Step 5 on
  its **internal** call graph. For new code that graph is a comprehension map and
  overlays directly onto the complexity/coverage risk — it is not a coupling
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
| Refactoring claim in PR title/description ("reduce coupling", "simplify") | Module + complexity before/after — verify the claim |
| Changes to a file with high fan-in | Always add function-level slice for that file |

### Step 3 — Read the language reference, run analysis on base AND head

Detect languages from changed-file extensions, then read the matching
reference file for exact tool commands and normalization invocations:

- `references/javascript.md` — JS / TypeScript (dependency-cruiser, madge, ts-morph)
- `references/python.md` — Python (pydeps, code2flow, pyreverse, radon)
- `references/go.md` — Go (go list, go-callvis/callgraph, gocyclo)
- `references/java.md` — Java / Kotlin (jdeps, java-callgraph, PMD)
- `references/generic.md` — any other language (tree-sitter / grep-based fallback, lizard for complexity)

Run the analysis **twice**: once at `$BASE_SHA`, once at HEAD. Use
`git stash` / `git worktree add` so the working tree isn't disturbed:

```bash
git worktree add /tmp/base-tree $BASE_SHA
# run tools in /tmp/base-tree → /tmp/deps-base.json (normalized)
# run tools in repo root      → /tmp/deps-head.json (normalized)
git worktree remove /tmp/base-tree --force
```

If a tool is missing, try **one** zero-install runner (`pipx run` / `npx` / `go
run`) — then stop. Do not thrash through a chain of system installers
(`pip install`, `comma`, `go install`): in CI and sandboxes most of these are
absent or need a TTY, and chasing them burns the bulk of the review's time for no
gain. If the runner isn't there, go **straight** to the no-install fallback —
every language reference has one (Python's grep-based import parser, `git grep`,
`references/generic.md`'s tree-sitter/lizard path) — and add a one-line note that
the tool was unavailable. The analysis must never block on tooling.

### Step 4 — Diff the graphs

```bash
python scripts/diff_deps.py /tmp/deps-base.json /tmp/deps-head.json \
  --fan-in-threshold 5 --mermaid > /tmp/deps-diff.json
```

Output includes: added/removed edges, new/resolved cycles, nodes whose
fan-in crossed the threshold, changed files that touch high-fan-in nodes,
and a Mermaid diff graph (added = green, removed = dashed gray,
high-fan-in touched = red).

### Step 5 — Blast radius for changed functions (when granularity includes function level)

```bash
python scripts/call_graph_slice.py /tmp/callgraph-head.json \
  --changed "funcA,ClassB.method,parse_config" --depth 2 --mermaid \
  > /tmp/blast.json
```

This BFS-walks callers (and callees, depth-limited) of every changed
symbol. Changed nodes are red, transitive callers yellow. For each changed
public function, check whether its callers' tests were updated in the PR —
flag if not.

For **new modules**, also check the opposite direction: identify public functions
with intra-module fan-in = 0 that have no tests added in this PR. These are
either dead code or intentional API surface without coverage. Surface them in
the Blast radius section as "uncalled exports — confirm public API intent or
remove."

### Step 6 — Complexity delta

Run the complexity tool from the language reference (lizard works for most
languages) on base and head, restricted to changed files. Report per-function
cyclomatic complexity before → after. Only surface functions whose
complexity changed or that exceed 10.

If no complexity tool is available (none installed and no zero-install runner),
don't skip this step: for the handful of changed functions, compute CC by hand —
`1 + count(if/elif/for/while/and/or/except/case/ternary)` — and label the table
"hand-computed". The changed set is small by definition, so this is cheap.

### Step 7 — Write the PR comment

ALWAYS use this exact structure (omit sections that have nothing to report,
but keep the order):

```markdown
## 🔍 Dependency & Complexity Review

> **Risk: 🔴/🟡/🟢** | Scope: N files, M dirs | Primary concern: <one phrase>

Set Risk to the worst item in Review Priority: 🔴 if any 🔴 item exists, else 🟡
if any 🟡 exists, else 🟢. Scope counts changed files/dirs from Step 1.
Primary concern is the single most important thing a reviewer must check — one
phrase, no sentence needed (e.g., "fan-in spike in auth.service", "data race",
"new cycle in payment module").

### Verdict
One-paragraph plain-language summary: did this PR increase or decrease
coupling/complexity? Where should a human look first? If the PR claims a
refactoring benefit, state whether the data supports it.

### ⚠️ Review priority
- 🔴 High-risk items — always include the **measured value** that triggered the
  flag: fan-in (`auth.service.ts — fan-in = 7, threshold: 5`), new cycle
  (`A → B → A`), complexity spike (`parseConfig — CC 12, threshold: 10`).
  Add file:line and the list of affected callers.
- 🟡 Worth a look
- 🟢 Improvements (resolved cycles, reduced fan-in, complexity drops)

### Primary visualization
The diagram for the Step 2 archetype (structural → diff_deps.py graph;
behavioral → sequence; state → state diagram; data-flow → source→sink). Add one
line on what it shows and one on what it *cannot* certify.

For **structural** archetypes, include a baseline summary line **above** the diagram
so reviewers who weren't around for the original graph can calibrate the change:

> Before: N edges (list key ones). After: M edges. Net: +X −Y.

Then the diff graph (added = green, removed = dashed gray, high-fan-in = red border).
If the before and after states differ enough that a single diff graph obscures the
original shape, use two `subgraph` blocks ("Before" / "After") in the same Mermaid
diagram instead of a diff overlay.

Always include a legend line immediately after the closing triple-backtick:

> Legend: 🟢 added edge / ~~gray~~ removed edge / 🔴 high-fan-in node (fan-in > 5)
> *(for call graphs: 🔴 changed node / 🟡 transitive caller / ░ uncalled export)*

Use the dependency-diff legend for structural archetypes and the call-graph legend
for blast-radius / behavioral diagrams. One legend per diagram, immediately after
the closing fence — never inside the Mermaid block.

### Blast radius (function-level: structural PRs, and new/substantial modules of any archetype)
```mermaid
<slice from call_graph_slice.py>
```
> Legend: 🔴 changed node / 🟡 transitive caller / ░ uncalled export (fan-in = 0, no tests)

Changed symbols and their callers; note untested callers. For a new module, this
is the **internal** call graph (a comprehension map) — surface shared helpers
(high intra-module fan-in) and how deep the high-complexity/under-tested functions
sit from the public entry point. Skip only if it duplicates the dependency graph's node set.

### Complexity
| Function | Before | After |
|---|---|---|
(only changed/notable rows)

### AI-generated-PR checks
See `references/ai-pr-checks.md`. In brief: scope wider than the task (5+
unrelated files / no one-sentence purpose), CI weakened (tests removed or
skipped, coverage or workflow gating), reinvented utilities, phantom imports
(not in the manifest), unnecessary fan-in-1 abstraction, changed public
behavior with no test that fails on the old code, and comprehension debt (no
plain-language explanation of each changed behavior).
```

Post it with `gh pr comment $PR_NUMBER --body-file /tmp/review.md` when
running in CI (GITHUB_ACTIONS env var present); otherwise just present the
markdown to the user.

## Practical rules

- Keep Mermaid graphs under ~30 nodes. If larger, collapse to directory
  level or show only the changed-node neighborhood. A huge graph is worse
  than no graph.
- Every Mermaid diagram in the PR comment must have a legend line immediately
  after its closing fence. Reviewers cannot decode color-coded graphs without one.
- Every 🔴 Review Priority item must include the measured value that triggered the
  flag (fan-in = N, CC = N, cycle path). Never flag without a number.
- One primary diagram per PR; a secondary archetype gets prose unless it earns
  its space (reference thresholds). Replace a degenerate graph — a star or a
  one-edge state diagram — with a sentence; never duplicate a node set.
- "Degenerate" is **per-scope**. Before you drop a dependency graph, name the
  scope you actually judged — module-to-module vs intra-module function-level. A
  new leaf module is degenerate at the module scope (fan-in 0, no cycles) but its
  internal call graph can be rich (shared helpers, deep call chains). A conclusion
  at one scope never licenses skipping the other.
- Match the diagram to the change: a call graph for a race is false reassurance.
  Draw the dimension that holds the risk, not the one the template defaults to.
- Static call graphs miss dynamic dispatch / DI. Say so when relevant —
  present the slice as "static callers found", not ground truth.
- Never fail the whole review because one tool failed; report what worked
  and note what was skipped.
- Token discipline: feed yourself the *diff* JSON and *slice* JSON, not the
  full repo graphs.
- When the PR is huge (>50 files), do module-level only and say explicitly
  that function-level analysis was skipped due to size.
