#!/usr/bin/env python3
"""Lincoln friction scorer.

Reads the session trace for the current node, computes a friction score based
on configured signals, and writes a suggestion/prompt file when thresholds are
met. Designed to be invoked asynchronously from on-stop.sh.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

DEFAULT_POLICY_PATH = ".claude/policies/friction.yaml"
DEFAULT_TRACE_TAIL_LINES = 500


def load_policy(root: Path) -> dict[str, Any]:
    """Load the friction policy YAML, returning defaults if missing."""
    path = root / DEFAULT_POLICY_PATH
    if not path.exists():
        return _default_policy()
    return yaml.safe_load(path.read_text(encoding="utf-8")) or _default_policy()


def _default_policy() -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "thresholds": {"prompt_user": 5, "auto_suggest": 3},
        "weights": {
            "tool_failed": 2,
            "tool_rejected": 3,
            "retry_spike": 3,
            "human_override": 5,
            "long_session": 1,
        },
        "long_session_minutes": 30,
        "retry_count_threshold": 3,
    }


def _tail_jsonl(trace_file: Path, lines: int) -> list[dict[str, Any]]:
    if not trace_file.exists():
        return []
    try:
        with open(trace_file, "r", encoding="utf-8") as fh:
            all_lines = fh.readlines()
        return [json.loads(line) for line in all_lines[-lines:] if line.strip()]
    except Exception:
        return []


def _parse_timestamp(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def _compute_long_session_minutes(events: list[dict[str, Any]], threshold_minutes: int) -> float:
    if len(events) < 2 or threshold_minutes <= 0:
        return 0.0
    timestamps = [t for t in (_parse_timestamp(e.get("timestamp")) for e in events) if t]
    if len(timestamps) < 2:
        return 0.0
    duration = (max(timestamps) - min(timestamps)).total_seconds() / 60.0
    return duration if duration >= threshold_minutes else 0.0


def _count_tool_failures(events: list[dict[str, Any]]) -> int:
    return sum(
        1
        for e in events
        if e.get("category") == "tool" and e.get("exit_code", 0) != 0
    )


def _count_tool_rejected(events: list[dict[str, Any]]) -> int:
    return sum(
        1
        for e in events
        if e.get("category") == "tool" and e.get("args_summary", {}).get("blocked") is True
    )


def _count_retry_spikes(events: list[dict[str, Any]], threshold: int) -> int:
    """Count tools that consecutively failed >= threshold times in this window."""
    if threshold <= 0:
        return 0
    counts: dict[str, int] = {}
    spikes = 0
    for e in events:
        if e.get("category") != "tool":
            continue
        tool = e.get("tool", "")
        failed = e.get("exit_code", 0) != 0 or e.get("args_summary", {}).get("blocked") is True
        if failed:
            counts[tool] = counts.get(tool, 0) + 1
            if counts[tool] == threshold:
                spikes += 1
        else:
            counts[tool] = 0
    return spikes


def compute_friction(
    events: list[dict[str, Any]],
    policy: dict[str, Any],
) -> dict[str, Any]:
    """Compute friction score and signals from a window of trace events."""
    weights = policy.get("weights", {})
    retry_threshold = policy.get("retry_count_threshold", 3)
    long_session_minutes = policy.get("long_session_minutes", 30)

    tool_failed = _count_tool_failures(events)
    tool_rejected = _count_tool_rejected(events)
    retry_spike = _count_retry_spikes(events, retry_threshold)
    long_session = _compute_long_session_minutes(events, long_session_minutes)

    signals: dict[str, Any] = {
        "tool_failed": {"count": tool_failed, "weight": weights.get("tool_failed", 0)},
        "tool_rejected": {"count": tool_rejected, "weight": weights.get("tool_rejected", 0)},
        "retry_spike": {"count": retry_spike, "weight": weights.get("retry_spike", 0)},
        "human_override": {"count": 0, "weight": weights.get("human_override", 0)},
        "long_session": {
            "minutes": round(long_session, 2),
            "weight": weights.get("long_session", 0),
        },
    }

    score = (
        tool_failed * signals["tool_failed"]["weight"]
        + tool_rejected * signals["tool_rejected"]["weight"]
        + retry_spike * signals["retry_spike"]["weight"]
        + signals["human_override"]["count"] * signals["human_override"]["weight"]
        + (1 if long_session >= long_session_minutes else 0) * signals["long_session"]["weight"]
    )

    return {
        "score": score,
        "signals": signals,
        "event_count": len(events),
    }


def resolve_trace_file(state_path: Path | None) -> Path | None:
    """Resolve the trace file from workflow state or environment override."""
    env_file = os.environ.get("LINCOLN_TRACE_FILE")
    if env_file:
        return Path(env_file)

    if state_path is None:
        return None

    try:
        sys.path.insert(0, str(state_path.resolve().parents[1]))
        from scripts.lincoln_paths import get_process_slug, process_package_root
        from scripts.lincoln_trace import _load_state

        state = _load_state(state_path)
        if state is None:
            return state_path.parent / ".trace" / "lc-trace.jsonl"
        slug = get_process_slug(state, state_path)
        root = process_package_root(slug, state, state_path)
        return root / ".trace" / "lc-trace.jsonl"
    except Exception:
        return state_path.parent / ".trace" / "lc-trace.jsonl"


def write_friction_report(
    trace_dir: Path,
    score: int,
    signals: dict[str, Any],
    policy: dict[str, Any],
) -> Path | None:
    """Write a friction suggestion or prompt file when thresholds are met."""
    thresholds = policy.get("thresholds", {})
    prompt_threshold = thresholds.get("prompt_user", 5)
    suggest_threshold = thresholds.get("auto_suggest", 3)

    if score >= prompt_threshold:
        path = trace_dir / "friction-prompt.md"
        kind = "prompt"
    elif score >= suggest_threshold:
        path = trace_dir / "friction-suggestion.md"
        kind = "suggestion"
    else:
        return None

    active_signals = [
        f"- **{name}**: {info.get('count', info.get('minutes', 0))} (weight {info['weight']})"
        for name, info in signals.items()
        if (info.get("count", 0) > 0 or info.get("minutes", 0) > 0)
    ]

    content = f"""# Friction Report ({kind})

