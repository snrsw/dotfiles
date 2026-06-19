---
name: loop-state
description: Maintain a durable plan.md progress file for multi-step or multi-session work, and drive it test-first until done. Use when a task spans many steps or sessions, when progress must survive context compaction, when resuming half-finished work, when tracking what is done / next / blocked, or when running a task "until done" with verification between steps. This is the persistent state file for longer work — distinct from plan mode, which gates the start of work in-conversation and does not persist.
---

# loop-state

A durable, on-disk progress file (`plan.md`) that records what is done, what is next, and what is blocked for a multi-step task — so work survives context compaction and resumes cleanly across sessions. Execution is test-first and runs until done.

## What this is — and what plan mode is

These are complementary, not duplicates:

- **Plan mode** decides *what to do*. It is ephemeral, gates the **start** of work via in-conversation approval, and is lost on compaction or in a fresh session.
- **loop-state** tracks and executes *across steps*. `plan.md` is a file on disk — the loop's memory. It survives compaction and lets a later session pick up exactly where this one stopped.

Use plan mode to agree on the approach; use this skill to record and grind through it.

## When to use

- The task spans multiple steps or more than one session.
- You need progress to survive context compaction or a fresh session.
- You are resuming half-finished work.
- You want to run "until done" rather than confirming each step by hand.

## The plan.md file

Location: repo root, or the worktree root when working under `git-wt`. One `plan.md` per task/worktree.

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
2. **Implement it test-first** via the `tdd` skill: Red → Green → Refactor.
3. **Mark it `[x]`** and move it to `## Done`. Record any decision or dead end in `## Notes`.
4. **Advance automatically to the next item** — do *not* wait for the user — as long as tests stay green.
5. **Stop and surface to the user** only when one of these is true:
   - All `## Next` items are done.
   - A step fails and you cannot get it green after a reasonable attempt — switch to the `debug` skill.
   - A DR trigger fires (protected domain, ambiguous requirement, hard-to-reverse choice).
   - The next item needs a decision `plan.md` does not resolve.

This deliberately replaces any "wait for a go after every step" behavior, matching the global WORKFLOW rule ("don't wait for a 'go'").

## Resuming across sessions

`plan.md` is the handoff. A fresh session reads it and continues at the top of `## Next` — no re-planning. Reach for `replay-prompt` only when the surrounding *context* (not just the checklist) also needs to move to another machine, branch, or repo.

## Keeping plan.md honest

- One `## Next` item = one Red → Green → Refactor cycle (one behavioral change), or one structural/tidy step. Do not bundle several.
- Mark `[x]` only after the item's tests pass **and** its commit has landed.
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
