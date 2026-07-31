# replay-prompt examples

Read this before drafting when you are unsure how much of a messy session to
fold in, or whether a session is smooth enough to skip distillation.

## Messy session distilled

Original opening prompt:

> "Can you clean up the auth module?"

After 4 CR rounds, 2 course corrections, and one dead-end refactor, the session converged. Winning variant (Workflow-led):

```text
Refactor src/auth/session.ts to extract token validation into a pure function, on branch refactor/auth-session. Use the tdd and tidy-first skills.

Context:
- Repo follows Tidy First: structural and behavioral changes go in separate commits
- Existing tests in src/auth/__tests__/session.test.ts must keep passing
- Token format is JWT (HS256), validated against env.JWT_SECRET

Requirements:
- Extract validateToken(raw: string): Result<Claims, AuthError> as a pure function
- Keep the SessionService API unchanged — callers must not break
- Add unit tests for validateToken: valid token, expired, malformed, wrong signature
- Commit as: 🧹 tidy(auth) for the extraction, then ✅ test(auth) for the new tests

Do NOT:
- Change SessionService method signatures
- Introduce a new JWT-parsing dependency — the existing jose import is fine
- Touch refresh-token logic — that is a separate task

Done when:
- pnpm test passes
- Two commits on the branch (tidy + test), no behavioral change in the tidy commit
```

Distilled from: clarification rounds 1–2 (scope + JWT/jose), DR (Result over throw), dead-end refactor (rolled back), commit-split correction.

## Smooth session, no distillation gain

Original opening prompt was already specific (file path, behavior change, success criteria). Variant generation and eval skipped. Return:

> The original prompt was already well-formed. A fresh session would not benefit from distillation. If you want to replay it elsewhere, paste the original prompt as-is.
