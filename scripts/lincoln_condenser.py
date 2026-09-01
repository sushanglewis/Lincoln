#!/usr/bin/env python3
"""Lincoln trace condenser.

Summarizes a window of trace events when the count exceeds a threshold. The
summary is appended as a `condensation` event to the trace and returned to the
caller (stage_loader handoff-report) for inclusion in handoff frontmatter.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts import lincoln_trace

DEFAULT_THRESHOLD = 200


def load_events(trace_file: Path, max_events: int = 10000) -> list[dict[str, Any]]:
    if not trace_file.exists():
        return []
    try:
        with open(trace_file, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
        return [json.loads(line) for line in lines[-max_events:] if line.strip()]
    except Exception:
        return []


def summarize(events: list[dict[str, Any]]) -> dict[str, Any]:
    categories = Counter(e.get("category", "other") for e in events)
    tools = Counter(e.get("tool", "") for e in events if e.get("category") == "tool")
    stages = Counter(e.get("stage", "unknown") for e in events)
    failed = sum(1 for e in events if e.get("exit_code", 0) != 0)
    blocked = sum(
        1 for e in events if e.get("args_summary", {}).get("blocked") is True
    )

    return {
        "event_count": len(events),
        "categories": dict(categories.most_common(10)),
        "top_tools": dict(tools.most_common(10)),
        "stages": dict(stages.most_common(10)),
        "failed_count": failed,
        "blocked_count": blocked,
        "first_timestamp": events[0].get("timestamp") if events else None,
        "last_timestamp": events[-1].get("timestamp") if events else None,
    }


def condense(
    trace_file: Path,
    threshold: int = DEFAULT_THRESHOLD,
    dry_run: bool = False,
) -> dict[str, Any] | None:
    """Condense trace events if threshold is exceeded.

    Returns the condensation summary or None when below threshold.
    """
    events = load_events(trace_file)
    if len(events) < threshold:
        return None

    summary = summarize(events)
    if not dry_run:
        try:
            lincoln_trace.append_event_to_file(
                trace_file=trace_file,
                category="condensation",
                payload={
                    "event_type": "condensation",
                    "event_count": summary["event_count"],
                    "threshold": threshold,
                    "summary": summary,
                },
                run_id=events[-1].get("run_id") if events else None,
                stage=events[-1].get("stage") if events else None,
                node_id=events[-1].get("node_id") if events else None,
            )
        except Exception:
            # Condensation must never block handoff report generation.
            pass
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Condense Lincoln trace events")
    parser.add_argument("--trace-file", type=Path, required=True)
    parser.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD)
    parser.add_argument("--dry-run", action="store_true", default=False)
    args = parser.parse_args(argv)

    result = condense(args.trace_file, threshold=args.threshold, dry_run=args.dry_run)
    if result is None:
        print(json.dumps({"condensed": False}, ensure_ascii=False))
    else:
        print(json.dumps({"condensed": True, "summary": result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())