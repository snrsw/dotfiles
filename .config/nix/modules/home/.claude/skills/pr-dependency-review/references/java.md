# Java / Kotlin analysis

## Package/class-level dependencies

jdeps (ships with the JDK; needs compiled classes — run the build first):
```bash
./gradlew classes -q || mvn -q compile
jdeps -verbose:class -dotoutput /tmp/jdeps <build_output_dir>
python scripts/normalize_deps.py /tmp/jdeps/*.dot --format dot \
  --granularity class > /tmp/deps-head.json
```
Use `-verbose:package` + `--granularity module` for the coarse view on big
codebases.

If the build is too slow/broken for CI, fall back to import parsing:
```bash
grep -rn --include='*.java' --include='*.kt' -E '^import ' src \
  | sed -E 's/^([^:]+):[0-9]+:\s*import (static )?([\w.]+).*/\1 -> \3/' \
  | python scripts/normalize_deps.py - --format edges --granularity class
```

## Function-level call graph

java-callgraph2 or javacg (static, operates on jars/classes):
```bash
# after build
java -jar javacg-static.jar <app.jar> > /tmp/cg.txt
# output lines look like: M:com.a.Foo:bar (M)com.b.Baz:qux
sed -E 's/^M:([^ ]+) \(.\)(.+)$/\1 -> \2/' /tmp/cg.txt \
  | python scripts/normalize_deps.py - --format edges \
    --granularity function > /tmp/callgraph-head.json
```
If no callgraph jar is obtainable in CI, use the grep fallback per changed
method name (same pattern as in javascript.md) — substring search for
`.methodName(` across the source tree.

## Complexity

PMD:
```bash
pmd check -d <changed files> -R category/java/design.xml/CyclomaticComplexity \
  -f json
```
Or `pipx run lizard -l java <files> --csv` (also supports kotlin).

## Notes

- Spring/DI: bean wiring means constructors and interfaces have no static
  call edges; flag interface changes as "callers undetectable statically,
  search for implementations instead" (`grep -rn "implements X"`).
- Kotlin coroutines and extension functions confuse most static tools —
  prefer the lizard + grep combination for Kotlin-heavy diffs.
