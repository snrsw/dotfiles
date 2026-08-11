# Generic fallback (any language)

Use this when `references/ast-grep.md` cannot cover the language and no
language-specific reference exists (exotic DSLs, generated code, shell), or when
no ast-grep runner is reachable.

**Read `references/ast-grep.md` first.** It handles 14 languages with one binary
and real parsing, including every language this file used to target (Rust, Ruby,
C#, C, C++, PHP, Kotlin, Swift). The grep recipes below are the last resort, not
the first move: they conflate same-named symbols across scopes and cannot tell an
import from a comment mentioning one.

The strategy here: imports via grep → module graph; changed-symbol callers via
grep → call edges; lizard for complexity. Less precise, never blocked.

## Module-level: parse import statements

Identify the import syntax for the language, extract `file -> imported`
lines, normalize with `--format edges`. Examples:

```bash
# Rust
grep -rn --include='*.rs' -E '^\s*use crate::([\w:]+)' src \
  | sed -E 's/^([^:]+):[0-9]+:\s*use crate::([\w:]+).*/\1 -> \2/'

# Ruby
grep -rn --include='*.rb' -E "require(_relative)? ['\"]" . \
  | sed -E "s/^([^:]+):[0-9]+:.*require(_relative)? ['\"]([^'\"]+).*/\1 -> \3/"

# C#
grep -rn --include='*.cs' -E '^using [\w.]+;' src \
  | sed -E 's/^([^:]+):[0-9]+:using ([\w.]+);/\1 -> \2/'
```
Pipe any of these into:
```bash
python scripts/normalize_deps.py - --format edges --granularity module
```
Run once at BASE_SHA (in the worktree) and once at HEAD.

Note in the brief that imports were matched textually, so commented-out and
conditionally-compiled imports are counted as real ones.

## Function-level: caller search for changed symbols only

Do not attempt a full call graph. For each changed function/method name
extracted from the diff:

```bash
grep -rn --include='*.<ext>' -E '\b<symbol>\s*\(' <src_dir> \
  | grep -v '<defining file>'
```
Emit `caller_file -> symbol` edge lines, normalize with `--format edges
--granularity function`, then run `call_graph_slice.py` as usual. Note in
the brief that matching is name-based (same-named symbols in different
scopes are conflated).

Unlike the ast-grep path, the caller here is the **file**, not the enclosing
function, because grep cannot see function boundaries. Say so rather than
letting a reader assume the edge is function-to-function.

## Complexity (lizard supports ~20 languages)

```bash
pipx run lizard <changed files> --csv
```
Columns: NLOC, CCN (cyclomatic complexity), token count, params, function
name, location. Compare the CCN column between base worktree and head.

If lizard is also unavailable, `astgrep_extract.py complexity` covers the
14 languages in `references/ast-grep.md`; hand-counting per Step 6 is the last
resort below that.

## When even grep is impractical

(Binary-heavy repos, generated code, exotic DSLs.) Skip graph analysis and
state clearly in the brief that dependency analysis was not available
for these files; still report the complexity table if lizard parses them.
