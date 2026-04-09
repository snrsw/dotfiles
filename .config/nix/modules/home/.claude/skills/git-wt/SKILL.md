---
name: git-wt
description: Manage git worktrees using the git-wt CLI for parallel development. Use this skill whenever the user mentions worktrees, wants to work on a separate branch without stashing, needs to isolate risky changes, wants parallel development, says "git wt", "new worktree", "switch worktree", or asks to work on something without disrupting their current branch. Also use when you judge that a worktree would be the right approach — e.g., the user has uncommitted work and wants to start something unrelated, or needs to review/test another branch while keeping their current state.
---

# Git Worktree Management with git-wt

## When to Use a Worktree

Worktrees let you have multiple branches checked out simultaneously in separate directories. Reach for a worktree when:

- **The user has in-progress work and wants to do something else** — instead of stashing or committing half-done work, create a worktree for the new task.
- **Isolating risky or experimental changes** — prototyping, large refactors, or spikes that might get thrown away.
- **Reviewing or testing another branch** — check out a PR branch in a worktree without disrupting the current working tree.
- **Parallel development** — working on multiple features or fixes at the same time.

If the situation calls for it, proactively suggest a worktree even if the user didn't explicitly ask for one.

## Commands

### List worktrees
```sh
git wt
```
Shows all worktrees. Add `--json` for machine-readable output.

### Create or switch to a worktree
```sh
git wt <branch|worktree|path>
```
- If the worktree exists: prints its path
- If it doesn't exist: creates a new worktree and branch, then prints the path

### Create worktree from a start-point
```sh
git wt <branch> <start-point>
```
Creates a worktree branching from the given start-point (e.g., `origin/main`, a tag, or a commit).

### Delete worktree (safe)
```sh
git wt -d <branch|worktree|path>
```
Deletes the worktree and branch only if fully merged.

### Force delete worktree
```sh
git wt -D <branch|worktree|path>
```
Force deletes regardless of merge status. Confirm with the user before using this.

## Project Configuration

This project uses:
- `wt.basedir = .worktrees` — worktrees live in `.worktrees/` relative to the repo root
- `wt.copyignored = true` — .gitignore'd files (build artifacts, caches, .env) are copied into new worktrees

These are set via `git config`. You do not need to pass `--basedir` or `--copyignored` flags.

## Working in a Worktree from Claude Code

`git-wt` prints the worktree path to stdout in non-interactive contexts. After creating or switching to a worktree, capture the path and use it:

```sh
# Create/switch and capture path
WT_PATH=$(git wt feature-branch origin/main)

# Use the path for subsequent commands
ls "$WT_PATH"
cd "$WT_PATH" && make test
```

When working in a worktree, use absolute paths or `cd` into the worktree directory before running commands. The main working directory remains unchanged unless you explicitly `cd`.

## Integration with Other Skills

Worktrees pair naturally with the existing development workflow:

### With plan-driven-workflow
When starting a new feature that needs a plan:
1. Create a worktree: `git wt feature-name origin/main`
2. Create `plan.md` inside the worktree
3. Follow the plan-driven-workflow from there

### With tdd
Each worktree is a self-contained workspace. Run the Red → Green → Refactor cycle inside the worktree directory. All test commands should target the worktree path.

### With tidy-first
If a structural refactor is needed before a behavioral change, consider doing the tidy work in the main tree and the feature work in a worktree, or vice versa — keeping the two concerns physically separated.

### With commit-message
Commits inside a worktree go to that worktree's branch. Use commit-message skill as usual — the branch context is automatic.

## Workflow Examples

**Start a feature without disrupting current work:**
```sh
git wt add-auth origin/main
# → creates .worktrees/add-auth, prints path
```

**Review a PR branch:**
```sh
git wt pr-branch
# → checks out existing branch in a new worktree
```

**Clean up after merging:**
```sh
git wt -d add-auth
# → removes worktree and branch
```

## Key Details

- The default branch (main/master) is protected from accidental deletion.
- Use `--copyuntracked` or `--copymodified` flags if you need untracked or modified files carried into the new worktree.
- Use `--hook <cmd>` to run setup commands (e.g., `npm install`) after worktree creation.
