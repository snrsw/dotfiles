# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Parse a CLAUDE.md (or any markdown rules file) into a draft rules.yaml.

A "rule" corresponds to one H1 (`# HEADING`) section. The script extracts the
heading and body verbatim. Triggers and rubric are left blank — the user fills
those in with help from references/methodology.md.

Stdlib only — no PyYAML dependency on the write path. Run with
`uv run scripts/extract_rules.py …` for consistency with the other scripts.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def slugify(heading: str) -> str:
    """Lowercase + non-alnum to underscore. `# COMMUNICATION` -> `communication`."""
    s = heading.strip().lower()
    s = _NON_ALNUM.sub("_", s)
    return s.strip("_")


def split_into_rules(markdown_text: str) -> list[tuple[str, str]]:
    """Split a markdown file into (heading, body) pairs at H1 boundaries.

    Returns one pair per `# HEADING` section. Body excludes the heading line and
    is stripped of leading/trailing whitespace. Content before the first H1 is
    discarded.
    """
    pairs: list[tuple[str, str]] = []
    current_heading: str | None = None
    current_body: list[str] = []

    for line in markdown_text.splitlines():
        is_h1 = line.startswith("# ") and not line.startswith("## ")
        if is_h1:
            if current_heading is not None:
                pairs.append((current_heading, "\n".join(current_body).strip()))
            current_heading = line[2:].strip()
            current_body = []
        elif current_heading is not None:
            current_body.append(line)

    if current_heading is not None:
        pairs.append((current_heading, "\n".join(current_body).strip()))

    return pairs


def extract_rules(claude_md_path: Path) -> list[dict]:
    """Read a markdown file and return rule skeleton dicts.

    Each dict:
        id:       slugified heading
        source:   `<file_path> § <heading>`
        text:     verbatim body
        triggers: ""        (user fills)
        rubric:   []        (user fills)
    """
    text = claude_md_path.read_text()
    pairs = split_into_rules(text)
    return [
        {
            "id": slugify(heading),
            "source": f"{claude_md_path} § {heading}",
            "text": body,
            "triggers": "",
            "rubric": [],
        }
        for heading, body in pairs
    ]


def render_yaml(rules: list[dict]) -> str:
    """Hand-roll the YAML for the rule skeleton shape.

    The rule shape is fixed and known, so a few lines of string formatting
    avoids depending on PyYAML for the write path. Block-scalar (`|`) is used
    for `text` so multi-line bodies stay readable. Strings that might contain
    YAML-special characters are quoted via `json.dumps`, since JSON strings
    are valid YAML 1.2.
    """
    out: list[str] = []
    for rule in rules:
        out.append(f"- id: {rule['id']}")
        out.append(f"  source: {json.dumps(rule['source'])}")
        if rule["text"]:
            out.append("  text: |-")  # |- strips the trailing newline so round-tripping is exact
            for line in rule["text"].splitlines():
                out.append(f"    {line}")
        else:
            out.append('  text: ""')
        out.append('  triggers: ""')
        out.append("  rubric: []")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path, help="Path to CLAUDE.md or rules markdown")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output path for the draft rules.yaml (default: stdout)",
    )
    args = parser.parse_args()

    if not args.target.exists():
        print(f"error: target file not found: {args.target}", file=sys.stderr)
        return 2

    rules = extract_rules(args.target)
    yaml_text = render_yaml(rules)

    if args.out:
        args.out.write_text(yaml_text)
        print(f"wrote {len(rules)} rule(s) to {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(yaml_text)

    return 0


if __name__ == "__main__":
    sys.exit(main())
