# debug examples

## Bug Mode

```go
// Phase 1 — Reproduce
// CalculateDiscount(100, 0) returns -5, expected 0

// Phase 2 — Isolate
// Root cause: discount rate defaults to -0.05 when 0 is passed
// Ruled out: input validation (caller passes correct value)

// Phase 3 — Fix (Red → Green)
func TestCalculateDiscount_ZeroRate(t *testing.T) {
    got := CalculateDiscount(100, 0)
    if got != 0 {
        t.Errorf("CalculateDiscount(100, 0) = %f, want 0", got)
    }
}
// ❌ FAILS — returns -5

// Fix: check for zero rate before applying default
// ✅ PASSES

// Phase 4 — Verify: full test suite passes
// Commit: 🐛(pricing): handle zero discount rate instead of applying default
```

## Investigation Mode

```
// "Nix build seems slower than last week" — no clear failure

// Phase 2 (front-loaded) — Isolate
// Add timing to build phases, compare with cached build log
// Hypothesis 1: new dependency added → ruled out (deps unchanged)
// Hypothesis 2: derivation rebuilding unnecessarily → confirmed
// Root cause: hash changed due to unrelated file included in source filter

// Confirmed as bug → switch to Bug Mode at Phase 3
// Write test for source filter, fix filter, verify build time
```

## DR Trigger

```
// Debugging a login failure — root cause is in session token validation
// Session handling is a protected domain → trigger DR before applying fix
```