Generated at: {datetime.now(timezone.utc).isoformat()}
Score: **{score}**

## Detected signals

{chr(10).join(active_signals) if active_signals else "_No strong friction signals detected._"}

## Suggested action

Consider capturing a lesson learned in `knowledge/05-learnings/` or running:

```bash
python3 scripts/lincoln-knowledge.py suggest --stage <stage_id>
```

This is a suggestion only; the human PM decides whether to persist anything.
"""
    path.write_text(content, encoding="utf-8")
    return path


def score_friction(
    root: Path,
    state_path: Path | None = None,
    trace_file: Path | None = None,
    tail_lines: int = DEFAULT_TRACE_TAIL_LINES,
) -> dict[str, Any]:
    """Score friction and write a report if thresholds are met."""
    policy = load_policy(root)
    target_trace = trace_file or resolve_trace_file(state_path)
    if target_trace is None:
        return {"score": 0, "signals": {}, "report": None, "error": "no trace file"}

    events = _tail_jsonl(target_trace, tail_lines)
    result = compute_friction(events, policy)
    report = write_friction_report(target_trace.parent, result["score"], result["signals"], policy)
    result["report"] = str(report) if report else None
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score session friction from trace events")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--state-file", type=Path, default=None)
    parser.add_argument("--trace-file", type=Path, default=None)
    parser.add_argument("--tail-lines", type=int, default=DEFAULT_TRACE_TAIL_LINES)
    args = parser.parse_args(argv)

    result = score_friction(
        root=args.root,
        state_path=args.state_file,
        trace_file=args.trace_file,
        tail_lines=args.tail_lines,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())