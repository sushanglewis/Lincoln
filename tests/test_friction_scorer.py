"""Tests for scripts/lincoln_friction.py."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

from scripts.lincoln_friction import (
    compute_friction,
    load_policy,
    score_friction,
    write_friction_report,
)


@pytest.fixture
def fake_repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    policy_dir = root / ".claude" / "policies"
    policy_dir.mkdir(parents=True)
    (policy_dir / "friction.yaml").write_text(
        yaml.safe_dump(
            {
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
        ),
        encoding="utf-8",
    )
    return root


def _event(
    category: str = "tool",
    tool: str = "Bash",
    exit_code: int = 0,
    blocked: bool = False,
    minutes_ago: int = 0,
) -> dict:
    ts = (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    return {
        "schema_version": "2.0.0",
        "sequence_id": "seq",
        "timestamp": ts,
        "run_id": "run-1",
        "stage": "phase-2-p1-implement",
        "category": category,
        "tool": tool,
        "exit_code": exit_code,
        "args_summary": {"blocked": blocked},
    }


def test_load_policy_reads_yaml(fake_repo):
    policy = load_policy(fake_repo)
    assert policy["thresholds"]["prompt_user"] == 5
    assert policy["weights"]["tool_failed"] == 2


def test_compute_friction_zero_for_empty_events():
    result = compute_friction([], _default_policy())
    assert result["score"] == 0
    assert result["event_count"] == 0


def test_compute_friction_counts_tool_failed():
    events = [_event(exit_code=1), _event(exit_code=1)]
    result = compute_friction(events, _default_policy())
    assert result["score"] == 4
    assert result["signals"]["tool_failed"]["count"] == 2


def test_compute_friction_counts_tool_rejected():
    events = [_event(blocked=True), _event(blocked=True)]
    result = compute_friction(events, _default_policy())
    assert result["score"] == 6
    assert result["signals"]["tool_rejected"]["count"] == 2


def test_compute_friction_counts_retry_spike():
    events = [_event(exit_code=1), _event(exit_code=1), _event(exit_code=1)]
    result = compute_friction(events, _default_policy())
    assert result["signals"]["retry_spike"]["count"] == 1
    assert result["score"] == 9  # 3*2 for failures + 3 for spike


def test_compute_friction_long_session():
    events = [
        _event(minutes_ago=40),
        _event(minutes_ago=0),
    ]
    result = compute_friction(events, _default_policy())
    assert result["signals"]["long_session"]["minutes"] >= 40
    assert result["score"] == 1


def test_write_friction_report_prompt_when_high_score(tmp_path):
    policy = _default_policy()
    report = write_friction_report(tmp_path, 6, {"tool_failed": {"count": 3, "weight": 2}}, policy)
    assert report is not None
    assert report.name == "friction-prompt.md"
    assert "tool_failed" in report.read_text(encoding="utf-8")


def test_write_friction_report_suggestion_when_medium_score(tmp_path):
    policy = _default_policy()
    report = write_friction_report(tmp_path, 3, {"tool_failed": {"count": 1, "weight": 2}}, policy)
    assert report is not None
    assert report.name == "friction-suggestion.md"


def test_write_friction_report_none_when_low_score(tmp_path):
    policy = _default_policy()
    report = write_friction_report(tmp_path, 1, {}, policy)
    assert report is None


def test_score_friction_writes_report(fake_repo):
    trace_dir = fake_repo / "issue-1" / ".trace"
    trace_dir.mkdir(parents=True)
    trace_file = trace_dir / "lc-trace.jsonl"
    events = [_event(exit_code=1), _event(exit_code=1), _event(exit_code=1)]
    trace_file.write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")

    result = score_friction(fake_repo, trace_file=trace_file)
    assert result["score"] == 9
    assert result["report"] is not None
    assert Path(result["report"]).exists()


def _default_policy():
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