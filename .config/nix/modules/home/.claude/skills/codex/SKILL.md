---
name: codex
description: Use OpenAI Codex CLI to run AI-powered coding tasks in the terminal. Use when the user wants to run codex, delegate a task to codex, use codex exec for non-interactive runs, review code with codex, or apply codex-generated diffs.
---

# Codex CLI

## Overview

Codex CLI is an AI coding agent that runs in the terminal. It can read, write, and execute code in a sandboxed environment.

## Common Commands

### Interactive session
```sh
codex [PROMPT]
```
Starts an interactive TUI session. Optionally pass an initial prompt.

### Non-interactive (scripted) execution
```sh
codex exec [OPTIONS] [PROMPT]
```
Runs a task non-interactively. Useful for automation or piping output.

```sh
echo "refactor this function to use early returns" | codex exec -
```

### Code review
```sh
codex review
# or non-interactively:
codex exec review
```
Runs a code review against the current repository.

### Apply latest diff
```sh
codex apply   # alias: codex a
```
Applies the latest diff produced by the Codex agent as a `git apply` to the local working tree.

### Resume / fork a session
```sh
codex resume          # pick from previous sessions
codex resume --last   # continue most recent session
codex fork --last     # fork most recent session into a new one
```

## Key Options

| Flag | Description |
|------|-------------|
| `--full-auto` | Low-friction mode: workspace-write sandbox, ask on-request approval |
| `-s, --sandbox <MODE>` | `read-only`, `workspace-write`, or `danger-full-access` |
| `-a, --ask-for-approval <POLICY>` | `untrusted`, `on-request`, `never` |
| `--search` | Enable live web search for the model |
| `-c key=value` | Override config (e.g. `-c model="o3"`) |
| `-C, --cd <DIR>` | Set working directory for the agent |

## Workflow Integration

### Running a focused task non-interactively
```sh
codex exec --full-auto "add docstrings to all public functions in src/"
```

### Applying changes after review
```sh
codex exec "fix the null check bug in auth.go"
codex apply
```

### Using with a specific model
```sh
codex -c model="o3" "optimize the database query in user_service.py"
```

## Sandbox Modes

- **read-only**: Agent can only read files (safest)
- **workspace-write**: Agent can read and write within the workspace (recommended for most tasks)
- **danger-full-access**: No restrictions (use only in fully isolated environments)

## Tips

- Use `codex exec` for automation pipelines or when you want output captured
- Use `codex resume --last` to continue a previous session if interrupted
- Pass prompts via stdin for complex, multi-line instructions
- `--full-auto` is the most convenient mode for trusted tasks in a workspace
