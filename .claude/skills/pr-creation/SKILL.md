---
name: pr-creation
description: Create a GitHub pull request following project conventions. Use when the user asks to create a PR or open a pull request.
---

# pr-creation

## Instructions

Follow this process to create a well-structured pull request.

### Steps

1. **Gather context** — run these in parallel:
    - `git status` to see uncommitted changes
    - `git diff <base>...HEAD` to review all commits on the branch
    - `git log --oneline` to see commit history
    - `gh pr list --state merged --limit 3` to recall recent PR style

2. **Draft the PR title**
    - Plain text, imperative, concise (no emoji in title)
    - Mirrors the commit message subject without the type prefix

3. **Draft the PR body** using this format:

```
## <One paragraph explaining the WHY — motivation, context, problem solved.>

## Changes

## Test plan


🤖 Generated with Claude Code
```

4. **Create the PR** with `gh pr create --title "..." --body "..."` using a HEREDOC for the body.

### Body Format Rules

- **Heading**: `## <type emoji> <Title>` — use the same emoji as the commit type (✨ feat, 🐛 fix, ♻️ refactor, 📝 docs, ⚡ perf, 🧹 tidy, ✅ test, 🔧 chore)
- **Why paragraph**: explain motivation, not mechanics
- **Changes**: one bullet per logical unit of change, referencing package/file names where helpful
- **Test plan**: checked boxes `[x]` showing what was actually verified (build, tests, manual checks)
- **Footer**: always include `🤖 Generated with [Claude Code](https://claude.com/claude-code)`

### Example

```
## 🐛 Fix duplicate version sections in CHANGELOG

tagpr writes a CHANGELOG section when creating the release PR, then
appends a new section after merge — leaving the pre-merge entry as an
orphaned duplicate.

## Changes

- Remove duplicate ## [0.0.8] section
- Remove duplicate ## [0.0.4] section
- Remove duplicate ## [0.0.3] section

## Test plan

- [] No duplicate version headings remain in CHANGELOG.md

🤖 Generated with Claude Code
```
