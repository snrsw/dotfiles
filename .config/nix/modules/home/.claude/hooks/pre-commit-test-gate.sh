#!/usr/bin/env bash
# PreToolUse gate on Bash: block `git commit` when the project's tests fail.
# Fail-open by design: unknown project shape, missing runner, or missing jq
# means allow — the gate must never brick unrelated commits.
set -u

command -v jq >/dev/null 2>&1 || exit 0
input=$(cat)
cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // empty')

# Only unquoted tokens count: text inside -m "..." or echo '...' must
# neither trigger the gate nor bypass it via --no-verify in a message.
cmd_unquoted=$(printf '%s' "$cmd" | sed -E "s/'[^']*'//g; s/\"[^\"]*\"//g")

case "$cmd_unquoted" in
  *"git commit"*) ;;
  *) exit 0 ;;
esac
# Escape hatch (same as native git hooks), honored only on a line that invokes git.
if printf '%s\n' "$cmd_unquoted" | grep 'git' | grep -q -- '--no-verify'; then
  exit 0
fi

cwd=$(printf '%s' "$input" | jq -r '.cwd // empty')
[ -n "$cwd" ] && cd "$cwd" 2>/dev/null

detect_test_command() {
  if [ -f justfile ] && command -v just >/dev/null 2>&1 \
      && just --summary 2>/dev/null | tr ' ' '\n' | grep -qx test; then
    echo "just test"
  elif [ -f Makefile ] && command -v make >/dev/null 2>&1 && grep -qE '^test:' Makefile; then
    echo "make test"
  elif [ -f package.json ] && jq -e '.scripts.test' package.json >/dev/null 2>&1 \
      && ! jq -r '.scripts.test' package.json | grep -q 'no test specified'; then
    if [ -f pnpm-lock.yaml ] && command -v pnpm >/dev/null 2>&1; then echo "pnpm test"
    elif [ -f yarn.lock ] && command -v yarn >/dev/null 2>&1; then echo "yarn test"
    elif command -v npm >/dev/null 2>&1; then echo "npm test --silent"
    fi
  elif [ -f Cargo.toml ] && command -v cargo >/dev/null 2>&1; then
    echo "cargo test --quiet"
  elif [ -f go.mod ] && command -v go >/dev/null 2>&1; then
    echo "go test ./..."
  elif [ -f uv.lock ] && command -v uv >/dev/null 2>&1 && { [ -d tests ] || [ -f pytest.ini ]; }; then
    echo "uv run pytest -q"
  elif command -v pytest >/dev/null 2>&1 && { [ -d tests ] || [ -f pytest.ini ]; }; then
    echo "pytest -q"
  fi
}

test_cmd=$(detect_test_command)
[ -z "$test_cmd" ] && exit 0

out=$(sh -c "$test_cmd" 2>&1)
if [ $? -ne 0 ]; then
  {
    echo "Commit blocked: '$test_cmd' fails in $(pwd). Fix the tests first (or commit with --no-verify if this is intentional)."
    echo "Last lines of output:"
    printf '%s\n' "$out" | tail -20
  } >&2
  exit 2
fi
exit 0
