"""Tests for scripts/lincoln_condenser.py."""

import json
from pathlib import Path

import pytest

from scripts.lincoln_condenser import condense, load_events, summarize


@pytest.fixture
def trace_file(tmp_path):
    return tmp_path / "lc-trace.jsonl"


def _event(category="tool", tool="Bash", exit_code=0, blocked=False, stage="s1"):
    return {
        "schema_version": "2.0.0",
        "sequence_id": "seq",
        "timestamp": "2026-08-29T12:00:00Z",
        "run_id": "run-1",
        "stage": stage,
        "node_id": "node-1",
        "category": category,
        "tool": tool,
        "exit_code": exit_code,
        "args_summary": {"blocked": blocked},
    }


def test_load_events_reads_jsonl(trace_file):
    events = [_event(), _event()]
    trace_file.write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
    loaded = load_events(trace_file)
    assert len(loaded) == 2
    assert loaded[0]["run_id"] == "run-1"


def test_load_events_empty_file(trace_file):
    assert load_events(trace_file) == []


def test_summarize_counts_categories():
    events = [
        _event(category="tool", tool="Bash"),
        _event(category="tool", tool="Edit"),
        _event(category="stage_lifecycle"),
    ]
    summary = summarize(events)
    assert summary["event_count"] == 3
    assert summary["categories"]["tool"] == 2
    assert summary["categories"]["stage_lifecycle"] == 1
    assert summary["top_tools"]["Bash"] == 1


def test_summarize_counts_failed_and_blocked():
    events = [
        _event(exit_code=1),
        _event(exit_code=1),
        _event(blocked=True),
    ]
    summary = summarize(events)
    assert summary["failed_count"] == 2
    assert summary["blocked_count"] == 1


def test_condense_below_threshold_returns_none(trace_file):
    events = [_event() for _ in range(5)]
    trace_file.write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
    result = condense(trace_file, threshold=10, dry_run=True)
    assert result is None


def test_condense_above_threshold_returns_summary(trace_file):
    events = [_event() for _ in range(15)]
    trace_file.write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
    result = condense(trace_file, threshold=10, dry_run=True)
    assert result is not None
    assert result["event_count"] == 15


def test_condense_appends_condensation_event(trace_file):
    events = [_event(stage="phase-2-p1-implement") for _ in range(15)]
    trace_file.write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
    result = condense(trace_file, threshold=10, dry_run=False)
    assert result is not None

    lines = trace_file.read_text(encoding="utf-8").strip().splitlines()
    last = json.loads(lines[-1])
    assert last["category"] == "condensation"
    assert last["args_summary"]["event_type"] == "condensation"
    assert last["args_summary"]["event_count"] == 15
    assert last["stage"] == "phase-2-p1-implement"


def test_condense_respects_dry_run(trace_file):
    events = [_event() for _ in range(15)]
    trace_file.write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
    before = trace_file.read_text(encoding="utf-8")
    result = condense(trace_file, threshold=10, dry_run=True)
    assert result is not None
    assert trace_file.read_text(encoding="utf-8") == before