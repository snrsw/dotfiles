# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml",
# ]
# ///
"""Run the eval matrix: variants × prompts × seeds via subscription `claude -p`.

Output: one jsonl row per (variant, rule_id, prompt_id, target, seed).
Resumable: re-running skips rows already present in raw.jsonl.

CLI flag verified against Claude Code: `--system-prompt-file <path>` cleanly
overrides both the default Claude Code system prompt and any auto-discovered
~/.claude/CLAUDE.md, without needing --bare (which would require API-key auth
and break the subscription cost model).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class RunSpec:
    """One scheduled call to `claude -p`."""

    variant: str
    rule_id: str
    prompt_id: str
    prompt_text: str
    target: str  # "on" | "off"
    seed: int

    @property
    def key(self) -> tuple[str, str, str, str, int]:
        return (self.variant, self.rule_id, self.prompt_id, self.target, self.seed)


@dataclass
class RunResult:
    """jsonl row written to raw.jsonl."""

    spec: RunSpec
    response: str
    duration_s: float
    total_tokens: int | None
    error: str | None


def _load_yaml_list(path: Path) -> list[dict]:
    """Load a YAML file expected to contain a list of dicts; empty list if missing."""
    if not path.exists():
        return []
    with path.open() as f:
        data = yaml.safe_load(f) or []
    if not isinstance(data, list):
        raise ValueError(f"{path}: expected a YAML list, got {type(data).__name__}")
    return data


def load_prompts(prompts_dir: Path, rule_id: str) -> tuple[list[dict], list[dict]]:
    """Read prompts/<rule_id>.yaml and split by `expected_fire`.

    The file is a YAML list of `{id, text, expected_fire?: bool, note?}`.
    `expected_fire` defaults to True (most prompts target the rule firing).
    For rules that fire every turn, omit any `expected_fire: false` entries —
    the off-target list will be empty.

    Falls back to the older two-file layout (`<rule_id>/on_target.yaml` +
    `<rule_id>/off_target.yaml`) if the single-file form is missing, so old
    workspaces still work.
    """
    flat = prompts_dir / f"{rule_id}.yaml"
    if flat.exists():
        prompts = _load_yaml_list(flat)
        on = [p for p in prompts if p.get("expected_fire", True)]
        off = [p for p in prompts if not p.get("expected_fire", True)]
        return on, off

    # Legacy two-file layout fallback
    on = _load_yaml_list(prompts_dir / rule_id / "on_target.yaml")
    off = _load_yaml_list(prompts_dir / rule_id / "off_target.yaml")
    return on, off


def build_specs(
    rules_yaml: Path,
    prompts_dir: Path,
    variants_dir: Path,
    seeds: int,
) -> list[RunSpec]:
    """Cartesian product of variants × prompts × seeds for each rule.

    A prompt under rule X runs against `full`, `empty`, and `ablated_X` (when
    that variant exists). Cross-rule ablations (rule X under ablated_Y) are
    skipped — they answer a different question and would multiply the matrix.
    """
    with rules_yaml.open() as f:
        rules = yaml.safe_load(f) or []

    available_variants = {p.stem for p in variants_dir.glob("*.md")}

    specs: list[RunSpec] = []
    for rule in rules:
        rid = rule["id"]
        on, off = load_prompts(prompts_dir, rid)

        rule_variants = ["full", "empty"]
        ablated = f"ablated_{rid}"
        if ablated in available_variants:
            rule_variants.append(ablated)

        for variant in rule_variants:
            for seed in range(1, seeds + 1):
                for target_label, prompts in (("on", on), ("off", off)):
                    for prompt in prompts:
                        specs.append(
                            RunSpec(
                                variant=variant,
                                rule_id=rid,
                                prompt_id=prompt["id"],
                                prompt_text=prompt["text"],
                                target=target_label,
                                seed=seed,
                            )
                        )
    return specs


def load_existing_keys(raw_jsonl: Path) -> set[tuple[str, str, str, str, int]]:
    """Return keys of rows already present in raw.jsonl. Used for resumability."""
    if not raw_jsonl.exists():
        return set()
    keys: set[tuple[str, str, str, str, int]] = set()
    with raw_jsonl.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
                keys.add((row["variant"], row["rule_id"], row["prompt_id"], row["target"], row["seed"]))
            except (json.JSONDecodeError, KeyError):
                continue
    return keys


def _result_to_jsonl(result: RunResult) -> str:
    return json.dumps(
        {
            "variant": result.spec.variant,
            "rule_id": result.spec.rule_id,
            "prompt_id": result.spec.prompt_id,
            "prompt_text": result.spec.prompt_text,
            "target": result.spec.target,
            "seed": result.spec.seed,
            "response": result.response,
            "duration_s": result.duration_s,
            "total_tokens": result.total_tokens,
            "error": result.error,
        }
    )


async def run_one(
    spec: RunSpec,
    variant_path: Path,
    semaphore: asyncio.Semaphore,
) -> RunResult:
    """Invoke `claude -p` once with the variant injected via --system-prompt-file."""
    async with semaphore:
        start = time.time()
        try:
            proc = await asyncio.create_subprocess_exec(
                "claude",
                "-p",
                "--system-prompt-file", str(variant_path),
                "--output-format", "json",
                "--no-session-persistence",
                spec.prompt_text,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
        except OSError as e:
            return RunResult(spec, "", time.time() - start, None, f"OSError: {e}")

        duration = time.time() - start
        if proc.returncode != 0:
            return RunResult(
                spec,
                "",
                duration,
                None,
                f"exit {proc.returncode}: {stderr.decode(errors='replace')[:500]}",
            )

        try:
            data = json.loads(stdout.decode(errors="replace"))
        except json.JSONDecodeError as e:
            return RunResult(spec, stdout.decode(errors="replace"), duration, None, f"JSONDecodeError: {e}")

        usage = data.get("usage") or {}
        total = (usage.get("input_tokens") or 0) + (usage.get("output_tokens") or 0)
        err = None
        if data.get("is_error"):
            err = data.get("subtype") or "claude_error"

        return RunResult(
            spec=spec,
            response=data.get("result", ""),
            duration_s=duration,
            total_tokens=total or None,
            error=err,
        )


async def run_matrix(
    rules_yaml: Path,
    prompts_dir: Path,
    variants_dir: Path,
    workspace: Path,
    seeds: int,
    concurrency: int,
) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    raw_jsonl = workspace / "raw.jsonl"

    specs = build_specs(rules_yaml, prompts_dir, variants_dir, seeds)
    existing = load_existing_keys(raw_jsonl)
    pending = [s for s in specs if s.key not in existing]

    print(
        f"total specs: {len(specs)}; pending: {len(pending)}; "
        f"skipping (already done): {len(specs) - len(pending)}",
        file=sys.stderr,
    )
    if not pending:
        return

    semaphore = asyncio.Semaphore(concurrency)
    write_lock = asyncio.Lock()

    with raw_jsonl.open("a") as out:

        async def run_and_write(spec: RunSpec) -> None:
            variant_path = variants_dir / f"{spec.variant}.md"
            result = await run_one(spec, variant_path, semaphore)
            line = _result_to_jsonl(result)
            async with write_lock:
                out.write(line + "\n")
                out.flush()
            status = "ok" if result.error is None else f"err: {result.error[:60]}"
            print(
                f"  [{spec.variant}/{spec.rule_id}/{spec.prompt_id}/seed={spec.seed}/{spec.target}] "
                f"{result.duration_s:.1f}s {status}",
                file=sys.stderr,
            )

        await asyncio.gather(*(run_and_write(s) for s in pending))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rules", type=Path, required=True)
    parser.add_argument("--prompts-dir", type=Path, required=True)
    parser.add_argument("--variants-dir", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args()

    asyncio.run(
        run_matrix(
            args.rules,
            args.prompts_dir,
            args.variants_dir,
            args.workspace,
            args.seeds,
            args.concurrency,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
