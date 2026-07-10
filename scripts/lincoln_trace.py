#!/usr/bin/env python3
"""Lincoln session trace writer.

Appends structured, immutable trace entries to a per-process JSONL file.
Designed to be called from the PostToolUse hook for every tool invocation
(except recursive or no-op tools).
"""

from __future__ import annotations

import argparse
import fcntl
import json
import logging
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure project root on path when invoked as a script
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.lincoln_paths import (  # noqa: E402
    get_process_slug,
    load_yaml,
    process_package_root,
)

TRACE_SCHEMA_VERSION = "1.0.0"

# Tools whose invocations are not traced to avoid recursion or noise.
NO_TRACE_TOOLS = {"Read", "Grep", "Glob"}

# Task-management tools that share the same trace category and redaction rules.
TASK_TOOLS = frozenset({
    "TaskCreate",
    "TaskUpdate",
    "TaskGet",
    "TaskList",
    "TaskOutput",
    "TaskStop",
})

# Maximum length stored for a Bash command summary in the trace entry.
COMMAND_SUMMARY_MAX_LEN = 500

# Basic secret masking for Bash command strings. Values following common secret
# flags or environment variable assignments are replaced with `***`.
_MASK_PATTERNS = [
    re.compile(r"(?i)((?:--api-key|-k|--token|--password|--secret|--access-token)\s+)\S+"),
    re.compile(r"(?i)((?:--api-key|-k|--token|--password|--secret|--access-token)=)\S+"),
    re.compile(
        r"(?i)\b(API_KEY|TOKEN|PASSWORD|SECRET|GH_TOKEN|GITHUB_TOKEN|OPENAI_API_KEY|ANTHROPIC_API_KEY|AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY|ACCESS_TOKEN)=\S+"
    ),
    re.compile(r"(?i)(Authorization:\s*(?:Bearer|Basic|Token)\s+)\S+"),
    re.compile(r"(?i)(X-Api-Key:\s+)\S+"),
    re.compile(r"(?i)((?:--user|-u)\s+)\S+:\S+"),
    re.compile(r"(?i)(https?://)[^:]+:[^@]+@"),
    re.compile(r"(?i)([\?\x26])(api_key|token|key)=[^\x26]+"),
]


def categorize_tool(tool: str) -> str:
    """Bucket a Claude Code tool name into a Lincoln trace category."""
    if tool == "Skill":
        return "skill"
    if tool == "Agent":
        return "agent"
    if tool in ("Read", "Grep", "Glob"):
        return "read"
    if tool == "Write":
        return "write"
    if tool == "Edit":
        return "edit"
    if tool == "Bash":
        return "bash"
    if tool in TASK_TOOLS:
        return "task"
    if tool.startswith("mcp__"):
        return "mcp"
    if tool == "LincolnHandoff":
        return "handoff"
    return "other"


