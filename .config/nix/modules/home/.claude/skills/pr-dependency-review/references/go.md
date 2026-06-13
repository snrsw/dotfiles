# Go analysis

## Package-level dependencies (within the module)

```bash
go list -deps -json ./... > /tmp/golist.json
python scripts/normalize_deps.py /tmp/golist.json --format golist \
  --granularity module --strip-prefix "$(go list -m)/" > /tmp/deps-head.json
```
`--strip-prefix` with the module path keeps node names short; external
modules keep their full path so they're visually distinct. Standard library
packages are dropped automatically by the golist parser.

External module graph (only if go.mod changed):
```bash
go mod graph | python scripts/normalize_deps.py - --format gomod \
  --granularity module > /tmp/modgraph-head.json
```

## Function-level call graph

callgraph from x/tools (static or cha algorithm; cha is faster):
```bash
go install golang.org/x/tools/cmd/callgraph@latest
callgraph -algo cha -format 'digraph' ./... 2>/dev/null > /tmp/cg.txt
python scripts/normalize_deps.py /tmp/cg.txt --format edges \
  --granularity function > /tmp/callgraph-head.json
```
The digraph format is "caller callee callee..." per line — if normalize
output looks wrong, use `-format '{{.Caller}} -> {{.Callee}}'` instead and
`--format edges`.

The full callgraph of a large module is huge. Filter before normalizing:
```bash
grep -F "<changed package path>" /tmp/cg.txt > /tmp/cg-filtered.txt
```

go-callvis is the visual alternative but is interactive-oriented; prefer
callgraph for CI.

## Complexity

```bash
go install github.com/fzipp/gocyclo/cmd/gocyclo@latest
gocyclo -over 0 <changed files>      # per-function complexity
```

## Notes

- Interface method calls: `cha` over-approximates (lists all
  implementations as possible callees). Mention this when an interface
  method is in the changed set — the real blast radius may be smaller.
- Generated code (`*_gen.go`, `*.pb.go`) inflates graphs; exclude it via
  normalize_deps.py `--exclude ".pb.go,_gen.go"`.
