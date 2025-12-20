---
name: commits
description: Follow strict commit discipline for clean git history. Use when committing changes, managing git commits, writing commit messages, or organizing code changes for version control.
---

# Commits

## Instructions

Follow strict commit discipline to maintain a clean, useful git history.

### Commit Message Guidelines

Commit messages should be clear, concise, and follow a standard format, and should explain the "why" behind the change.

### Commit Message Format

Use `<type emoji>(<target>): <description>` format. `<type emoji>` indicates change type, `<target>` is optional scope, `<description>` is concise summary.

**Types**:
- ✨ `feat`: New feature
- 🐛 `fix`: Bug fix
- ♻️ `refactor`: Code refactoring
- ✅ `test`: Adding/updating tests
- 📝 `docs`: Documentation changes
- 🎨 `style`: Code style changes (formatting)
- 🔧 `chore`: Build process, dependencies
- ⚡ `perf`: Performance improvements
- 🧹 `tidy`: Structural code changes (renaming, extracting methods)

### Commit Frequency

**Prefer small, frequent commits over large, infrequent ones**

#### Benefits of Small Commits:
- Easier to review
- Easier to understand
- Easier to revert if needed
- Clearer history
- Better bisection for debugging
- Reduced merge conflicts

#### Guidelines:
- Commit after each passing test (in TDD)
- Commit each refactoring separately
- Commit each feature increment separately
- Don't wait until "everything is done"

## Examples

**Examples**:
```
✨(auth): add OAuth2 login support since many users requested it
🐛: fix crash on null pointer in order processing
♻️(cart): extract calculateTotal method
✅: add tests for user registration
📝: update API documentation for payment endpoint
```
