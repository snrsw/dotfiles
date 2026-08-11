# Change-map brief template

Read this at write time (Step 7). ALWAYS use this exact structure.

The brief is a **resolution ladder**: each section answers the same question —
what changed — one zoom level deeper than the last. A reader may stop after any
rung and still hold a correct, coarser picture; that is the design, not a
failure mode. Render a rung only when it is non-degenerate **at its own scope**
(SKILL.md's per-scope rule); a degenerate rung becomes its one-sentence
verdictless summary, never an empty diagram.

```markdown
## 🗺️ Change map

> Scope: N files, M dirs, K commits | <base-sha>..<head-sha>

Scope counts come from Step 1. No internal jargon in this line — "archetype"
and granularity names stay in the skill, not in the brief.

### What changed
Lead with the single-sentence answer; a reader who stops here must still have
the right idea. If the PR contains several logical units, one bullet per unit —
the commit list from Step 1 is the author's own chunking and the first guess at
the units. If the PR description makes a claim ("reduces coupling", "fixes the
retry race"), state the claim and then what the measurements show, keeping the
two apart.

### Where it sits — L0, the codebase around the change
The collapsed module graph from `diff_deps.py --mermaid`: changed edges plus
the unchanged edges touching them (drawn plain), everything else absent or
collapsed to directory level. One line above the diagram calibrates:

> Before: N edges (list key ones). After: M edges. Net: +X −Y.

Every fan-in number carries its repo context from `fan_in_stats`:
`auth — fan-in 3 → 7 (repo median 2, max 9)`. That places the number without
grading it.

> Legend: 🟢 added edge / ~~gray~~ removed edge / thin plain arrow = unchanged
> edge (context) / 🔴 fan-in above threshold (highlight, not a pass/fail line)

Module-scope facts land here as bullets, largest movement first, each with its
number: new/resolved cycles (`A → B → A`), fan-in moves, moved symbols and
phantom imports from `containment_detect.py`.

Degenerate at this scope (all changes inside one module, no import edge in or
out changed) → one sentence saying exactly that, no diagram.

### How the boundary changes — L1, interfaces and hand-offs
The `interface_diff.py` result as a table, each row with `file:line`:

| Change | Function | Signature |
|---|---|---|
| changed | `svc.py:1 fetch` | `def fetch(url)` → `def fetch(url, retries=3)` |
| added | `svc.py:7 _helper` | `def _helper(x)` |

Rows ordered: changed first, then added, then removed — a moved promise matters
more than a new one.

State the test-correspondence **fact** (not a flag): "of N changed public
functions, M have test changes in this PR" — computed from the changed-file
list, which includes test files.

**If the hand-off itself changed** — the data a call carries, the call order,
sync → async, a new intermediary — draw the before/after sequence diagram here,
whatever the PR's archetype. A signature that gains a parameter moves data
across the boundary; that is exactly what a sequence diagram shows and a
dependency edge cannot. The data-flow archetype's source→sink diagram also
lives at this rung.

Degenerate at this scope → the single most load-reducing sentence this brief
can contain: **"Public surface unchanged — signatures identical base→head
(verified)."** It licenses the reader to skip everything outside the component.
Always state it when true; never leave the rung silently absent.

### Inside the component — L2, internals
The call-graph slice from `call_graph_slice.py` (for new modules: the internal
call graph, with shared helpers and uncalled exports). The state-machine
archetype's diagram lives at this rung.

> Legend: 🔴 changed node / 🟡 transitive caller / ░ uncalled export (intra-module fan-in = 0)

Then the complexity table, **ordered by |after − before| descending** — the
reader reads top-down and the biggest movement comes first:

| Function | Before | After |
|---|---|---|
(only changed/notable rows; label the table "hand-computed" when no tool ran)

### What this map does not show
One bullet per gap, so the reader knows the edges of the picture:
- tools that were unavailable and the fallback used instead
- dynamic dispatch / DI / reflection the static graph cannot see
- files skipped (binary, generated, >50-file size cap)
- what the chosen diagram type cannot certify (e.g. "the sequence diagram
  shows the interleaving window; it cannot prove the write is atomic")
- signature comparison limits when relevant (renames read as removed+added;
  Kotlin/Swift return types are cut at the colon)
```

## Prose rules inside this template

- **Describe, don't grade.** Every line reports a measurement or a plain-language
  description. No risk rating, no verdict, no "should", no severity adjectives.
  If the reader should worry about something, the number says so on its own.
- **Biggest first, at every rung.** Tables and bullet lists are ordered by the
  size of the measured change, sign-blind. The ladder orders the sections; the
  magnitude orders the rows.
- **Every number has an anchor.** A fan-in carries its repo median and max; a
  table row carries `file:line`. A number without a place to jump to leaves the
  reader searching.
- **Lead with the conclusion** in "What changed" — first sentence answers "what
  does this PR do".
- **One term per node.** The same string in the prose, the Mermaid label, and
  the tables, at every rung — the reader tracks one name down the whole ladder.
- **Table columns hold one kind of content.** `Before` and `After` hold
  measurements only.
- **Separate fact from inference.** Counts and signature diffs are unhedged;
  anything about cause or consequence is marked as inference.
- **Author's claim and measured result stay apart.** Never merge "the PR says it
  simplifies X" and "CC went 14 → 9" into one unattributed sentence.
