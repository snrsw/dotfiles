---
name: replay-prompt
description: Distill the current conversation into a single self-contained prompt that would let a fresh session redo the same task efficiently. Use when the user says "what would have been a better first prompt", "give me a prompt to redo this in a fresh session", "distill this conversation into one prompt", "rewrite my opening prompt with everything we know now", "replay this somewhere else", or "seed a new session with this". Also use proactively when you judge it useful — e.g., after a clarification-heavy or course-corrected session that the user is likely to repeat on another machine, branch, or repo.
---

# replay-prompt

## Instructions

Read the entire conversation as a transcript and produce the opening prompt the user *should* have written if they had known then what is known now. The output is an executable artifact, not a recap — a fresh session pasted with this prompt should reach the same outcome without the detours.

### Core Principle

The literal opening prompt is rarely the real task. The real task is what the conversation converged on after clarifications, corrections, and discoveries. Distill that, and fold in every constraint, default, and dead end so the new session does not relive them.

### Workflow

#### Phase 1: Reconstruct the true goal

- Re-read the conversation start to finish before drafting
- Identify the actual outcome the user wanted, not just the literal first message
- If the goal shifted mid-session, take the final understanding as authoritative
- If multiple distinct tasks happened in one conversation, ask the user which to distill (default: one prompt per task)

#### Phase 2: Harvest the session

Extract everything a fresh session would otherwise have to rediscover:

- **Constraints and preferences** surfaced via `clarification-required` rounds, corrections ("no, do it this way"), or stated defaults
- **Decisions** from `decision-required` — fold the chosen option in; drop alternatives unless they explain a "Do NOT"
- **Environment and state** — repo paths, branch, language, framework versions, file paths actually touched, conventions discovered in the codebase
- **Dead ends** — approaches that were tried and failed; convert each into an explicit "Do NOT" line
- **Success criteria** — how the user signaled "done" (tests passing, specific file shape, manual check)

#### Phase 3: Draft three variants

Produce three candidates that differ in *framing*, not in *facts*. Each carries the same harvested content; only the structure varies:

- **Minimal**: only must-have requirements + dead ends; trust the new session to derive the rest
- **Comprehensive**: every harvested fact made explicit; lowest ambiguity, highest verbosity
- **Workflow-led**: explicitly invokes existing skills (`tdd`, `tidy-first`, `plan-driven-workflow`, `commit-message`, etc.) where applicable, leveraging convention over restating it

Each variant fills this template:

```
<One-sentence task statement — what to produce, for whom, where.>

Context:
- <repo / paths / branch / environment facts>
- <conventions already verified>

Requirements:
- <bullets, including mid-session surfacings>

Do NOT:
- <each dead end as one anti-pattern line>

Done when:
- <concrete success criteria>
```

Skip a section when the session produced nothing for it — do not pad. Run the Quality Checklist on each variant before sending to Phase 4.

#### Phase 4: Evaluate variants empirically

Spawn one subagent per variant **in parallel** (single message, multiple `Agent` tool calls). Each subagent receives only its candidate prompt and is instructed:

> "Imagine you just received this as the opening message of a fresh Claude Code session with no prior context. Evaluate (do NOT execute the task). Score 1–5 on each: (a) goal clarity, (b) constraint sufficiency, (c) ambiguity / would you need to ask clarifying questions, (d) executability, (e) verifiability of 'Done when'. List any clarifying questions you would need to ask. Return ≤200 words in a structured format."

Use `subagent_type: "general-purpose"` with `model: "opus"`. Cap each response at 200 words.

#### Phase 5: Pick winner and deliver

Select the variant with the highest aggregate score and fewest clarifying questions. On ties, prefer the Comprehensive variant. Run the Quality Checklist on the winner one more time.

Return three things in chat:

1. **The winning prompt** in a single fenced ```` ```text ```` block so the user can copy verbatim
2. **Distilled from** — 3–6 bullets listing what was folded in (which CR/DR resolutions, course corrections, dead ends)
3. **Eval summary** — one line per variant with scores and the winner, so the user can request a different variant if desired

Do not write the prompt to a file unless the user asks.

### Quality Checklist

Run this twice — in Phase 3 on each variant before subagent eval, and in Phase 5 on the winner before delivery. Any "no" triggers a revision pass.

1. **Goal fidelity** — Does the task statement match the *converged* intent, not the literal opening prompt?
2. **Constraint completeness** — Every CR resolution, DR decision, mid-session correction, and environment fact captured?
3. **Anti-pattern coverage** — Dead ends explicit as "Do NOT" lines?
4. **Self-contained executability** — Actionable with zero prior context? No dangling "the file we were working on" references?
5. **No hallucination / no bloat** — Only facts the session actually established? Every line earns its place?
6. **Safety preservation** — Protected-domain triggers (auth, deletions, infra, etc.) require the new session to fire `decision-required`? DR resolved in the original session does NOT carry over.
7. **Verifiable "Done when"** — Success criterion concrete enough for objective verification?

### Edge Cases

- **Incomplete task** — write as starting-over with partial progress in Context, unfinished work in Requirements. Do not pretend it is done
- **Multi-task session** — ask which task to distill before generating variants
- **Smooth session, nothing to distill** — say so explicitly and return the original prompt with at most a one-line tightening. Skip Phases 3–4 entirely; no variant generation, no subagent eval
- **Protected-domain work** — include a one-line note in the generated prompt that the new session must trigger `decision-required` before acting, even if the original session had resolved the DR

### Integration with Other Skills

- **`clarification-required`**: every CR resolution from the source session becomes a baked-in requirement; the new session does not re-ask
- **`decision-required`**: chosen options become requirements; rejected options become "Do NOT" entries when they explain why
- **`documentation-layers`**: the distilled prompt sits at the *Why* and *What* layer — keep it about contract and constraints, not implementation steps the new session should derive
- **`plan-driven-workflow`**: if the source session built a `plan.md`, reference it by path in Context rather than inlining it

### Golden Rules

1. **Distill, do not summarize** — the output is an executable prompt, not a session log
2. **Bake in the corrections** — every "no, do it this way" turn becomes a requirement or anti-pattern
3. **Kill the dead ends** — explicit "Do NOT" lines for paths that already failed
4. **No invented context** — only include facts the session actually established
5. **One prompt, one task** — split multi-task sessions, never merge
6. **Empirical eval beats self-grade** — always run subagents on candidate variants; do not skip Phase 4

## Examples

### Messy session distilled

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

Distilled from: CR rounds 1–2 (scope + JWT/jose), DR (Result over throw), dead-end refactor (rolled back), commit-split correction.

Eval summary: Minimal 17/25, Comprehensive 22/25, Workflow-led 24/25 (winner).

### Smooth session, no distillation gain

Original opening prompt was already specific (file path, behavior change, success criteria). Phases 3–4 skipped. Return:

> The original prompt was already well-formed. A fresh session would not benefit from distillation. If you want to replay it elsewhere, paste the original prompt as-is.
