#!/usr/bin/env bash
# Stop reminder (one-shot): if this session edited files and no test/verify
# activity is visible in the transcript, nudge once before finishing.
# Never blocks twice: stop_hook_active guards against loops.
set -u

command -v jq >/dev/null 2>&1 || exit 0
input=$(cat)

active=$(printf '%s' "$input" | jq -r '.stop_hook_active // false')
[ "$active" = "true" ] && exit 0

transcript=$(printf '%s' "$input" | jq -r '.transcript_path // empty')
[ -f "$transcript" ] || exit 0

# Only relevant when the session actually changed files.
grep -qE '"name": ?"(Edit|Write|NotebookEdit)"' "$transcript" 2>/dev/null || exit 0

# Heuristic: any visible test/verify activity counts as verification.
if grep -qE 'pytest|npm test|pnpm test|yarn test|cargo test|go test|make test|just test|/verify|nix flake check|nix-instantiate' "$transcript" 2>/dev/null; then
  exit 0
fi

echo "Files were edited this session but no test or verify run is visible. Verify the change (run tests, or exercise the affected flow) before finishing — or state plainly why verification does not apply." >&2
exit 2
