# Documentation Layers

Every code change writes to four documentation surfaces — code, tests, commits, comments. Each answers a different question. Putting the wrong content at the wrong layer creates rot: comments contradict code, commit messages restate diffs anyone can read, tests describe implementation instead of contract.

## The four layers

**Code → How.** The implementation itself. Names and structure should make intent obvious. Don't narrate what the code does — let the code do that.

**Tests → What.** The contract the system promises. A reader scanning test names should learn the observable behavior. Don't describe *how* the implementation works.

**Commits → Why.** The reason this change exists *now* — the constraint, bug, decision, or external trigger that motivated it. Don't restate the diff.

**Comments → Why not.** The non-obvious thing a future reader can't see: a hidden constraint, a workaround for a specific bug, a path that was tried and rejected, an invariant that isn't enforced by the type system. Don't explain *what* the code does — the code already does that.

## Anti-patterns

- Comments that paraphrase identifiers (`// increment counter` above `counter++`) — duplicate of code.
- Commit messages that list changed files or restate the diff — duplicate of `git show`.
- Test names that encode the implementation (`test_service_calls_repo_then_returns`) — describe the contract instead.
- Long paragraph comments explaining flow — usually a sign the code itself should be clearer first.
- Docstrings that repeat the function signature in prose — empty calories.

## When to apply

Whenever you write or modify code. Use the layers as the lens: *is this content pulling its weight, or duplicating an adjacent layer?* If a comment, commit message, or test name could be deleted without losing information, it belongs to a different layer or shouldn't exist.
