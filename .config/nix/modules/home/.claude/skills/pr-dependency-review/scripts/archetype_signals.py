#!/usr/bin/env python3
"""Extract non-structural archetype signals from a unified diff.

The structural path has diff_deps.py; this is its counterpart for the
behavioral / state-machine / data-flow archetypes. It runs the grep recipes in
references/visualization-archetypes.md over a diff and emits structured findings
(plus optional Mermaid scaffolds), turning "read the whole PR" into "review a
candidate list, then fill the template".

Heuristic, not a type checker: it surfaces candidates to confirm, not ground
truth. Static — it cannot see runtime atomicity, dynamic dispatch, or whether a
scrubber actually covers a sink.

Usage:
  git diff BASE HEAD | archetype_signals.py [--archetype all] [--mermaid]
  archetype_signals.py --diff-file pr.diff --archetype dataflow --mermaid
"""
import argparse
import json
import re
import sys

# --- behavioral / temporal -------------------------------------------------
GUARD_READ = re.compile(
    r"\.query\(|\.first\(\)|\.get\(|AsyncResult|\bget_[a-z_]+\(|\bis_[a-z_]+\(",
)
ACT = re.compile(
    r"\.delay\(|\.apply_async\(|\.commit\(\)|\.status\s*=|_task_id\s*=",
)
ATOMICITY = re.compile(
    r"with_for_update|FOR UPDATE|select_for_update|\bSETNX\b|setnx|"
    r"Lock\(|\.lock\(|advisory_lock|nx=True",
    re.IGNORECASE,
)

# --- state-machine ---------------------------------------------------------
# assignment only — exclude ``==`` / ``!=`` / ``<=`` comparisons
STATUS_ASSIGN = re.compile(
    r"(\w+)\.(?:status|state)\s*(?<![=!<>])=(?!=)\s*(.+?)\s*(?:#.*)?$")
STATE_TOKEN = re.compile(r"\b([A-Z][A-Z0-9_]{2,})\b")

# --- data-flow -------------------------------------------------------------
SOURCE = re.compile(
    r"\b(access_token|refresh_token|client_secret|code_verifier|client_id|"
    r"api_key|password|secret|private_key|authorization)\b|Bearer\b",
    re.IGNORECASE,
)
SINKS = [
    ("traceback", re.compile(r"logger\.exception\(|\bexc_info\s*=|\bstack_info\s*=")),
    ("log", re.compile(r"\blog(?:ger|ging)?\.(?:error|warning|info|debug)\(")),
    ("print", re.compile(r"\bprint\(")),
    ("raise_fstring", re.compile(r"\braise\b.*f[\"']")),
    ("structured_extra", re.compile(r"\bextra\s*=\s*\{|\bextra\s*=\s*dict\(")),
    ("db_to_ui", re.compile(r"\.last_error\s*=|\.message\s*=")),
    ("sentry", re.compile(r"capture_(?:message|exception)\(")),
]
# sinks where the secret form is hard to scrub (flagged regardless of source hit)
HIGH_RISK_SINKS = {"traceback"}


