# Scored verification loop

Read this when a document is high-stakes and needs a verified result. This
instantiates the same scored-review protocol as `issue-resolver` (fresh
reviewers, parse-one-json-block with one re-ask, refute-before-fix, ≥ 80
threshold, MAX_ROUNDS = 3) — keep the shared constants in sync when editing
either.

Roles are separated so no agent grades its own work: the main session orchestrates; a **fresh subagent** reviews each round (never a previous reviewer, never the reviser); a **separate subagent** revises. The reviewer never fixes, and the reviser never scores.

Each round:

1. **Review.** Dispatch a fresh reviewer with the document plus `document-style`'s SKILL.md — the reviewer needs its "Checklist for Revision", which is the scoring rubric and does not live in this file. It scores EVERY checklist item and ends its reply with exactly one fenced json block:

   ```json
   {"policies": [{"policy": "<checklist item>", "score": 0-100, "confidence": 0-1,
     "reason": "...",
     "issues": [{"issue": "...", "quote": "<verbatim offending text>",
                 "severity": "critical|high|medium|low", "confidence": 0-1, "fix": "..."}]}]}
   ```

   Parse the final fenced json block of the reply. On parse failure, re-ask once ("return only the json block"); on a second failure, treat the round as failed and stop.

2. **Anchor the scores — no vibes.** Each policy starts at 100 and deducts per issue: critical −30, high −15, medium −8, low −3. A reviewer that deviates states why in `reason`. This makes ≥ 80 mean something concrete: no critical/high issue, at most minor nits.

3. **Gates a score cannot buy back.** In a revision, any lost or altered technical fact is an automatic `critical` issue, whatever the style quality. The loop exits only when BOTH hold: every policy scores ≥ 80 AND no confirmed critical/high issue remains.

4. **Refute before fixing.** For each critical/high issue with confidence < 0.7, dispatch a fresh subagent to REFUTE it ("assume this may be wrong; default to not confirmed"). Only confirmed issues drive fixes — this stops the loop from chasing a hallucinated issue.

5. **Fix and re-review.** A reviser subagent applies the remaining issues, locating each by its `quote` and preserving every technical fact. The next round starts with a FRESH reviewer.

**MAX_ROUNDS = 3.** If the cap is hit with a policy still below 80, stop and report the residual policies and issues to the user instead of looping — a stuck policy is a decision for the user, not fuel for iteration.
