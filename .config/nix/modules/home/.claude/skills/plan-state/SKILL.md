---
name: plan-state
description: Use when any task spans multiple steps or sessions — looped or not — when progress must survive context compaction or a /clear, when resuming half-finished work, when tracking what is done / next / blocked, or when stopping mid-task so a later session can pick up cleanly. Distinct from plan mode, which gates the start of work in-conversation and does not persist.
---

# plan-state

A durable, on-disk progress file (`plan.md`) that records what is done, what is next, and what is blocked for a multi-step task — so work survives context compaction and resumes cleanly across sessions. Each item is done against a check defined up front — a test for code, an acceptance check for anything else — and execution runs until done.

This applies to **any** multi-step task, not just automated loops. A loop (`/loop`, issue-loop, a Routine) is one consumer of `plan.md`; an ordinary interactive session that might get compacted or resumed tomorrow is another.

## What this is — and what plan mode is

These are complementary, not duplicates:

- **Plan mode** decides *what to do*. It is ephemeral, gates the **start** of work via in-conversation approval, and is lost on compaction or in a fresh session.
- **plan-state** tracks and executes *across steps*. `plan.md` is a file on disk — the task's memory. It survives compaction and lets a later session pick up exactly where this one stopped.

Use plan mode to agree on the approach; use this skill to record and grind through it.

## When to use

- The task spans multiple steps or more than one session.
- You need progress to survive context compaction or a fresh session.
- You are resuming half-finished work.
- You want to run "until done" rather than confirming each step by hand.
- You are stopping mid-task and a later session must continue without re-planning.

**When NOT to use:** a task that finishes comfortably in one sitting. A `plan.md` for a two-step change is noise — a stray file that lingers and confuses the next session.

## The plan.md file

Location: for code, the repo root — or the worktree root when working under `git-wt`. For work with no repo, put it alongside the deliverable (the doc folder, the project directory). One `plan.md` per task/worktree.

```markdown
# <task title>

## Done
- [x] <completed item> — <commit sha or short note>

## Next
- [ ] <current item — top of this list is what runs next>
- [ ] <following item>

## Blocked / DR
- [ ] <item> — <reason, or link to the DR awaiting a decision>

## Notes
- <key decisions, environment facts>
- Do NOT: <dead ends already tried, so a fresh session does not relive them>
```

## Execution: run until done, test-first

On activation or resume:

1. **Read `plan.md`.** The top unmarked item in `## Next` is the current item.
2. **Do the item against a check defined up front.** For code, that check is a test — implement it test-first via the `tdd` skill (Red → Green → Refactor). For work with no test surface (prose, research, config, ops), state the item's acceptance check before starting — what it must contain or satisfy — then do the work and verify against it. Same discipline, domain-appropriate check.
3. **Mark it `[x]`** and move it to `## Done`. Record any decision or dead end in `## Notes`.
4. **Advance automatically to the next item** — do *not* wait for the user — as long as the item's check passed.
5. **Stop and surface to the user** only when one of these is true:
   - All `## Next` items are done.
   - A step fails and you cannot get it green after a reasonable attempt — switch to the `debug` skill.
   - A DR trigger fires (protected domain, ambiguous requirement, hard-to-reverse choice).
   - The next item needs a decision `plan.md` does not resolve.

This deliberately replaces any "wait for a go after every step" behavior, matching the global WORKFLOW rule ("don't wait for a 'go'").

## Resuming across sessions

`plan.md` is the handoff. A fresh session reads it and continues at the top of `## Next` — no re-planning. Reach for `replay-prompt` only when the surrounding *context* (not just the checklist) also needs to move to another machine, branch, or repo.

## Keeping plan.md honest

- One `## Next` item = one unit of progress: a single Red → Green → Refactor cycle (one behavioral change), one structural/tidy step, or one self-contained non-code deliverable. Do not bundle several.
- Mark `[x]` only after the item's check passes **and** the change is persisted — tests green and the commit landed for code; the acceptance check met and the artifact saved for other work.
- The `— <commit sha or short note>` on a `## Done` item is optional but valuable as a pointer to where the finished work lives: a commit sha for code, a file path or doc link for other work. Omit only when nothing would help a fresh session find it.
- If you discover new work mid-task, **add it to `## Next`** rather than doing it silently — this keeps scope visible and guards against comprehension debt.
- Record every dead end as a `Do NOT:` line in `## Notes`.
- Record intentional deferrals — decisions that are "correct as-is, do not action yet" — distinctly from dead ends (e.g. a `Deferred:` line in `## Notes`, or keep the item in `## Blocked / DR` with the reason it is *intentionally* not next). This stops a resumed session from mistaking a deliberate non-action for unfinished work and redoing or "fixing" it.

## Integration with other skills

- **tdd** — each `## Next` item is implemented via Red → Green → Refactor.
- **tidy-first** — structural changes get their own `## Next` entries and commits, separate from behavioral ones.
- **git-wt** — `plan.md` lives in the worktree root; one plan per worktree/task.
- **debug** — if a step fails unexpectedly, switch to `debug`; add the regression test as a `## Next` item, then resume.
- **commit-message** — mark an item `[x]` only after its commit lands.
- **replay-prompt** — for moving full context to a fresh session elsewhere; `plan.md` handles same-repo resume on its own.
- **DR pattern** — an item waiting on a decision goes under `## Blocked / DR` with a link, not silently skipped.