def _first_non_none(mapping: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in mapping:
            return mapping[key]
    return None


def _mask_command(command: str) -> str:
    masked = command
    for pattern in _MASK_PATTERNS:
        masked = pattern.sub(r"\1***", masked)
    return masked


def _redact_bash(args: dict[str, Any]) -> dict[str, Any]:
    command = args.get("command", "")
    return {"command": _mask_command(str(command))[:COMMAND_SUMMARY_MAX_LEN]}


def _redact_file(args: dict[str, Any]) -> dict[str, Any]:
    return {"file_path": str(args.get("file_path", ""))[:500]}


def _redact_skill(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "skill": str(args.get("skill", ""))[:200],
        "args": str(args.get("args", ""))[:500],
    }


def _redact_agent(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "subagent_type": str(args.get("subagent_type", ""))[:200] or "general-purpose",
        "description": str(args.get("description", ""))[:300],
    }


def _redact_task(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "subject": str(_first_non_none(args, "subject", "taskId", "description") or "")[:300],
    }


def _redact_mcp(args: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for key in ("path", "name", "url", "projectId", "skill", "query"):
        if key in args:
            summary[key] = str(args[key])[:200]
    return summary


def _redact_handoff(args: dict[str, Any]) -> dict[str, Any]:
    return {"stage": str(args.get("stage", ""))[:100]}


def _redact_generic(args: dict[str, Any]) -> dict[str, Any]:
    return {
        key: str(value)[:200]
        for key, value in args.items()
        if isinstance(value, (str, int, float, bool))
    }


def redact_args(tool: str, args: Any) -> dict[str, Any]:
    """Produce a privacy-safe summary of tool arguments.

    This implementation is intentionally conservative: it records paths and
    high-level identifiers but does not store secrets, full command output, or
    large payloads. It is designed as a pluggable hook for future MCP-specific
    redaction rules.
    """
    if not isinstance(args, dict):
        return {"_raw_type": type(args).__name__}

    if tool == "Bash":
        return _redact_bash(args)
    if tool in ("Write", "Edit", "Read"):
        return _redact_file(args)
    if tool == "Skill":
        return _redact_skill(args)
    if tool == "Agent":
        return _redact_agent(args)
    if tool == "LincolnHandoff":
        return _redact_handoff(args)
    if tool in TASK_TOOLS:
        return _redact_task(args)
    if tool.startswith("mcp__"):
        return _redact_mcp(args)
    return _redact_generic(args)


def generate_sequence_id() -> str:
    """Return a globally unique trace sequence identifier."""
    return uuid.uuid4().hex


def _resolve_trace_file(state: dict[str, Any] | None, state_path: Path | None) -> Path:
    """Decide which JSONL file to write to, honouring child-agent overrides."""
    env_file = os.environ.get("LINCOLN_TRACE_FILE")
    if env_file:
        return Path(env_file)

    project_root = state_path.resolve().parents[1] if state_path else _PROJECT_ROOT
    slug = get_process_slug(state, state_path)
    root = process_package_root(slug, state, state_path, project_root=project_root)
    trace_dir = root / ".trace"

    agent_id = os.environ.get("LINCOLN_AGENT_ID")
    if agent_id:
        return trace_dir / f"lincoln-trace-{agent_id}.jsonl"

    return trace_dir / "lincoln-trace.jsonl"


def _get_run_id(state: dict[str, Any] | None, run_id: str | None) -> str:
    if run_id:
        return run_id
    if state:
        return str(state.get("current_run", {}).get("run_id", "")) or "unknown"
    return "unknown"


def _get_stage(state: dict[str, Any] | None, stage: str | None) -> str:
    if stage:
        return stage
    if state:
        return str(state.get("current_run", {}).get("current_stage", "")) or "unknown"
    return "unknown"


def _safe_json_loads(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception as exc:
            logging.warning("Could not parse trace args as JSON: %s", exc)
            return {"_unparsed": value[:200]}
    return value


def _load_state(state_path: Path | None) -> dict[str, Any] | None:
    if not state_path or not state_path.exists():
        return None
    try:
        return load_yaml(state_path)
    except Exception as exc:
        logging.warning("Failed to load workflow state from %s: %s", state_path, exc)
        return None


def _build_trace_target(tool: str, args_summary: dict[str, Any]) -> str:
    if tool == "Skill":
        return str(args_summary.get("skill", ""))
    if tool == "Agent":
        return str(args_summary.get("subagent_type", ""))
    if tool == "Bash":
        return str(args_summary.get("command", ""))[:120]
    if "file_path" in args_summary:
        return str(args_summary["file_path"])
    return str(args_summary.get("path", args_summary.get("name", "")))


def _build_trace_entry(
    tool: str,
    args_summary: dict[str, Any],
    exit_code: int,
    run_id: str,
    stage: str,
) -> dict[str, Any]:
    return {
        "schema_version": TRACE_SCHEMA_VERSION,
        "sequence_id": generate_sequence_id(),
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "run_id": run_id,
        "stage": stage,
        "tool": tool,
        "category": categorize_tool(tool),
        "target": _build_trace_target(tool, args_summary),
        "exit_code": int(exit_code),
        "args_summary": args_summary,
    }


def _append_trace_line(trace_file: Path, entry: dict[str, Any]) -> None:
    trace_file.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n"
    with open(trace_file, "a", encoding="utf-8") as fh:
        fcntl.lockf(fh.fileno(), fcntl.LOCK_EX)
        try:
            fh.write(line)
            fh.flush()
        finally:
            fcntl.lockf(fh.fileno(), fcntl.LOCK_UN)


def append_trace_entry(
    state_path: Path | None,
    tool: str,
    args: Any,
    exit_code: int,
    stage: str | None = None,
    run_id: str | None = None,
) -> Path | None:
    """Append a single trace entry to the appropriate JSONL file.

    The write is atomic with respect to other processes on the same host: the
    file is locked while appending, so concurrent parent and child agents do
    not interleave JSON lines.
    """
    if tool in NO_TRACE_TOOLS:
        return None

    state = _load_state(state_path)
    resolved_run_id = _get_run_id(state, run_id)
    resolved_stage = _get_stage(state, stage)
    trace_file = _resolve_trace_file(state, state_path)
    args_summary = redact_args(tool, _safe_json_loads(args))
    entry = _build_trace_entry(tool, args_summary, exit_code, resolved_run_id, resolved_stage)
    _append_trace_line(trace_file, entry)
    return trace_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Append a Lincoln trace entry")
    parser.add_argument("--state-file", type=Path, default=None)
    parser.add_argument("--tool", required=True)
    parser.add_argument("--args-json", default="{}")
    parser.add_argument("--exit-code", type=int, default=0)
    parser.add_argument("--stage", default=None)
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args(argv)

    append_trace_entry(
        state_path=args.state_file,
        tool=args.tool,
        args=args.args_json,
        exit_code=args.exit_code,
        stage=args.stage,
        run_id=args.run_id,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
