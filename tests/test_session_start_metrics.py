"""Tests for session-start token/byte estimation (#63)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.lincoln_session_start_metrics import compute_metrics, estimate_tokens, main


def test_estimate_tokens_is_positive():
    assert estimate_tokens("hello world") > 0


def test_estimate_tokens_counts_cjk_per_char():
    text = "你好世界"
    assert estimate_tokens(text) == 4


def test_compute_metrics_includes_all_fields():
    metrics = compute_metrics("hello 世界", stage="clarify", status="in_progress")
    assert metrics["schema_version"] == "1.0.0"
    assert metrics["stage"] == "clarify"
    assert metrics["status"] == "in_progress"
    assert metrics["bytes"] > 0
    assert metrics["chars"] > 0
    assert metrics["tokens"] > 0


def test_cli_writes_json(tmp_path):
    input_file = tmp_path / "hook.txt"
    input_file.write_text("Lincoln session start", encoding="utf-8")
    output_file = tmp_path / "metrics.json"

    assert main(["--input", str(input_file), "--output", str(output_file)]) == 0
    assert output_file.exists()
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data["tokens"] > 0


def test_benchmark_metrics_reads_session_start_tokens(tmp_path):
    from scripts.lincoln_benchmark_metrics import compute_metrics

    process_slug = "issue-test"
    trace_dir = tmp_path / process_slug / ".trace"
    trace_dir.mkdir(parents=True, exist_ok=True)
    metrics_file = trace_dir / "session-start-metrics.json"
    metrics_file.write_text(
        json.dumps({"schema_version": "1.0.0", "bytes": 1200, "chars": 600, "tokens": 150}),
        encoding="utf-8",
    )

    state = {
        "current_run": {
            "current_stage": "clarify",
            "variables": {"process_slug": process_slug},
        },
        "workflow": {"template": "interview-to-knowledge"},
        "nodes": [],
    }

    metrics, confidence = compute_metrics([], state, "S1", tmp_path)
    assert metrics["session"]["session_start_tokens"] == 150
    assert metrics["session"]["session_start_bytes"] == 1200
    assert confidence["session_start_tokens"] == "exact"
