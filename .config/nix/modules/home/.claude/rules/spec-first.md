# Spec-First for Vague Requests

When a request is ambiguous — it names a goal loosely, or does not say what the output is for — do NOT start designing or implementing from guesses. Recover the purpose first, then explore the spec by proposing, not interrogating.

## Step 1: Elicit the purpose (only if missing)

A request has a purpose when it answers: who is this for, and what should the output enable?

If that is missing:

1. Infer 2-3 plausible purposes from the repository, recent commits, and the conversation.
2. Ask ONE question with AskUserQuestion: "What is this for?" — present the inferred purposes as options, recommendation first, each noting what it would change about the design.
3. Restate the request with the confirmed purpose before continuing.

Skip this step when the request already states its intent, or names an exact file/change where the intent is obvious.

## Step 2: Propose, don't interrogate

This overrides the question-first ordering of any imported design/brainstorming skill (user rules take precedence over plugin skills):

- After exploring context, present your best-guess interpretation as a concrete draft spec with assumptions marked — BEFORE asking further questions.
- Then ask at most one batch of questions, only for decisions the draft cannot settle, each with options and a recommended default.
- Never return a bare list of questions.

## How the steps compose

- When the purpose is missing, your FIRST response contains both: the draft spec (built on your recommended purpose) and the single batch of questions. "One batch" means one AskUserQuestion call (one turn) — it carries the purpose question plus any decisions the draft cannot settle, each with its own options. Do not split the spec and the questions across turns.
- Mark assumptions inline, one per line: `[ASSUMPTION] The reader is an operator at a terminal, not a log pipeline.`
- If an unknown would change the architecture (deployment topology, data volume, tenancy), surface it as a question with a conservative default — do not bury it as an assumption.
