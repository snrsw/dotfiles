# AI-generated-PR checks

Agent PRs fail in characteristic ways. These checks are detectable from a diff
and target the failure modes the empirical literature reports (GitHub's agent-PR
review guide; MSR'26 agentic-PR studies). Heuristic — each is a prompt to look,
not a verdict.

## Scope wider than the task
Flag when the diff touches 5+ unrelated files, or its purpose can't be stated in
one sentence. Agentic PRs spend ~39% of commits on explicit refactoring plus
~54% on incidental cleanup, so scope creep is the norm — ask for a smaller PR
rather than reviewing an over-reaching one.

## CI weakened (blocker)
Treat as high-risk any diff that:
- removes, renames, or skips tests (`@pytest.mark.skip`, `xfail`, deleted `test_` fns)
- lowers a coverage threshold / `fail_under`
- gates a workflow so it no longer runs on PRs or forks, or adds conditions that
  skip CI steps
Not-merged agent PRs disproportionately weaken or fail CI. A green check on a
weakened pipeline is false reassurance.

## Hallucinated correctness
Agent code often compiles and passes the existing tests but is functionally wrong
(off-by-one, a missing permission check on an untested branch, unconsidered edge
cases). For each changed public function, require a test that FAILS on the
pre-change behavior — a passing existing suite does not prove the change correct.

## Reinvented utilities
New code duplicating an existing module it could have imported. Check whether a
module with the same responsibility was NOT imported. `containment_detect.py`'s
`misplaced` findings feed this.

## Phantom / undeclared imports
A newly added import whose top-level package is not stdlib, not first-party, and
not in the manifest (pyproject / requirements). Catches hallucinated packages
(slopsquatting) and undeclared dependencies. Rare on real agent PRs — they add a
dependency in ~1% of PRs — but cheap to check and severe when it hits.
`containment_detect.py` surfaces these as `phantom_imports`; verify the survivors
against the package registry (a hallucinated name often resembles a real one).

## Unnecessary abstraction / dead edges
New module with fan-in of exactly 1; unused imports; dead edges introduced.
`diff_deps.py --fan-in-threshold` flags the *opposite* end — high fan-in coupling
hotspots — so it will **not** surface a fan-in-1 node. Read single-caller nodes
straight off the normalized head graph: a newly added `to` node reached by exactly
one distinct `from` edge is the fan-in-1 abstraction.

## Comprehension debt (loop-generated code)
The most dangerous failure of an automated loop is code that merges without
anyone understanding it. Before approving a loop- or agent-generated PR, require
that a human can state, in one plain sentence per changed behavior, what changed
and why. If the diff cannot be summarized that way — if the only justification is
"the agent did it and tests pass" — that is comprehension debt: do not merge; ask
for a smaller or explained PR. A green pipeline proves the code runs, not that
anyone understands it.
