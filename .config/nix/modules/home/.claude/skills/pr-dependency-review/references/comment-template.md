# PR comment template

Read this at write time (Step 7). ALWAYS use this exact structure (omit sections
that have nothing to report, but keep the order):

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
See this skill's `references/ai-pr-checks.md`. In brief: scope wider than the task (5+
unrelated files / no one-sentence purpose), CI weakened (tests removed or
skipped, coverage or workflow gating), reinvented utilities, phantom imports
(not in the manifest), unnecessary fan-in-1 abstraction, changed public
behavior with no test that fails on the old code, and comprehension debt (no
plain-language explanation of each changed behavior).
```
