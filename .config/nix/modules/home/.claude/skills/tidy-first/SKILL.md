---
name: tidy-first
description: Follow Kent Beck's Tidy First principles by strictly separating structural changes from behavioral changes. Use when refactoring code, restructuring code, making structural changes without changing behavior, renaming variables/functions, extracting methods, separating concerns, preparing code for new features, or need to ensure structural and behavioral changes are in separate commits.
---

# tidy-first

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
- **Never mix structural and behavioral changes in the same PR**
- Each PR should be either purely structural OR purely behavioral
- Within a PR, each commit should also be a single logical unit of the same type
- This makes code review easier, debugging simpler, and reverts safer

#### Structural Changes First
- **Always make structural changes first when both are needed**
- Create and merge the structural PR before starting the behavioral PR
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
1. Create a dedicated branch for structural changes
2. Ensure all tests are currently passing
3. Make one structural change at a time
4. Run tests to verify behavior unchanged
5. Commit the structural change with clear message
6. Repeat for next structural change if needed
7. Open a PR containing only structural changes

#### When Making Behavioral Changes
1. Merge the structural PR first
2. Create a new branch from the updated base for behavioral changes
3. Make behavioral changes
4. Follow TDD cycle (Red → Green → Refactor)
5. Commit behavioral changes separately
6. Open a PR containing only behavioral changes

### PR and Commit Discipline

#### PR Separation
- One PR per change type: structural OR behavioral, never both
- Structural PRs are merged before their corresponding behavioral PRs
- Keep PRs small and focused on a single purpose

#### Commit Message Format
Use the `commit-message` skill format:
- Structural changes: ♻️ refactor or 🧹 tidy
- Behavioral changes: ✨ feat or 🐛 fix

#### Commit Requirements
Only commit when:
1. ALL tests are passing
2. ALL compiler/linter warnings have been resolved
3. The change represents a single logical unit of work

#### Commit Frequency
- Use small, frequent commits rather than large, infrequent ones
- Each structural change gets its own commit
- Each behavioral change gets its own commit

### Refactoring Patterns

Use established refactoring patterns with their proper names:

- **Extract Method**: Pull code into a new method
- **Rename**: Change names to better express intent
- **Move Method**: Relocate method to more appropriate class
- **Extract Class**: Split large class into smaller ones
- **Inline Method**: Replace method call with method body
- **Replace Temp with Query**: Replace temporary variable with method
- **Introduce Parameter Object**: Group parameters into object

### Examples

#### Structural Change Example

```go
// Before Refactoring
func CalculateTotal(price float64, taxRate float64) float64 {
    tax := price * taxRate
    return price + tax
}
// After Refactoring - Extract Method
func CalculateTotal(price float64, taxRate float64) float64 {
    tax := CalculateTax(price, taxRate)
    return price + tax
}
func CalculateTax(price float64, taxRate float64) float64 {
    return price * taxRate
}
```

#### Behavioral Change Example

```go
// Before Behavioral Change
func CalculateTotal(price float64, taxRate float64) float64 {
    tax := price * taxRate
    return price + tax
}
// After Behavioral Change - Change Tax Calculation
func CalculateTotal(price float64, taxRate float64) float64 {
    tax := price * taxRate * 1.1 // New tax logic
    return price + tax
}
```

