---
name: code-quality
description: Apply code quality standards and best practices to maintain clean, maintainable code. Use when reviewing code, improving code quality, refactoring, or ensuring code meets quality standards.
---

# code-quality

## Instructions

Apply these code quality principles to all development work to maintain clean, maintainable code.

### Code Quality Checklist

When reviewing or writing code, check:

- [ ] **No duplication** - Is any code repeated unnecessarily?
- [ ] **Clear names** - Do names clearly express intent?
- [ ] **Explicit dependencies** - Are all dependencies visible?
- [ ] **Single responsibility** - Does each function do one thing?
- [ ] **Minimal state** - Is mutable state minimized?
- [ ] **Simple solution** - Is this the simplest approach?
- [ ] **Readable** - Can someone else understand this easily?
- [ ] **Testable** - Is the code easy to test?
- [ ] **Documented** - Document at the right layer: Code → How, Tests → What, Commits → Why, Comments → Why not. Keep documentation up to date with code changes.

### When to Apply

Apply these standards:
- During code reviews
- When refactoring
- While writing new code
- When improving existing code
- Before committing changes

### Integration with Other Practices

- **With TDD**: Apply during the Refactor phase
- **With Tidy First**: Use when making structural changes
- **With Commits**: Ensure quality before each commit


## Examples

#### 1. Eliminate Duplication Ruthlessly

**Principle**: Don't Repeat Yourself (DRY)

- Identify repeated code patterns
- Extract common functionality into reusable functions/methods
- Use abstraction to eliminate duplication
- Apply the "Rule of Three" - if code appears three times, extract it

**Examples of Duplication to Eliminate**:
```go
// Bad - Duplication
func ProcessOrder(order Order) {
    if order.Total < 0 {
        return errors.New("invalid total")
    }
    // process order
}

func ProcessRefund(refund Refund) {
    if refund.Amount < 0 {
        return errors.New("invalid amount")
    }
    // process refund
}

// Good - Extracted validation
func ValidatePositiveAmount(amount int, fieldName string) error {
    if amount < 0 {
        return fmt.Errorf("invalid %s", fieldName)
    }
    return nil
}
```

#### 2. Express Intent Clearly Through Naming and Structure

**Principle**: Code should be self-documenting

- Use descriptive, meaningful names for variables, functions, and types
- Choose names that reveal intent and purpose
- Structure code to make the flow obvious
- Avoid cryptic abbreviations or single-letter names (except standard loop counters)

**Good Naming Examples**:
```go
// Bad
func calc(u User, o Order) int {
    t := o.T
    d := u.D
    return t - (t * d / 100)
}

// Good
func CalculateDiscountedTotal(user User, order Order) int {
    total := order.Total
    discountPercent := user.DiscountPercent
    discount := total * discountPercent / 100
    return total - discount
}
```

#### 3. Make Dependencies Explicit

**Principle**: Dependencies should be visible and clear

- Avoid hidden dependencies and global state
- Pass dependencies as parameters
- Use dependency injection
- Make it clear what a function/method needs to work

**Examples**:
```go
// Bad - Hidden dependency
var db *Database

func SaveUser(user User) error {
    return db.Insert(user)  // Where did db come from?
}

// Good - Explicit dependency
func SaveUser(db *Database, user User) error {
    return db.Insert(user)  // Clear that we need a database
}

// Better - Dependency injection
type UserService struct {
    db *Database
}

func (s *UserService) SaveUser(user User) error {
    return s.db.Insert(user)
}
```

#### 4. Keep Methods Small and Focused on Single Responsibility

**Principle**: Single Responsibility Principle (SRP)

- Each function/method should do one thing well
- If a function does multiple things, split it
- Aim for functions that fit on one screen
- Each function should have one reason to change

**Guidelines**:
- If using "and" to describe a function, it probably does too much
- Extract helper methods for distinct sub-tasks

```go
// Bad - Does too much
func ProcessOrder(order Order) error {
    // Validate
    if order.Total < 0 {
        return errors.New("invalid total")
    }

    // Calculate discount
    discount := order.Total * order.DiscountPercent / 100
    finalTotal := order.Total - discount

    // Save to database
    db.SaveOrder(order)

    // Send email
    email.Send(order.CustomerEmail, "Order confirmed")

    // Update inventory
    inventory.Reduce(order.Items)

    return nil
}

// Good - Single responsibilities
func ProcessOrder(order Order) error {
    if err := ValidateOrder(order); err != nil {
        return err
    }

    finalTotal := CalculateOrderTotal(order)

    if err := SaveOrder(order); err != nil {
        return err
    }

    if err := NotifyCustomer(order); err != nil {
        return err
    }

    return UpdateInventory(order)
}
```

#### 5. Minimize State and Side Effects

**Principle**: Prefer pure functions when possible

- Reduce mutable state
- Make side effects explicit and controlled
- Prefer pure functions that don't modify external state
- Isolate stateful operations

**Examples**:
```go
// Bad - Side effects and mutation
var totalRevenue int

func ProcessSale(amount int) {
    totalRevenue += amount  // Hidden side effect
}

// Good - Explicit, no side effects
func CalculateNewRevenue(currentRevenue int, saleAmount int) int {
    return currentRevenue + saleAmount
}

// Caller controls state
totalRevenue = CalculateNewRevenue(totalRevenue, saleAmount)
```

#### 6. Use the Simplest Solution That Could Possibly Work

**Principle**: YAGNI (You Aren't Gonna Need It)

- Don't build for hypothetical future requirements
- Solve today's problem, not tomorrow's
- Avoid over-engineering
- Add complexity only when needed

**Examples**:
```go
// Bad - Over-engineered for simple need
type ConfigManager interface {
    Get(key string) interface{}
    Set(key string, value interface{})
    Delete(key string)
    Clear()
    Export() map[string]interface{}
    Import(map[string]interface{})
}

// Good - Just what's needed now
type Config struct {
    APIKey string
    Timeout int
}
```

### Benefits

- **Maintainability**: Easier to modify and extend
- **Readability**: Team members understand code faster
- **Fewer bugs**: Clear, simple code has fewer defects
- **Testability**: Quality code is easier to test
- **Longevity**: Code remains useful longer
