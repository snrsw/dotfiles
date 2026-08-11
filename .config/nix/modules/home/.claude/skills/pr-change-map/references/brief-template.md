# Change-map brief template

Read this at write time (Step 7). ALWAYS use this exact structure (omit sections
that have nothing to report, but keep the order):

```markdown
## 🗺️ Change map

> Scope: N files, M dirs | Archetype: structural | Analysed at: <base-sha>..<head-sha>

Scope counts changed files/dirs from Step 1. Archetype is the Step 2
classification, one of: structural / behavioral / state-machine / data-flow.

### What changed
Two to four sentences in plain language: what this PR does, and where it does
it. Lead with the single-sentence answer. If the PR description makes a claim
("reduces coupling", "fixes the retry race"), state the claim and then state
what the measurements show, keeping the two apart.

### Primary diagram
The diagram for the Step 2 archetype (structural → diff_deps.py graph;
behavioral → sequence; state → state diagram; data-flow → source→sink). Add one
line on what it shows and one on what it cannot show.

For **structural** archetypes, include a baseline summary line **above** the diagram
so a reader who has never seen this part of the codebase can calibrate:

> Before: N edges (list key ones). After: M edges. Net: +X −Y.

Then the diff graph (added = green, removed = dashed gray, high-fan-in = red border).
If the before and after states differ enough that a single diff graph obscures the
original shape, use two `subgraph` blocks ("Before" / "After") in the same Mermaid
diagram instead of a diff overlay.

Always include a legend line immediately after the closing triple-backtick:

> Legend: 🟢 added edge / ~~gray~~ removed edge / 🔴 fan-in above 5 (highlight, not a threshold)
> *(for call graphs: 🔴 changed node / 🟡 transitive caller / ░ uncalled export)*

Use the dependency-diff legend for structural archetypes and the call-graph legend
for blast-radius / behavioral diagrams. One legend per diagram, immediately after
the closing fence — never inside the Mermaid block.

### What it touches (function-level: structural PRs, and new/substantial modules of any archetype)
```mermaid
<slice from call_graph_slice.py>
```
> Legend: 🔴 changed node / 🟡 transitive caller / ░ uncalled export (intra-module fan-in = 0)

Changed symbols and their callers — what comes into scope if you touch this code.
For a new module, this is the **internal** call graph: name the shared helpers
(high intra-module fan-in) and say how deep the complex functions sit from the
public entry point. Skip only if it duplicates the dependency graph's node set.

### Notable structure
Facts the graphs surface that the diagram alone does not carry, one bullet each,
each with its number: cycles added or resolved (`A → B → A`), fan-in moves
(`auth.service 3 → 7`), moved or renamed symbols, imports added that are not in
the manifest. Omit the section entirely when there is nothing measured to say.

### Complexity
| Function | Before | After |
|---|---|---|
(only changed/notable rows; label the table "hand-computed" when no tool ran)

### What this map does not show
One bullet per gap, so the reader knows the edges of the picture:
- tools that were unavailable and the fallback used instead
- dynamic dispatch / DI / reflection the static graph cannot see
- files skipped (binary, generated, >50-file size cap)
- what the chosen diagram type cannot certify (e.g. "a sequence diagram shows
  the interleaving window; it cannot prove the write is atomic")
```

## Prose rules inside this template

- **Describe, don't grade.** Every line reports a measurement or a plain-language
  description. No risk rating, no verdict, no "should", no severity adjectives.
  If the reader should worry about something, the number says so on its own.
- **Lead with the conclusion** in "What changed" — first sentence answers "what
  does this PR do".
- **One term per node.** The same string in the prose, the Mermaid label, and the
  Complexity table row.
- **Table columns hold one kind of content.** `Before` and `After` hold
  measurements only.
- **Separate fact from inference.** Counts are unhedged; anything about cause or
  consequence is marked as inference.
- **Author's claim and measured result stay apart.** Never merge "the PR says it
  simplifies X" and "CC went 14 → 9" into one unattributed sentence.
