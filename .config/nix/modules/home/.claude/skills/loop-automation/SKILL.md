---
name: loop-automation
description: Stand up a recurring trigger (heartbeat) that surfaces — and optionally acts on — work on a schedule, safely. Use when setting up automated triage, a scheduled PR-review or maintenance job, a "run until done" cadence, or any recurring AI task. Covers the two real unattended heartbeats — Claude Code Routines (agentic, cloud) and GitHub Actions (deterministic gate) — versus in-session CronCreate, plus the safety rails an unattended loop needs. Unattended loops make unattended mistakes — this skill is about bounding that.
---

# loop-automation

The heartbeat of a loop: a scheduled trigger that surfaces work without you asking. The hard part is not the scheduling — it is bounding what an unattended run is allowed to do.

## Pick the mechanism

| Need | Use |
|---|---|
| Unattended *agentic* work when you are away (triage, review, fix, refactor) | **Claude Code Routines** (cloud) |
| Deterministic gate: run tests / lint, block PRs on red, scripted maintenance | **GitHub Actions** |
| A cadence *within* a live working session (e.g. re-check CI every 20 min) | **CronCreate** (in-session) |
| One-shot reminder later today | **CronCreate** `recurring:false` |
| An in-session goal that persists across turns until a condition is met | **/goal** (built-in) |
| An in-session "until done" loop on one task (iterate until a completion condition holds) | **ralph-loop** plugin |
| A self-paced in-session loop where the agent picks each next wake-up | **/loop** (ScheduleWakeup) |
| Deterministic multi-agent orchestration inside one session (fan-out, pipelines) | **Workflow** tool — explicit user opt-in only |

Anthropic's own frame for these ("Getting started with loops"): turn-based → goal-based (`/goal`) → time-based (`/loop`, `/schedule`) → proactive (Routines). Pick the simplest type that fits.

There are **two true unattended heartbeats**: Routines (the smart worker — Claude runs natively) and GitHub Actions (the dumb-but-reliable gate). `CronCreate`, `/goal`, `ralph-loop`, `/loop`, and the `Workflow` tool are *not* heartbeats — they are session-scoped. In-session until-done looping comes from `/goal`, `ralph-loop`, or `/loop`; `Workflow` orchestrates multi-agent runs only when the user explicitly opts in. (Verified on Claude Code 2.1.201. Verify mechanisms on the right surface: tools via ToolSearch, CLI built-ins via the commands doc or by typing the command — a tool search can never see a built-in.)

## Claude Code Routines — the agentic heartbeat (primary)

Routines run unattended on Anthropic's cloud, with no live session or laptop needed. Create one via `/schedule` (CLI) or at `claude.ai/code/routines`.

- **Triggers**: cron schedule, HTTP API, or GitHub events (PR / release webhooks). Minimum interval is **1 hour**.
- **Each run** clones the repo into a fresh cloud environment, reads your `CLAUDE.md` and skills, runs the configured prompt, pushes to a new branch, then **destroys the environment**.
- **Best for** the agentic part — the run reads your skills (`plan-state`, `maker-checker`, `pr-dependency-review`) natively, so there is no API to wire up.
- **Critical property — runs are ephemeral; no state persists between them.** Each run starts cold. This is exactly why `plan-state`'s `plan.md` is **committed in the repo**: the cloud box is wiped, but the next run reads the file. The repo *is* the cross-run memory.

## GitHub Actions — the deterministic gate (secondary)

Use Actions for the reliable, non-agentic part: run tests / lint, block a PR on red (the workflow only reports the status; the actual block comes from a branch-protection **required status check**), simple scheduled maintenance. This repo's `.github/workflows/update-flake-lock.yml` is the closest template (it schedules on `0 0 * * *`; for new loops prefer an off-peak minute so runs do not pile onto the top of the hour). To build one:

1. `on:` a `schedule:` cron (off-peak minute, not `0 0`) **and** `workflow_dispatch` (manual run + kill switch).
2. Minimal `permissions:` — least privilege for what the job actually does, not a fixed set: a PR-opening job needs `contents: write` + `pull-requests: write`; a read-only gate that only flags PRs needs `contents: read` (+ `checks: write`). Nothing beyond that.
3. Run the task: a script, or an agent step via the official `anthropics/claude-code-action`.
4. Open a PR via `peter-evans/create-pull-request` on an `automation/*` branch. **Never auto-merge.**

