#!/usr/bin/env python3
"""Lincoln workflow bundle CLI backing the lc-wf-* harness commands.

Usage:
    python3 scripts/lincoln_workflow.py list
    python3 scripts/lincoln_workflow.py start --workflow <name> [--issue-number N] [--force]
    python3 scripts/lincoln_workflow.py status

- solo workflows render a session-scoped instance at .context/workflow/<name>.yaml
- team workflows delegate to scripts/init-lincoln-branch.sh (branch + issue package)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lincoln_paths import PROJECT_ROOT  # noqa: E402

WORKFLOWS_DIR = PROJECT_ROOT / ".claude" / "workflows"
SOLO_TEMPLATE_PATH = PROJECT_ROOT / ".claude" / "templates" / "solo-workflow-context.yaml"
SOLO_STATE_DIR = PROJECT_ROOT / ".context" / "workflow"
INIT_BRANCH_SCRIPT = PROJECT_ROOT / "scripts" / "init-lincoln-branch.sh"
STAGE_LOADER_SCRIPT = PROJECT_ROOT / "scripts" / "stage_loader.py"

DEFAULT_EXECUTION_MODE = "team"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_id_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def load_workflow_definition(name: str) -> dict[str, Any]:
    path = WORKFLOWS_DIR / f"{name}.yaml"
    if not path.is_file():
        available = ", ".join(sorted(p.stem for p in WORKFLOWS_DIR.glob("*.yaml")))
        raise SystemExit(f"ERROR: unknown workflow '{name}'. Available: {available}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data.get("workflow", data)


def list_workflows() -> int:
    rows = []
    for path in sorted(WORKFLOWS_DIR.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        wf = data.get("workflow", {})
        rows.append(
            (
                wf.get("name", path.stem),
                wf.get("execution_mode", DEFAULT_EXECUTION_MODE),
                wf.get("description", ""),
            )
        )
    if not rows:
        print("No workflows found under .claude/workflows/")
        return 1
    print(f"{'NAME':<32} {'MODE':<6} DESCRIPTION")
    for name, mode, description in rows:
        print(f"{name:<32} {mode:<6} {description}")
    return 0


def start_solo(workflow_name: str, wf: dict[str, Any], force: bool) -> int:
    state_path = SOLO_STATE_DIR / f"{workflow_name}.yaml"
    if state_path.exists() and not force:
        raise SystemExit(f"ERROR: solo instance already exists: {state_path} (use --force to overwrite)")

    state = yaml.safe_load(SOLO_TEMPLATE_PATH.read_text(encoding="utf-8"))
    steps = wf.get("steps", [])
    first_stage = steps[0].get("id", "not_started") if steps else "not_started"
    now = now_iso()

    state["workflow"]["name"] = wf.get("name", workflow_name)
    state["workflow"]["version"] = wf.get("version", "1.0.0")
    state["workflow"]["template"] = workflow_name

    current_run = state["current_run"]
    current_run["run_id"] = f"{workflow_name}-{run_id_stamp()}"
    current_run["current_stage"] = first_stage
    current_run["status"] = "in_progress"
    current_run["started_at"] = now
    current_run["last_updated_at"] = now
    state["recovery"]["can_resume_from"] = first_stage

    state_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = state_path.with_suffix(".yaml.tmp")
    try:
        tmp_path.write_text(
            yaml.dump(state, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8"
        )
        tmp_path.replace(state_path)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        raise

    try:
        display_path = state_path.relative_to(PROJECT_ROOT)
    except ValueError:
        display_path = state_path
    print(f"Solo workflow instance created: {display_path}")
    print(f"Workflow: {workflow_name} (solo) | first stage: {first_stage}")
    print(f"Next: python3 scripts/stage_loader.py --stage {first_stage} --action validate-entry")
    return 0


def start_team(workflow_name: str, issue_number: str | None) -> int:
    if not issue_number:
        raise SystemExit(
            "ERROR: --issue-number is required for team workflows (branch-scoped issue package)"
        )
    cmd = [
        "bash",
        str(INIT_BRANCH_SCRIPT),
        "--workflow",
        workflow_name,
        "--issue-number",
        str(issue_number),
    ]
    return subprocess.run(cmd, cwd=PROJECT_ROOT).returncode


def cmd_start(args: argparse.Namespace) -> int:
    wf = load_workflow_definition(args.workflow)
    mode = wf.get("execution_mode", DEFAULT_EXECUTION_MODE)
    if mode == "solo":
        return start_solo(args.workflow, wf, args.force)
    return start_team(args.workflow, args.issue_number)


def cmd_status(_args: argparse.Namespace) -> int:
    return subprocess.run(
        [sys.executable, str(STAGE_LOADER_SCRIPT), "--action", "status"], cwd=PROJECT_ROOT
    ).returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Lincoln workflow bundle CLI (lc-wf-* commands)",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="List registered workflows with execution mode")

    start = sub.add_parser("start", help="Start a workflow run (solo instance or team issue package)")
    start.add_argument("--workflow", required=True, help="Workflow name under .claude/workflows/")
    start.add_argument("--issue-number", help="Issue number (required for team workflows)")
    start.add_argument("--force", action="store_true", help="Overwrite existing solo instance")

    sub.add_parser("status", help="Show current workflow run status")

    args = parser.parse_args()
    if args.command == "list":
        return list_workflows()
    if args.command == "start":
        return cmd_start(args)
    return cmd_status(args)


if __name__ == "__main__":
    sys.exit(main())
