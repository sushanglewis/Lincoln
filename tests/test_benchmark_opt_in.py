"""Tests that benchmark is opt-in only (#72)."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_on_stop_does_not_auto_run_benchmark():
    script = ROOT / ".claude" / "hooks" / "on-stop.sh"
    text = script.read_text(encoding="utf-8")
    assert "scripts/lincoln_benchmark.py" not in text
    assert "session_stop" not in text


def test_post_tool_use_does_not_auto_run_benchmark():
    script = ROOT / ".claude" / "hooks" / "post-tool-use.sh"
    text = script.read_text(encoding="utf-8")
    assert "scripts/lincoln_benchmark.py" not in text


def test_handoff_report_does_not_auto_run_benchmark():
    source = ROOT / "scripts" / "stage_loader.py"
    text = source.read_text(encoding="utf-8")
    assert 'action_benchmark_report(state_file, "handoff")' not in text


def test_command_map_points_to_explicit_benchmark_cli():
    command_map = ROOT / ".claude" / "harnesses" / "command-map.yaml"
    data = yaml.safe_load(command_map.read_text(encoding="utf-8"))
    benchmark = data["commands"]["lc-benchmark"]
    assert "lc-benchmark-cli.py" in benchmark["action"]
    assert "显式" in benchmark["description"] or "opt-in" in benchmark["description"].lower()


def test_explicit_benchmark_cli_exists():
    cli = ROOT / "scripts" / "lc-benchmark-cli.py"
    assert cli.exists()
    text = cli.read_text(encoding="utf-8")
    assert "resolve_state_path" in text
    assert "lincoln_benchmark.main" in text
