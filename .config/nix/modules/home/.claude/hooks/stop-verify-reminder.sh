#!/usr/bin/env bash
# Stop reminder (one-shot): if this session edited files and no test/verify
# command was actually executed, nudge once before finishing.
# Detection parses tool_use entries with jq instead of grepping raw text:
# transcripts embed skill listings and prose that mention test commands,
# so a raw grep is permanently suppressed. Never blocks twice
# (stop_hook_active) and fails open on any parse error.
set -u

command -v jq >/dev/null 2>&1 || exit 0
input=$(cat)

active=$(printf '%s' "$input" | jq -r '.stop_hook_active // false')
[ "$active" = "true" ] && exit 0

transcript=$(printf '%s' "$input" | jq -r '.transcript_path // empty')
[ -f "$transcript" ] || exit 0

# Only relevant when the session actually changed files (real tool_use only).
edited=$(jq -r 'select(.type=="assistant") | .message.content[]? | select(.type=="tool_use") | .name' "$transcript" 2>/dev/null | grep -cE '^(Edit|Write|NotebookEdit)$') || true
[ "${edited:-0}" -gt 0 ] || exit 0

# Verification counts only if a test/verify command was actually run via Bash.
verified=$(jq -r 'select(.type=="assistant") | .message.content[]? | select(.type=="tool_use" and .name=="Bash") | .input.command // empty' "$transcript" 2>/dev/null | grep -cE 'pytest|npm test|pnpm test|yarn test|cargo test|go test|make test|just test|nix flake check|nix-instantiate|bats|ctest') || true
[ "${verified:-0}" -gt 0 ] && exit 0

echo "Files were edited this session but no test or verify run is visible. Verify the change (run tests, or exercise the affected flow) before finishing — or state plainly why verification does not apply." >&2
exit 2
