# JavaScript / TypeScript analysis

## Module-level dependencies

dependency-cruiser (preferred — richer output):
```bash
npx --yes dependency-cruiser src --no-config --output-type json > /tmp/dc.json
python scripts/normalize_deps.py /tmp/dc.json --format depcruise \
  --granularity module > /tmp/deps-head.json
```
If the repo has a `.dependency-cruiser.js`, drop `--no-config`.

madge (lighter, also detects cycles natively):
```bash
npx --yes madge --json src > /tmp/madge.json
python scripts/normalize_deps.py /tmp/madge.json --format madge \
  --granularity module > /tmp/deps-head.json
```

For monorepos, run per-package or point at the workspace root with
`--exclude` covering other packages' node_modules.

## Function/class-level call graph

No single dominant CLI tool. Two practical options, in order of preference:

1. **TypeScript compiler API one-shot script** (works for TS and JS with
   allowJs). Write a small script with ts-morph that, for each changed
   file, finds call expressions and resolves their declarations. Restrict
   to the changed files plus their importers (from the module graph) to
   keep it fast. Emit `from -> to` lines and pipe through:
   ```bash
   node /tmp/callgraph.mjs | python scripts/normalize_deps.py - \
     --format edges --granularity function > /tmp/callgraph-head.json
   ```
   ts-morph sketch: `Project.addSourceFilesAtPaths`, walk
   `SyntaxKind.CallExpression`, use `.getSymbol()?.getDeclarations()` to get
   the target file + name; name nodes as `relpath::funcName`.

2. **Grep-based fallback**: for each changed exported symbol, find callers:
   ```bash
   grep -rn --include='*.ts' --include='*.tsx' -E '\bmySymbol\s*\(' src \
     | grep -v 'path/to/defining/file'
   ```
   Build `caller_file::<line> -> symbol` edge lines and normalize with
   `--format edges`. Less precise (no scope resolution) but always works.

## Complexity

```bash
npx --yes eslint --no-eslintrc --rule '{"complexity": ["warn", 0]}' \
  --format json <changed files>   # complexity per function in messages
```
Or use lizard (language-agnostic): `pipx run lizard -l javascript <files> --csv`.

## Notes

- Type-only imports (`import type`) in depcruise output have
  `dependencyTypes` including `type-only`; they are compile-time only —
  deprioritize them in the review.
- Barrel files (index.ts re-exports) inflate fan-in; mention when a
  high-fan-in node is a barrel file.
