#!/usr/bin/env python3
"""
Task-tool guard for the Lincoln workflow.

Prevents the agent from using TaskCreate/TaskUpdate as placeholders for
"I will send a user message soon" in dialogue stages, and limits consecutive
task-tool calls everywhere else so a runaway loop cannot accumulate hundreds
of task artifacts without a non-task action in between.

Intended to be invoked from .claude/hooks/pre-tool-use.sh for every tool call.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

# Stages where the agent is expected to talk to the PM, not to manage a task
# list.  We default this from the workflow YAML (human_gate: true), but allow
# an override for tests.
DIALOGUE_STAGE_FALLBACK: frozenset[str] = frozenset(
    {"clarify", "product-design-docs", "product-prototype", "implement"}
)

TASK_TOOLS: frozenset[str] = frozenset({"TaskCreate", "TaskUpdate"})

DEFAULT_MAX_CONSECUTIVE = 3


def load_yaml(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(path)
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_state(state_file: Path) -> dict[str, Any] | None:
    if not state_file.exists():
        return None
    data = load_yaml(state_file)
    if not isinstance(data, dict):
        return None
    return data


def resolve_project_root(state_file: Path) -> Path | None:
    """Derive project root from <root>/.claude/workflow-state.yaml."""
    resolved = state_file.resolve()
    if len(resolved.parents) < 2:
        return None
    return resolved.parents[1]


def dialogue_stages(workflow_file: Path | None, override: set[str] | None) -> set[str]:
    if override is not None:
        return override
    if workflow_file is None or not workflow_file.exists():
        return set(DIALOGUE_STAGE_FALLBACK)
    try:
        data = load_yaml(workflow_file)
        workflow = data.get("workflow", data) if isinstance(data, dict) else {}
        return {
            step["id"]
            for step in workflow.get("steps", [])
            if isinstance(step, dict) and step.get("human_gate")
        }
    except (yaml.YAMLError, AttributeError, KeyError, TypeError):
        return set(DIALOGUE_STAGE_FALLBACK)


def counter_file_path(state_file: Path) -> Path:
    root = resolve_project_root(state_file)
    if root is None:
        # Unusual path depth; keep the counter next to the state file.
        return state_file.resolve().parent / ".context" / "task-tool-burst.json"
    return root / ".context" / "task-tool-burst.json"


def load_counter(counter_file: Path) -> dict[str, Any]:
    if not counter_file.exists():
        return {"count": 0, "last_stage": None, "last_tool": None}
    try:
        data = json.loads(counter_file.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    return {"count": 0, "last_stage": None, "last_tool": None}


def save_counter(counter_file: Path, data: dict[str, Any]) -> None:
    counter_file.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(dir=counter_file.parent, suffix=".json.tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, counter_file)
    except Exception:
        try:
            os.close(tmp_fd)
        except OSError:
            pass
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def block(message: str) -> int:
    print(f"BLOCKED: {message}", file=sys.stderr)
    return 1


def allow() -> int:
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lincoln task-tool guard")
    parser.add_argument("--state-file", type=Path, default=None)
    parser.add_argument("--tool-name", required=True)
    parser.add_argument("--tool-args", default="{}")
    parser.add_argument(
        "--dialogue-stages",
        help="Comma-separated list of stage IDs where task tools are forbidden",
    )
    parser.add_argument(
        "--max-consecutive",
        type=int,
        default=DEFAULT_MAX_CONSECUTIVE,
        help="Maximum allowed consecutive TaskCreate/TaskUpdate calls",
    )
    args = parser.parse_args(argv)

    state_file = args.state_file
    if state_file is None:
        state_file = Path(
            os.environ.get(
                "LINCOLN_STATE_FILE",
                Path.cwd() / ".claude" / "workflow-state.yaml",
            )
        )

    state = load_state(state_file)
    if state is None:
        # Not a Lincoln project or not initialized yet; stay out of the way.
        return allow()

    current_stage = state.get("current_run", {}).get("current_stage") or "not_started"

    # Reset the burst counter whenever a non-task tool is used.
    if args.tool_name not in TASK_TOOLS:
        counter_file = counter_file_path(state_file)
        save_counter(
            counter_file,
            {"count": 0, "last_stage": current_stage, "last_tool": args.tool_name},
        )
        return allow()

    # We are handling a task tool from here on.
    override_stages = None
    if args.dialogue_stages is not None:
        override_stages = {s.strip() for s in args.dialogue_stages.split(",") if s.strip()}

    root = resolve_project_root(state_file)
    workflow_file = None
    if root is not None:
        workflow_file = root / ".claude" / "workflows" / "interview-to-knowledge.yaml"

    dialogue = dialogue_stages(workflow_file, override_stages)

    if current_stage in dialogue:
        return block(
            f"TaskCreate/TaskUpdate are not allowed in the dialogue stage '{current_stage}'. "
            "Send your message to the user directly instead of using task tools as placeholders."
        )

    counter_file = counter_file_path(state_file)
    counter = load_counter(counter_file)

    if counter.get("last_stage") != current_stage or counter.get("last_tool") not in TASK_TOOLS:
        counter = {"count": 1, "last_stage": current_stage, "last_tool": args.tool_name}
    else:
        counter = {
            **counter,
            "count": counter.get("count", 0) + 1,
        }

    save_counter(counter_file, counter)

    if counter["count"] > args.max_consecutive:
        return block(
            f"Too many consecutive task-tool calls ({counter['count']}) in stage '{current_stage}'. "
            "Perform a non-task action (e.g. Read or send a user message) before creating/updating more tasks."
        )

    return allow()


if __name__ == "__main__":
    sys.exit(main())
