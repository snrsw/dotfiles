---
name: pr-body
description: Draft a well-structured GitHub pull request body following project conventions. Use whenever the user wants to write a PR description, open a pull request, or needs PR body content — even if they just say "write the PR" or "draft the PR description".
---

# pr-body

## Instructions

Follow this process to draft a well-structured pull request body.

### Steps

1. **Gather context** — run these in parallel:
    - `git diff <base>...HEAD` to review all commits on the branch
    - `git log --oneline` to see commit history
    - `gh pr list --state merged --limit 3 --json title,body` to recall recent PR style and detect language

2. **Draft the PR body** using this format:

```
## <One paragraph explaining the WHY — motivation, context, problem solved.>

## Changes

## Test plan


🤖 Generated with Claude Code
```

### Language

Detect the language used in the recent merged PRs fetched above. Write the PR body in that same language to stay consistent with the project's convention. However, keep section headings (`## Changes`, `## Test plan`, etc.) in English regardless of the body language — headings serve as structural anchors and should remain universal.

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

- [x] No duplicate version headings remain in CHANGELOG.md

🤖 Generated with Claude Code
```
