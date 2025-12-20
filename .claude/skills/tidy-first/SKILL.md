---
name: tidy-first
description: Follow Kent Beck's Tidy First principles by separating structural changes from behavioral changes. Use when refactoring code, restructuring code, making structural changes, separating concerns, or preparing code for new features.
---

# Tidy First

## Instructions
Follow Kent Beck's "Tidy First" approach by strictly separating structural changes from behavioral changes in all development work.

### Core Principle
Separate all changes into two distinct types:

1. **STRUCTURAL CHANGES**: Rearranging code without changing behavior
   - Renaming variables, functions, classes
   - Extracting methods or functions
   - Moving code to different files or modules
   - Reorganizing code structure
   - Improving code organization

2. **BEHAVIORAL CHANGES**: Adding or modifying actual functionality
   - Adding new features
   - Fixing bugs
   - Changing business logic
   - Modifying functionality

### Golden Rules

#### Never Mix Change Types
- **Never mix structural and behavioral changes in the same commit**
- Each commit should be either purely structural OR purely behavioral
- This makes code review easier and debugging simpler

#### Structural Changes First
- **Always make structural changes first when both are needed**
- Tidy the code before adding new behavior
- Prepare the structure to receive new functionality

#### Validate Structural Changes
- **Validate structural changes do not alter behavior**
- Run all tests before making structural changes
- Run all tests after making structural changes
- Tests must pass both before and after - same results
- If behavior changes, it wasn't a pure structural change

### Workflow

#### When Making Structural Changes
1. Ensure all tests are currently passing
2. Make one structural change at a time
3. Run tests to verify behavior unchanged
4. Commit the structural change with clear message
5. Repeat for next structural change if needed

#### When Making Behavioral Changes
1. Complete all structural changes first
2. Commit all structural changes separately
3. Now make behavioral changes
4. Follow TDD cycle (Red → Green → Refactor)
5. Commit behavioral changes separately

### Commit Discipline

#### Commit Requirements
Only commit when:
1. ALL tests are passing
2. ALL compiler/linter warnings have been resolved
3. The change represents a single logical unit of work
4. Commit message clearly states whether it contains structural or behavioral changes

#### Commit Messages
- **Structural commits**: Prefix with "refactor:", "restructure:", or "tidy:"
  - Example: "refactor: extract calculateTotal method"
  - Example: "tidy: rename userId to customerId for clarity"

- **Behavioral commits**: Prefix with "feat:", "fix:", or describe the behavior
  - Example: "feat: add user authentication"
  - Example: "fix: correct tax calculation for Canadian customers"

#### Commit Frequency
- Use small, frequent commits rather than large, infrequent ones
- Each structural change gets its own commit
- Each behavioral change gets its own commit

### Code Quality Standards

Apply these principles during structural changes:

- **Eliminate duplication ruthlessly**
  - Look for repeated code patterns
  - Extract common functionality
  - Use DRY (Don't Repeat Yourself) principle

- **Express intent clearly through naming and structure**
  - Use descriptive names for variables, functions, classes
  - Make code self-documenting
  - Structure code to reveal intent

- **Make dependencies explicit**
  - Clearly show what depends on what
  - Avoid hidden dependencies
  - Use dependency injection where appropriate

- **Keep methods small and focused on a single responsibility**
  - Each function/method should do one thing well
  - Follow Single Responsibility Principle
  - Extract large methods into smaller, focused ones

- **Minimize state and side effects**
  - Prefer pure functions when possible
  - Make side effects explicit and controlled
  - Reduce mutable state

### Refactoring Patterns

Use established refactoring patterns with their proper names:

- **Extract Method**: Pull code into a new method
- **Rename**: Change names to better express intent
- **Move Method**: Relocate method to more appropriate class
- **Extract Class**: Split large class into smaller ones
- **Inline Method**: Replace method call with method body
- **Replace Temp with Query**: Replace temporary variable with method
- **Introduce Parameter Object**: Group parameters into object

### Integration with TDD

When following TDD:
1. Write failing test (Red)
2. Write minimum code to pass (Green)
3. Make structural changes if needed (Tidy First)
   - Each structural change committed separately
   - Tests remain green throughout
4. Move to next test

### Examples

#### Good: Separated Changes

**Commit 1 (Structural)**:
```
refactor: rename validateUser to validateUserCredentials

No behavior change. Tests pass before and after.
```

**Commit 2 (Behavioral)**:
```
feat: add email validation to user registration

Added email format validation when creating new users.
```

#### Bad: Mixed Changes

**Commit (Mixed - Don't Do This)**:
```
Add email validation and rename methods

- Renamed validateUser to validateUserCredentials
- Added email format validation
- Moved validation logic to separate class
```

This mixes structural (rename, move) with behavioral (add validation).

### Benefits

- **Easier code review**: Reviewers can quickly verify structural changes don't alter behavior
- **Safer refactoring**: Tests guarantee no behavior changed
- **Better git history**: Clear separation makes debugging easier
- **Easier rollback**: Can revert behavioral changes without losing structural improvements
- **Lower risk**: Small, focused changes reduce chance of introducing bugs