def parse_diff(text):
    """Return [{path, added:[(lineno,text)], removed:[(lineno,text)]}]."""
    files, cur = [], None
    new_no = old_no = 0
    for line in text.splitlines():
        if line.startswith("+++ "):
            path = line[4:].strip()
            path = path[2:] if path[:2] in ("b/", "a/") else path
            cur = {"path": path, "added": [], "removed": []}
            if path != "/dev/null":
                files.append(cur)
            continue
        if line.startswith("--- ") or line.startswith("diff "):
            continue
        m = re.match(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
        if m:
            old_no, new_no = int(m.group(1)), int(m.group(2))
            continue
        if cur is None:
            continue
        if line.startswith("+"):
            cur["added"].append((new_no, line[1:]))
            new_no += 1
        elif line.startswith("-"):
            cur["removed"].append((old_no, line[1:]))
            old_no += 1
        else:
            new_no += 1
            old_no += 1
    return files


def behavioral_signals(files):
    out = []
    for f in files:
        guards = [{"line": n, "text": t.strip()}
                  for n, t in f["added"] if GUARD_READ.search(t)]
        acts = [{"line": n, "text": t.strip()}
                for n, t in f["added"] if ACT.search(t)]
        has_atomicity = any(ATOMICITY.search(t) for _, t in f["added"])
        if guards and acts:
            out.append({
                "file": f["path"],
                "guard_reads": guards,
                "acts": acts,
                "atomicity_in_added": has_atomicity,
                "verdict": ("guarded" if has_atomicity
                            else "check-then-act with no atomicity primitive — "
                                 "candidate race"),
            })
    return out


def _states_in(text):
    return set(STATE_TOKEN.findall(text))


def state_signals(files):
    added, removed, states = [], [], set()
    for f in files:
        for n, t in f["added"]:
            if t.strip().startswith("#"):  # skip comments describing code
                continue
            m = STATUS_ASSIGN.search(t)
            if m:
                added.append({"file": f["path"], "line": n,
                              "target": m.group(2).strip(), "text": t.strip()})
                states |= _states_in(m.group(2))
        for n, t in f["removed"]:
            if t.strip().startswith("#"):
                continue
            m = STATUS_ASSIGN.search(t)
            if m:
                removed.append({"file": f["path"], "line": n,
                                "target": m.group(2).strip(), "text": t.strip()})
                states |= _states_in(m.group(2))
    return {"states": sorted(states),
            "added_transitions": added, "removed_transitions": removed}


def dataflow_signals(files):
    hits, sources = [], set()
    for f in files:
        for n, t in f["added"]:
            src = SOURCE.search(t)
            if src:
                sources.add(src.group(0).lower())
            for kind, rx in SINKS:
                if rx.search(t):
                    hits.append({
                        "file": f["path"], "line": n, "sink": kind,
                        "source_on_line": bool(src),
                        "high_risk": kind in HIGH_RISK_SINKS,
                        "text": t.strip(),
                    })
    return {"sinks": hits, "sources_seen": sorted(sources)}


def mermaid(beh, st, df):
    out = {}
    if beh:
        out["behavioral"] = (
            "sequenceDiagram\n"
            "    participant A as Caller A\n"
            "    participant S as shared state\n"
            "    participant B as Caller B\n"
            "    A->>S: read / check\n    B->>S: read / check\n"
            "    Note over A,B: both pass the guard\n"
            "    A->>S: write\n    B->>S: write (unguarded -> conflict)")
    if st["added_transitions"] or st["removed_transitions"]:
        lines = ["stateDiagram-v2"]
        for tr in st["added_transitions"]:
            tgt = re.sub(r"[^A-Za-z0-9_]", "_", tr["target"])[:24] or "TARGET"
            lines.append(f"    SRC --> {tgt}: NEW ({tr['file']}:{tr['line']})")
        out["state"] = "\n".join(lines)
    if df["sinks"]:
        lines = ["graph LR", '    src["secret source"]']
        for i, h in enumerate(df["sinks"]):
            mark = " NOT scrubbed?" if h["high_risk"] or h["source_on_line"] else ""
            lines.append(f'    src --> s{i}["{h["sink"]} {h["file"]}:{h["line"]}{mark}"]')
        gaps = [f"s{i}" for i, h in enumerate(df["sinks"])
                if h["high_risk"] or h["source_on_line"]]
        if gaps:
            lines.append("    classDef gap fill:#ffd6d6,stroke:#c62828;")
            lines.append("    class " + ",".join(gaps) + " gap;")
        out["dataflow"] = "\n".join(lines)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archetype",
                    choices=["behavioral", "state", "dataflow", "all"],
                    default="all")
    ap.add_argument("--diff-file", help="unified diff path (default: stdin)")
    ap.add_argument("--mermaid", action="store_true")
    args = ap.parse_args()

    text = (open(args.diff_file, encoding="utf-8").read()
            if args.diff_file else sys.stdin.read())
    files = parse_diff(text)
    want = {args.archetype} if args.archetype != "all" else {
        "behavioral", "state", "dataflow"}

    beh = behavioral_signals(files) if "behavioral" in want else []
    st = (state_signals(files) if "state" in want
          else {"states": [], "added_transitions": [], "removed_transitions": []})
    df = (dataflow_signals(files) if "dataflow" in want
          else {"sinks": [], "sources_seen": []})

    out = {
        "summary": {
            "files": len(files),
            "behavioral_candidates": len(beh),
            "state_transitions_changed": (len(st["added_transitions"])
                                          + len(st["removed_transitions"])),
            "dataflow_sinks": len(df["sinks"]),
            "high_risk_sinks": sum(1 for h in df["sinks"] if h["high_risk"]),
        },
        "behavioral": beh,
        "state": st,
        "dataflow": df,
    }
    if args.mermaid:
        out["mermaid"] = mermaid(beh, st, df)

    json.dump(out, sys.stdout, indent=1)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
