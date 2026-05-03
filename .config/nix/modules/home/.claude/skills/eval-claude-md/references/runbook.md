# Full-eval runbook

Exact commands per phase. Read this when the user has asked for the full quantitative eval (not just operationalization or audit). Workspace lives in `${TMPDIR:-/tmp}/eval-claude-md/<timestamp>/`.

## Layout

```
$WORKSPACE/
├── rules.yaml                  # rule registry: id, source, text, triggers, rubric
├── prompts/<rule_id>.yaml      # one file per rule, list of {id, text, expected_fire, note?}
├── variants/
│   ├── full.md                 # target verbatim
│   ├── empty.md                # placeholder string (NOT literally empty)
│   └── ablated_<rule_id>.md    # full minus the named rule
├── raw.jsonl                   # output of run_eval.py
├── graded.jsonl                # output of judge.py
└── report.md                   # output of analyze.py
```

## Phase 1 — Extract

```bash
WORKSPACE="${TMPDIR:-/tmp}/eval-claude-md/$(date +%Y%m%dT%H%M%S)"
mkdir -p "$WORKSPACE/prompts" "$WORKSPACE/variants"

uv run scripts/extract_rules.py ~/.claude/CLAUDE.md --out "$WORKSPACE/rules.yaml"
```

User then fills in `triggers` and `rubric` for each rule (see `methodology.md`).

## Phase 2 — Author prompts

One file per rule at `prompts/<rule_id>.yaml`. Schema:

```yaml
- id: ot_001
  text: "..."
  expected_fire: true     # rule should fire here (on-target)
  note: "optional"
- id: nt_001
  text: "..."
  expected_fire: false    # rule should NOT fire here (off-target)
```

`expected_fire` defaults to `true`. For rules that fire every turn (no meaningful off-target set), omit all `expected_fire: false` entries.

Aim for 8–10 prompts per rule. Off-target prompts must be plausible adjacent — see `methodology.md` "Off-target prompt design".

## Phase 3 — Build variants

```bash
cp ~/.claude/CLAUDE.md "$WORKSPACE/variants/full.md"
echo "(no system prompt)" > "$WORKSPACE/variants/empty.md"   # MUST be non-empty
```

### Section-level ablation

Use when the rule corresponds to a whole H1 section (one rule per heading):

```bash
# Drops the entire COMMUNICATION section
awk 'BEGIN{skip=0} /^# COMMUNICATION/{skip=1; next} /^# / && skip{skip=0} skip==0{print}' \
    ~/.claude/CLAUDE.md > "$WORKSPACE/variants/ablated_communication.md"
```

### Paragraph-level (sub-rule) ablation

Use when several distinct directives share one H1 section and you split them into separate `rules.yaml` entries (see SKILL.md Phase 2). The ablation should remove just the target paragraph or bullet — preserving the rest of the section, since they're separate rules:

```bash
# Drop the english_rewrite paragraph from COMMUNICATION but keep the rest.
# Match by the directive's first line and remove until the next blank line.
python3 - <<'PY' > "$WORKSPACE/variants/ablated_english_rewrite.md"
from pathlib import Path
src = Path("$HOME/.claude/CLAUDE.md").read_text()
target = "When the user writes a prompt, rewrite it in natural English"
out_lines = []
skip = False
for line in src.splitlines():
    if line.startswith(target):
        skip = True
        continue
    if skip:
        if line.strip() == "":
            skip = False
        continue
    out_lines.append(line)
print("\n".join(out_lines))
PY
```

Adjust the `target` substring to match the first line of whatever paragraph you're ablating. The recipe relies on the convention that paragraphs in CLAUDE.md are separated by blank lines.

### Why `--system-prompt-file` works under subscription

The `--system-prompt-file` flag is verified to override both Claude Code's default system prompt and any auto-discovered `~/.claude/CLAUDE.md`. It does not require `--bare` (which would force API-key auth and break subscription billing). The flag is hidden from the main `claude --help` output but documented in the `--bare` description.

## Phase 4 — Run

```bash
uv run scripts/run_eval.py \
  --rules    "$WORKSPACE/rules.yaml" \
  --prompts-dir "$WORKSPACE/prompts" \
  --variants-dir "$WORKSPACE/variants" \
  --workspace "$WORKSPACE" \
  --seeds 3 \
  --concurrency 4
```

Resumable: re-running skips rows already in `raw.jsonl`. On 429s, lower `--concurrency` and rerun.

## Phase 5 — Grade

```bash
uv run scripts/judge.py \
  --raw  "$WORKSPACE/raw.jsonl" \
  --rules "$WORKSPACE/rules.yaml" \
  --out  "$WORKSPACE/graded.jsonl" \
  --concurrency 4
```

Before trusting metrics, hand-grade ~10 rows from `graded.jsonl` against the responses in `raw.jsonl`. If your verdicts disagree with the judge's on more than ~1 in 10, the rubric is too fuzzy — tighten it and regrade.

## Phase 6 — Analyze

```bash
uv run scripts/analyze.py \
  --graded "$WORKSPACE/graded.jsonl" \
  --rules  "$WORKSPACE/rules.yaml" \
  --out    "$WORKSPACE/report.md"
```

`report.md` contains a per-rule scorecard with recommendations (`keep` / `rewrite` / `delete` / `narrow_scope`).

## Phase 7 — Propose edits

Read `report.md`. For each rule with a non-`keep` recommendation, draft a concrete edit (text diff, not a description). Show all edits as one batch. **Wait for explicit user approval before applying.** After applying, suggest re-running phases 4–6 on just the changed rules to confirm metrics moved.
