---
name: loop-automation
description: Stand up a recurring trigger (heartbeat) that surfaces — and optionally acts on — work on a schedule, safely. Use when setting up automated triage, a scheduled PR-review or maintenance job, a "run until done" cadence, or any recurring AI task. Covers when to use GitHub Actions (the real unattended heartbeat) versus in-session CronCreate, and the safety rails an unattended loop needs. Unattended loops make unattended mistakes — this skill is about bounding that.
---

# loop-automation

The heartbeat of a loop: a scheduled trigger that surfaces work without you asking. The hard part is not the scheduling — it is bounding what an unattended run is allowed to do.

## Pick the mechanism (they differ a lot in strength)

| Need | Use |
|---|---|
| Runs when you are away / no live session | **GitHub Actions** scheduled workflow |
| Recurring PR review, triage, or maintenance on a repo | **GitHub Actions** |
| A cadence *within* a live working session (e.g. re-check CI every 20 min) | **CronCreate** (in-session) |
| One-shot reminder later today | **CronCreate** `recurring:false`, or **ScheduleWakeup** |

**GitHub Actions is the only true unattended heartbeat.** `CronCreate` is session-only: it dies when Claude exits, fires only while the REPL is idle, and recurring jobs auto-expire after 7 days (`durable:true` survives restarts but still needs a live session). Do not use `CronCreate` for automation that must run when you are not at the machine.

## GitHub Actions loop — model on what is already here

This repo's `.github/workflows/update-flake-lock.yml` is the template: `schedule:` cron + `workflow_dispatch`, least-privilege permissions, do the work, open a PR (never merge). To build a loop:

1. `on:` a `schedule:` cron (off-peak minute, not `0 0`) **and** `workflow_dispatch` (manual run + kill switch).
2. Minimal `permissions:` — `contents: write`, `pull-requests: write`, nothing more.
3. Run the task: a triage script, or an agent step.
4. Open a PR via `peter-evans/create-pull-request` on an `automation/*` branch. **Never auto-merge.**

## Safety rails (the skill's real content)

Unattended loops make unattended mistakes. Every loop must:

- **Open PRs, never merge.** A human reviews and merges — verification stays on you.
- **Verify between iterations.** Pair with `maker-checker`: a separate agent checks the loop's output before it surfaces.
- **Keep state outside the run.** Progress lives in `loop-state`'s `plan.md`, an issue, or a board — not in the ephemeral run.
- **Bound cost.** Cap iterations and use a cheap model for triage; loops accumulate tokens fast across runs and sub-agents.
- **Least privilege + a kill switch.** Minimal token scope; `workflow_dispatch` plus the ability to disable the workflow.
- **Guard the three risks.** Comprehension debt (review what the loop shipped — see `pr-dependency-review`), cognitive surrender (the loop assists, it does not replace your judgment), false confidence (a smooth loop is not a correct one).

## The loop's shape

heartbeat (schedule) → triage (read CI failures / issues / commits) → isolate (`git-wt` worktree or branch) → maker drafts (`maker-checker`) → checker verifies → open PR + update `plan.md` (`loop-state`) → human reviews and merges.

## Integration

- **maker-checker** — the verification gate between iterations.
- **loop-state** — where the loop records progress between runs.
- **git-wt** — isolate each automated task in its own worktree/branch.
- **pr-dependency-review** — the review job a PR-triage loop runs (it already supports the `GITHUB_ACTIONS` env var).
