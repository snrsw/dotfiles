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
## <type emoji> <Title>

<One paragraph explaining the WHY — motivation, context, problem solved.>

## Changes

- <bullet>

## Test plan

- [x] <verification>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

### Language

Detect the language used in the recent merged PRs fetched above. Write the PR body in that same language to stay consistent with the project's convention. However, keep section headings (`## Changes`, `## Test plan`, etc.) in English regardless of the body language — headings serve as structural anchors and should remain universal.

The section *names* are also fixed: even if recent merged PRs use different section labels (e.g., `## Summary` instead of `## Changes`), follow the format prescribed above. Mirror project convention for language only, not for structure.

### Body Format Rules

- **Heading**: `## <type emoji> <Title>` — use the same emoji as the commit type (the type table lives in `commit-message`); for a commit emoji outside that table (e.g., 🔥 remove), carry it through verbatim. When commits mix types, pick the type that carries the PR's primary value. Drop the commit scope `(xxx)` from the title; the title should read as a standalone statement.
- **Why paragraph**: explain motivation, not mechanics
- **Changes**: one bullet per logical unit of change, referencing package/file names where helpful
- **Test plan**: checked boxes `[x]` mark items where you actually verified the property — either by executing the check (build, test, manual interaction) or by direct static observation (e.g., grep, diff inspection) where the annotation makes the method explicit, e.g., `(verified by grep)`. Items needing execution that you did not run stay `[ ]`.
- **Footer**: always include `🤖 Generated with [Claude Code](https://claude.com/claude-code)`
- **No planning jargon**: never carry internal planning tokens into the PR body — task IDs (`T1`, `T2`), phase labels (`Phase 1.2`, `Step 3`), sprint names, story references from plan.md or similar files. Reviewers have no context for these. Replace them with plain descriptions of what changed and why.

### Response Style

The `response-style` rule names "PR text" explicitly, so it applies to everything
inside the format above. That format governs structure; these govern the prose.

- **Why paragraph**: lead with the conclusion. One meaning per sentence — split a
  sentence carrying two claims. Plain words; delete sentences that only build
  atmosphere.
- **Same term for the same concept** throughout, matching the terms in the diff
  itself (identifiers, file names, headings). No synonym rotation.
- **Separate fact from speculation.** A `Changes` bullet states what changed; mark
  any causal or performance claim as inference ("we expect", "not profiled"). A
  `[x]` test-plan item is a verified fact by definition — never check a box for
  something you only inferred.
- **No back-jumps**: a bullet that depends on an earlier bullet restates the needed
  piece in one clause rather than pointing back at it.
- **Tables**, if used: one kind of content per column; status columns drawn from a
  small closed set; the table must agree with the surrounding prose.