If the work is genuinely agentic, prefer a Routine over wiring an agent into Actions.

## CronCreate — in-session only (not a heartbeat)

`CronCreate` dies when Claude exits, fires only while the REPL is idle, and recurring jobs auto-expire after 7 days (`durable:true` survives restarts but still needs a live session). Use it for a cadence *within* a working session, never for automation that must run when you are away.

## /goal, ralph-loop, /loop, Workflow — in-session "until done" (not heartbeats)

Session-scoped mechanisms for *until-done* rather than *time-based* looping:

- **/goal** (built-in) — `/goal <condition>` keeps Claude working across turns until the condition is met; `/goal clear` stops it early. The most direct until-done engine: give it an objective, checkable condition — e.g. `issue-loop`'s stop predicate ("every issue has a draft PR or a Blocked entry in plan.md").
- **ralph-loop** (plugin) re-feeds one task to the session until its completion condition holds — the same outer-loop role as `/goal`, as a plugin.
- **/loop** (ScheduleWakeup) lets the agent schedule its own next turn, so the cadence adapts to whatever the loop is waiting on.
- **Workflow** (tool) — deterministic multi-agent orchestration (fan-out, pipelines, judge panels) within one session. Runs only on explicit user opt-in — a skill may offer it, never require it.

All die with the session. Any state they need across sessions belongs in `plan-state`'s `plan.md` — same rule as Routines.

## Safety rails (the skill's real content)

Unattended loops make unattended mistakes. Every loop must (the parallelism and worktree rails apply only when a run dispatches parallel subagents):

- **Open PRs, never merge.** A human reviews and merges — verification stays on you.
- **Verify between iterations.** Pair with `maker-checker`: a separate agent checks the loop's output before it surfaces.
- **Keep state outside the run.** Progress lives in `plan-state`'s `plan.md`, an issue, or a board — never in the ephemeral run (Routines wipe theirs every time).
- **Bound cost — parallelism is the trap.** Each parallel sub-agent multiplies token burn; unbounded fan-out has produced four-to-five-figure bills. Cap parallel agents explicitly and use a cheap model for triage.
- **Isolate every subagent in its own worktree.** When the heartbeat fans out one subagent per issue, each works in a dedicated `git-wt` worktree on a distinct branch/path (`issue/<id>`) — so concurrent `git worktree add` never collides and one task's edits never touch another's tree. The whole per-issue chain (analyze → implement → review → PR) shares that one worktree; reclaim merged ones with `git wt -d`.
- **Respect Routines limits.** 1-hour minimum interval; a capped number of routines per day that varies by plan — check current limits in-app rather than assuming.
- **Least privilege + a kill switch.** Minimal token scope; `workflow_dispatch` (Actions) or disabling the routine, so you can always stop it.
- **Guard the three risks.** Comprehension debt (review what the loop shipped — see `pr-dependency-review`), cognitive surrender (the loop assists, it does not replace your judgment), false confidence (a smooth loop is not a correct one).

## The loop's shape

heartbeat (Routine schedule, or Action) → triage (read CI failures / issues / commits) → isolate (`git-wt`: one worktree per fanned-out subagent, distinct branch/path) → maker drafts (`maker-checker`) → checker verifies → open PR + update `plan.md` (`plan-state`) → human reviews and merges.

## Integration

- **maker-checker** — the verification gate between iterations.
- **plan-state** — `plan.md` is the cross-run memory a fresh (ephemeral) Routine reads to resume.
- **git-wt** — one worktree per fanned-out subagent, on a distinct branch/path per task so parallel `git worktree add` cannot collide.
- **issue-loop** — the concrete per-issue body this heartbeat runs: it already implements the worktree-per-issue isolation (one worktree per issue → draft PR), so schedule it rather than re-deriving the procedure.
- **pr-dependency-review** — the lowest-risk first heartbeat is a scheduled, read-only run of this review on open PRs (it only comments; supports the `GITHUB_ACTIONS` env var).
