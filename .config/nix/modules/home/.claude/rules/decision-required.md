# Decision Required (DR) Pattern

When you encounter a judgment call — an ambiguity, trade-off, architectural choice, or anything not explicitly resolved by plan.md — do NOT guess. Follow this protocol.

## When to Trigger DR

- Requirements are ambiguous or contradictory
- Multiple valid implementation approaches exist with meaningful trade-offs
- A change touches a protected domain (see below)
- The plan says one thing but the code suggests another
- You are about to make a choice that is difficult to reverse

## DR Format

Stop execution and present:

### DR: <short title>

**Context**: <1-2 sentences on what you were doing when this came up>

**Option A**: <description>
- Pro: ...
- Con: ...

**Option B**: <description>
- Pro: ...
- Con: ...

**Recommendation**: <A or B> because <reason>

**Impact if deferred**: <what happens if we skip this decision for now>

## After Resolution

1. Log the decision to `decisions.md` in the project root:

   ```
   ## DR: <title>
   - **Date**: <date>
   - **Context**: <context>
   - **Decision**: <chosen option>
   - **Rationale**: <why>
   ```

2. If the decision changes plan.md, update plan.md immediately.
3. Resume execution.

## Protected Domains

These topics ALWAYS trigger a DR regardless of confidence level:

- Authentication / authorization
- Payment processing
- Data deletion or migration
- Security configuration
- Infrastructure / deployment changes
- API contract changes (breaking)
- License or legal implications
