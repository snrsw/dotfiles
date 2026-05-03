# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml",
# ]
# ///
"""Grade responses against per-rule rubrics via `claude -p --output-format json`.

Input:  raw.jsonl from run_eval.py
Output: graded.jsonl (raw fields + `rubric: {<check_id>: bool, ...}`)

The judge is the same Claude reachable via `claude -p`. Same-model bias is
real — hand-grade a 10–20 row sample and confirm ≥90% agreement with the
judge before trusting downstream metrics.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import yaml


JUDGE_PROMPT_TEMPLATE = """\
You are grading a model response against a rubric. Reply with JSON only — no
prose, no markdown fences, no explanation. Just the JSON object.

# Rule under test
{rule_text}

# Triggers (when this rule should fire)
{triggers}

# Rubric checks
For each check below, decide whether the model's response satisfies it. Output
one boolean per check_id.

{rubric_block}

# Original user prompt (the model was responding to this)
{user_prompt}

# Model response (judge this)
{response}

# Output format
A single JSON object. Example shape (with your booleans, not these placeholders):
{example_output}
"""


def build_judge_prompt(row: dict, rule: dict) -> str:
    rubric = rule.get("rubric") or []
    if not rubric:
        raise ValueError(f"rule {rule.get('id')!r} has no rubric checks")
    rubric_block = "\n".join(f"- `{c['id']}`: {c['check'].strip()}" for c in rubric)
    example = "{" + ", ".join(f'"{c["id"]}": true' for c in rubric) + "}"
    return JUDGE_PROMPT_TEMPLATE.format(
        rule_text=rule.get("text", "").strip(),
        triggers=rule.get("triggers", "").strip() or "(no triggers specified)",
        rubric_block=rubric_block,
        user_prompt=(row.get("prompt_text") or "").strip(),
        response=(row.get("response") or "").strip(),
        example_output=example,
    )


def _strip_code_fence(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        # Drop opening fence (and optional language tag), then trailing fence.
        first_nl = s.find("\n")
        if first_nl == -1:
            return s
        s = s[first_nl + 1 :]
        if s.endswith("```"):
            s = s[:-3]
        s = s.strip()
    return s


def parse_judge_output(raw_stdout: str, expected_keys: list[str]) -> dict[str, bool]:
    """Extract the rubric verdict from `claude -p --output-format json` stdout.

    Outer envelope: claude's JSON with a `result` field carrying the model's
    text. The model is asked to return a JSON object as that text. Some
    responses arrive wrapped in markdown fences despite our instruction; we
    strip those defensively.
    """
    outer = json.loads(raw_stdout)
    result_text = outer.get("result", "")
    inner_text = _strip_code_fence(result_text)
    verdict = json.loads(inner_text)
    if not isinstance(verdict, dict):
        raise ValueError(f"expected dict, got {type(verdict).__name__}")
    out: dict[str, bool] = {}
    for key in expected_keys:
        if key not in verdict:
            raise ValueError(f"missing rubric key: {key!r}")
        out[key] = bool(verdict[key])
    return out


async def grade_one(
    row: dict,
    rule: dict,
    semaphore: asyncio.Semaphore,
    max_retries: int = 3,
) -> dict:
    """Build the judge prompt, call claude -p, parse, return graded row.

    On parse failure, retry up to `max_retries` times with exponential backoff.
    After exhausting retries, return the row with `rubric: None` and a
    `judge_error` field so it shows up as ungraded instead of being dropped.
    """
    judge_prompt = build_judge_prompt(row, rule)
    expected_keys = [c["id"] for c in rule.get("rubric") or []]

    last_error: str | None = None
    for attempt in range(max_retries):
        async with semaphore:
            try:
                proc = await asyncio.create_subprocess_exec(
                    "claude",
                    "-p",
                    "--output-format", "json",
                    "--no-session-persistence",
                    judge_prompt,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()
            except OSError as e:
                last_error = f"OSError: {e}"
                continue

            if proc.returncode != 0:
                last_error = f"exit {proc.returncode}: {stderr.decode(errors='replace')[:200]}"
            else:
                try:
                    verdict = parse_judge_output(stdout.decode(errors="replace"), expected_keys)
                    return {**row, "rubric": verdict, "judge_error": None, "judge_attempts": attempt + 1}
                except (json.JSONDecodeError, ValueError) as e:
                    last_error = f"{type(e).__name__}: {e}"

        if attempt < max_retries - 1:
            await asyncio.sleep(2**attempt)

    return {**row, "rubric": None, "judge_error": last_error, "judge_attempts": max_retries}


async def grade_all(
    raw_jsonl: Path,
    rules_yaml: Path,
    out_jsonl: Path,
    concurrency: int,
) -> None:
    with rules_yaml.open() as f:
        rules = yaml.safe_load(f) or []
    rule_by_id = {r["id"]: r for r in rules}

    rows: list[dict] = []
    with raw_jsonl.open() as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    pending = [r for r in rows if not r.get("error")]
    pre_errored = [r for r in rows if r.get("error")]
    print(
        f"grading {len(pending)} rows ({len(pre_errored)} pre-errored will be passed through)",
        file=sys.stderr,
    )

    semaphore = asyncio.Semaphore(concurrency)
    write_lock = asyncio.Lock()

    with out_jsonl.open("w") as out:

        async def grade_and_write(row: dict) -> None:
            rule = rule_by_id.get(row["rule_id"])
            if rule is None:
                graded = {**row, "rubric": None, "judge_error": f"unknown rule: {row['rule_id']!r}"}
            else:
                graded = await grade_one(row, rule, semaphore)
            async with write_lock:
                out.write(json.dumps(graded) + "\n")
                out.flush()
            verdict = (
                "ungraded"
                if graded.get("rubric") is None
                else "/".join(f"{k}={v}" for k, v in graded["rubric"].items())
            )
            print(
                f"  [{row['variant']}/{row['rule_id']}/{row['prompt_id']}/seed={row['seed']}/{row['target']}] {verdict}",
                file=sys.stderr,
            )

        await asyncio.gather(*(grade_and_write(r) for r in pending))

        # Pass-through pre-errored rows so downstream sees the full matrix.
        for row in pre_errored:
            out.write(json.dumps({**row, "rubric": None, "judge_error": "skipped: upstream error"}) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True, help="raw.jsonl from run_eval.py")
    parser.add_argument("--rules", type=Path, required=True, help="rules.yaml")
    parser.add_argument("--out", type=Path, required=True, help="path to write graded.jsonl")
    parser.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args()

    asyncio.run(grade_all(args.raw, args.rules, args.out, args.concurrency))
    return 0


if __name__ == "__main__":
    sys.exit(main())
