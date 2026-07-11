"""Tests for scripts/lincoln_trace.py."""

import json
import os
from pathlib import Path

import pytest
import yaml

from scripts import lincoln_trace


def _write_state(tmp_path: Path, state: dict) -> Path:
    slug = state.get("current_run", {}).get("variables", {}).get("process_slug", "lincoln-test")
    path = tmp_path / slug / "workflow-stage.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


@pytest.fixture
def minimal_state(tmp_path):
    return _write_state(
        tmp_path,
        {
            "schema_version": "2.0.0",
            "current_run": {
                "run_id": "run-123",
                "current_stage": "clarify",
                "variables": {"process_slug": "lincoln-test"},
            },
        },
    )


def test_categorize_tool():
    assert lincoln_trace.categorize_tool("Skill") == "skill"
    assert lincoln_trace.categorize_tool("Agent") == "agent"
    assert lincoln_trace.categorize_tool("Write") == "write"
    assert lincoln_trace.categorize_tool("Edit") == "edit"
    assert lincoln_trace.categorize_tool("Bash") == "bash"
    assert lincoln_trace.categorize_tool("TaskCreate") == "task"
    assert lincoln_trace.categorize_tool("mcp__context7__query-docs") == "mcp"
    assert lincoln_trace.categorize_tool("LincolnHandoff") == "handoff"
    assert lincoln_trace.categorize_tool("Monitor") == "other"


def test_redact_args_bash():
    assert lincoln_trace.redact_args("Bash", {"command": "echo hello"}) == {"command": "echo hello"}


def test_redact_args_bash_masks_secrets():
    command = (
        "curl -H 'Authorization: Bearer super_secret_token' "
        "--api-key AKIAIOSFODNN7EXAMPLE "
        "--token=ghp_secrettoken "
        "OPENAI_API_KEY=sk-abc123 "
        "-u admin:password123 "
        "https://token:secret@github.com/org/repo.git "
        "https://api.example.com?api_key=leaked&token=leaked2 "
        "normal-arg"
    )
    summary = lincoln_trace.redact_args("Bash", {"command": command})
    masked = summary["command"]
    assert "super_secret_token" not in masked
    assert "AKIAIOSFODNN7EXAMPLE" not in masked
    assert "ghp_secrettoken" not in masked
    assert "sk-abc123" not in masked
    assert "password123" not in masked
    assert "token:secret@github.com" not in masked
    assert "api_key=leaked" not in masked
    assert "token=leaked2" not in masked
    assert "normal-arg" in masked


def test_redact_args_write():
    assert lincoln_trace.redact_args("Write", {"file_path": "foo.md"}) == {"file_path": "foo.md"}


def test_redact_args_skill():
    assert lincoln_trace.redact_args("Skill", {"skill": "foo", "args": "bar"}) == {
        "skill": "foo",
        "args": "bar",
    }


def test_redact_args_agent():
    assert lincoln_trace.redact_args("Agent", {"subagent_type": "coder", "description": "x"}) == {
        "subagent_type": "coder",
        "description": "x",
    }


def test_redact_args_unsupported_returns_primitives():
    assert lincoln_trace.redact_args("Monitor", {"command": "tail -f log", "timeout_ms": 5}) == {
        "command": "tail -f log",
        "timeout_ms": "5",
    }


def test_append_trace_entry_writes_jsonl(minimal_state):
    trace_file = lincoln_trace.append_trace_entry(
        minimal_state,
        "Bash",
        {"command": "pytest"},
        0,
    )
    assert trace_file is not None
    assert trace_file.name == "lincoln-trace.jsonl"

    lines = trace_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["schema_version"] == "1.0.0"
    assert entry["run_id"] == "run-123"
    assert entry["stage"] == "clarify"
    assert entry["tool"] == "Bash"
    assert entry["category"] == "bash"
    assert entry["target"] == "pytest"
    assert entry["exit_code"] == 0
    assert "sequence_id" in entry


def test_append_trace_entry_skips_no_trace_tools(minimal_state):
    assert lincoln_trace.append_trace_entry(minimal_state, "Read", {"file_path": "x"}, 0) is None
    assert lincoln_trace.append_trace_entry(minimal_state, "Grep", {}, 0) is None
    assert lincoln_trace.append_trace_entry(minimal_state, "Glob", {}, 0) is None


def test_append_trace_entry_uses_env_trace_file(minimal_state, monkeypatch, tmp_path):
    custom = tmp_path / "custom-trace.jsonl"
    monkeypatch.setenv("LINCOLN_TRACE_FILE", str(custom))
    lincoln_trace.append_trace_entry(minimal_state, "Write", {"file_path": "a.md"}, 0)
    assert custom.exists()
    entries = [json.loads(line) for line in custom.read_text(encoding="utf-8").strip().splitlines()]
    assert entries[0]["tool"] == "Write"


def test_append_trace_entry_uses_agent_id(minimal_state, monkeypatch, tmp_path):
    monkeypatch.delenv("LINCOLN_TRACE_FILE", raising=False)
    monkeypatch.setenv("LINCOLN_AGENT_ID", "agent-42")
    trace_file = lincoln_trace.append_trace_entry(minimal_state, "Bash", {"command": "x"}, 0)
    assert trace_file.name == "lincoln-trace-agent-42.jsonl"


def test_append_trace_entry_parses_string_args(minimal_state):
    trace_file = lincoln_trace.append_trace_entry(
        minimal_state,
        "Skill",
        '{"skill": "brainstorm", "args": "foo"}',
        0,
    )
    entry = json.loads(trace_file.read_text(encoding="utf-8").strip().splitlines()[0])
    assert entry["args_summary"]["skill"] == "brainstorm"


def test_append_trace_entry_multiple_are_atomic(minimal_state):
    for i in range(5):
        lincoln_trace.append_trace_entry(minimal_state, "Bash", {"command": f"cmd{i}"}, 0)
    trace_file = minimal_state.parent / ".trace" / "lincoln-trace.jsonl"
    lines = trace_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 5
    assert all(json.loads(line)["tool"] == "Bash" for line in lines)


def test_main_cli(minimal_state):
    argv = [
        "--state-file",
        str(minimal_state),
        "--tool",
        "Bash",
        "--args-json",
        json.dumps({"command": "make test"}),
        "--exit-code",
        "1",
    ]
    assert lincoln_trace.main(argv) == 0
    entry = json.loads(
        (minimal_state.parent / ".trace" / "lincoln-trace.jsonl")
        .read_text(encoding="utf-8")
        .strip()
        .splitlines()[0]
    )
    assert entry["exit_code"] == 1
    assert entry["target"] == "make test"
