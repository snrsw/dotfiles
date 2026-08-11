# Python analysis

## Module-level dependencies

pydeps:
```bash
pipx run pydeps <package_dir> --show-deps --no-output --noshow \
  --max-bacon 2 2>/dev/null > /tmp/pydeps.json
python scripts/normalize_deps.py /tmp/pydeps.json --format pydeps \
  --granularity module > /tmp/deps-head.json
```
Use `--exclude` in normalize_deps.py to drop stdlib/site-packages noise
(e.g. `--exclude "node_modules,vendor,site-packages"`), or filter to nodes
whose name starts with the project package.

Fallback without pydeps — parse imports directly (always works, no install):
```bash
grep -rn --include='*.py' -E '^(from|import) ' src \
  | python - <<'EOF'  # build "file -> imported_module" edge lines
import sys, re
for line in sys.stdin:
    path, _, rest = line.partition(':')
    rest = rest.split(':', 1)[1]
    m = re.match(r'\s*from\s+([\w.]+)|\s*import\s+([\w.]+)', rest)
    if m:
        print(f"{path} -> {m.group(1) or m.group(2)}")
EOF
```
Pipe through `normalize_deps.py - --format edges`.

## Function-level call graph

code2flow (also handles JS/Ruby/PHP):
```bash
pipx run code2flow <changed_files_and_their_dir> --output /tmp/cg.dot \
  --quiet --skip-parse-errors
python scripts/normalize_deps.py /tmp/cg.dot --format dot \
  --granularity function > /tmp/callgraph-head.json
```
Point code2flow at the smallest directory covering the changed files plus
likely callers, not the whole repo, to keep runtime down.

PyCG is more precise but slower and stricter about imports; use it only if
code2flow's output looks too noisy.

## Class-level

pyreverse (ships with pylint):
```bash
pipx run --spec pylint pyreverse -o dot -p proj <package_dir> -d /tmp
python scripts/normalize_deps.py /tmp/classes_proj.dot --format dot \
  --granularity class > /tmp/classes-head.json
```

## Complexity

```bash
pipx run radon cc <changed files> -j > /tmp/radon.json   # per-function CC
```
Or `pipx run lizard <files> --csv`.

## Containment detectors (structural problems flat graphs miss)

Flat per-level graphs hide problems that need the module→class→function nesting.
`scripts/containment_detect.py` (stdlib `ast`, no deps) emits three text findings:

```bash
python3 scripts/containment_detect.py --base BASE_SHA --head HEAD_SHA > /tmp/cont.json
```
- `encapsulation_leaks` — a changed file imports a private (`_underscore`) symbol
  from another module (reaches past its public surface).
- `moves` — a top-level symbol kept its name but changed container module/class
  (the refactor-move signal edge-diffs miss). Renamed-while-moved is out of scope.
- `misplaced` — a changed function whose first-party references point mostly at one
  *other* logic module (a move/coupling candidate; shared-type modules and test
  files are excluded to cut noise).
- `phantom_imports` — a newly added import not in stdlib / first-party / the
  manifest (pyproject / requirements). Catches hallucinated packages and
  undeclared deps; verify survivors against the registry.

Add `--mermaid` for a changed-neighborhood containment diagram (drawn only when
something is flagged; skipped when clean, per "a graph must earn its space").

High precision, often silent — silence means the PR is clean on these axes, not
that the tool failed. Confirm each hit; heuristic, not ground truth.

## Notes

- Dynamic dispatch, decorators, and `getattr` calls are invisible to static
  call graphs — caveat the blast radius accordingly.
- For Django/Flask apps, route handlers have no static callers; absence of
  callers does not mean dead code.
