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
- ♻️ `refactor`: Restructure how code is organized — module boundaries, control flow, dependencies between components — without changing behavior
- 🧹 `tidy`: Small mechanical cleanups without changing behavior — rename, extract method/variable, reorder, dead-code removal
- 🎨 `style`: Formatting-only changes (whitespace, semicolons, quotes) — no code structure change
- ⚡ `perf`: Performance improvements
- ✅ `test`: Adding/updating tests
- 📝 `docs`: Documentation changes
- 🔧 `chore`: Build process, dependencies, tooling

**Choosing when types overlap**:
- **🧹 tidy vs ♻️ refactor**: if an IDE could perform the change mechanically (symbol rename, extract method, reorder) — even across files — it is 🧹. If it requires judgment about module boundaries, control flow, or dependency direction, it is ♻️.
- **Multi-type diffs** (e.g. feat + its tests + its new dependency): use the type of the change that delivers the primary user-facing value; supporting tests/deps/docs that exist only to land that change fold into the same commit.
- **Unrelated changes**: split into separate commits instead of picking a combined type.

## Examples

**Examples**:
```
✨(auth): add OAuth2 login support since many users requested it
🐛: fix crash on null pointer in order processing
♻️(cart): invert dependency between pricing and inventory modules
🧹(cart): extract calculateTotal method
✅: add tests for user registration
📝: update API documentation for payment endpoint
```
