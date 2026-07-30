# Spikes (plan phase only)

Read this before dispatching a spike.

When a lagging axis — usually *feasibility* or *risk* — cannot be scored honestly without
evidence ("will this approach be fast enough / fit the existing API?"), spawn 1–N spike
subagents (`Agent` with `isolation: "worktree"`), each in a **throwaway** worktree, to
build the smallest prototype that answers the question and measure it against a stated
metric. Compare the spikes, fold the winning **conclusion** into the plan, and discard the
spike code — only the conclusion survives. Cap the number of spikes (`MAX_SPIKES`) so this
does not balloon. Which axes may trigger a spike is explicit: an axis drives one when it
is marked `spikes: true` (defaults: *feasibility*, *risk*) — an issue-specific axis opts
in the same way.

Spikes are **plan-phase only** — they settle *pre-code* unknowns. A KPI that is only
measurable once code exists (perf delta, mutation score, coverage) is measured by the
impl-phase reviewer itself — it runs the tests/benchmark as part of its review — not by a
spike. So a perf axis spikes in the plan phase to set a baseline/target, then the impl-phase
performance reviewer measures the real change against that target.
