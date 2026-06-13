# Generic fallback (any language)

Use this when no language-specific reference exists (Ruby, PHP, Rust, C#,
C/C++, Swift, ...) or when the language-specific tool failed to install.
The strategy: imports via grep → module graph; changed-symbol callers via
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

## Function-level: caller search for changed symbols only

Do not attempt a full call graph. For each changed function/method name
extracted from the diff:

```bash
grep -rn --include='*.<ext>' -E '\b<symbol>\s*\(' <src_dir> \
  | grep -v '<defining file>'
```
Emit `caller_file -> symbol` edge lines, normalize with `--format edges
--granularity function`, then run `call_graph_slice.py` as usual. Note in
the PR comment that matching is name-based (same-named symbols in different
scopes are conflated).

## Complexity (lizard supports ~20 languages)

```bash
pipx run lizard <changed files> --csv
```
Columns: NLOC, CCN (cyclomatic complexity), token count, params, function
name, location. Compare the CCN column between base worktree and head.

## When even grep is impractical

(Binary-heavy repos, generated code, exotic DSLs.) Skip graph analysis and
state clearly in the PR comment that dependency analysis was not available
for these files; still report the complexity table if lizard parses them.
