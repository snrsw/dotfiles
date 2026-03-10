---
name: commit-message
description: Write conventional git commit messages with emoji type prefixes. Use this whenever committing changes, creating a commit message, or formatting a commit — even if the user just says "commit this" or "what should my commit message be". Always apply this when working in any git workflow.
---

# Commit Message

## Instructions

Follow strict commit discipline to maintain a clean, useful git history.

### Commit Message Guidelines

Commit messages should be clear, concise, and follow a standard format, and should explain the "why" behind the change.

### Commit Message Format

Use `<type emoji>(<target>): <description>` format. `<type emoji>` indicates change type, `<target>` is optional scope, `<description>` is one-line concise summary with no indent.

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

## Examples

**Examples**:
```
✨(auth): add OAuth2 login support since many users requested it
🐛: fix crash on null pointer in order processing
♻️(cart): extract calculateTotal method
✅: add tests for user registration
📝: update API documentation for payment endpoint
```
