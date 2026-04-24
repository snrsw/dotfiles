---
name: tdd
description: Guide development following Kent Beck's Test-Driven Development (TDD) using Red → Green → Refactor cycle. Use when writing tests first, implementing features with TDD, need to write failing tests, make tests pass, refactoring after tests pass, following red-green-refactor, fixing defects with tests, or practicing test-driven development methodology.
---

# Test-Driven Development (TDD)

## Instructions
Follow Kent Beck's Test-Driven Development (TDD) methodology precisely using the Red → Green → Refactor cycle.

### Core TDD Principles

#### The TDD Cycle
Always follow: **Red → Green → Refactor**

1. **Red**: Write a failing test
2. **Green**: Write minimal code to make it pass
3. **Refactor**: Improve structure while keeping tests green

### Test Writing Guidelines

#### Writing Tests
- Write the simplest failing test first
- Start by writing a failing test that defines a small increment of functionality
- Use meaningful test names that describe behavior (e.g., "shouldSumTwoPositiveNumbers")
- Make test failures clear and informative
- Write just enough code to make the test pass - no more
- Always write one test at a time

#### Test Execution
- Run tests to confirm they pass (Green)
- Always run all the tests (except long-running tests) each time
- Once tests pass, consider if refactoring is needed
- Repeat the cycle for new functionality

#### Defect Fixing
When fixing a defect:
1. First write an API-level failing test (exercises only the public contract the caller sees)
2. Then write the smallest possible test that replicates the problem — the minimum inputs and minimum assertion surface that still pin the defect
3. Get both tests to pass

If the fix requires a signature change (e.g., adding an `error` return), updating pre-existing tests to the new contract is a mechanical migration, not a forbidden refactor — preserve their behavioral assertions verbatim while adapting call sites.

### Implementation Guidelines

#### Minimum Implementation
- Implement the minimum code needed to make tests pass
- Use the simplest solution that could possibly work
- Write just enough code to make the test pass - no more

#### Code Quality
- Eliminate duplication ruthlessly
- Express intent clearly through naming and structure
- Make dependencies explicit
- Keep methods small and focused on a single responsibility
- Minimize state and side effects

### Refactoring in TDD

#### When to Refactor
- Refactor only when tests are passing (in the "Green" phase)
- Never refactor when tests are failing

#### How to Refactor
- Use established refactoring patterns with their proper names
- Make one refactoring change at a time
- Run tests after each refactoring step
- Prioritize refactorings that remove duplication or improve clarity

### TDD Workflow

#### Standard Feature Development
1. Write a simple failing test for a small part of the feature
2. Implement the bare minimum to make it pass
3. Run tests to confirm they pass (Green)
4. Make any necessary structural changes, running tests after each change
5. Add another test for the next small increment of functionality
6. Repeat until the feature is complete

### Discipline
- Always write one test at a time
- Make it run
- Improve structure
- Maintain high code quality throughout development

### Commit Standards

Use the `commit-message` skill format for all commits.

Only commit when:
1. ALL tests are passing
2. ALL compiler/linter warnings have been resolved
3. The change represents a single logical unit of work

Use small, frequent commits rather than large, infrequent ones.

## Example: Red → Green → Refactor

```go
// Red: write the failing test first
func TestAdd(t *testing.T) {
    if Add(2, 3) != 5 {
        t.Errorf("got %d, want 5", Add(2, 3))
    }
}
// ❌ FAILS — Add doesn't exist yet

// Green: simplest code that passes
func Add(a, b int) int { return a + b }
// ✅ PASSES

// Refactor: improve structure if needed, keeping tests green
```

For defect fixes: write a failing test that reproduces the bug first, then fix until it passes.
