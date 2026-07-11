#!/usr/bin/env python3
"""
Lincoln structural validators.

Usage:
    python scripts/validate_stage.py --phase entry --check file_exists --args path/to/file
    python scripts/validate_stage.py --phase exit --check artifacts_present

Exit code 0 means pass, 1 means fail.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lincoln_paths import get_process_slug, load_yaml, resolve_state_path


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def pass_check(message: str = "") -> None:
    print(f"PASS{' - ' + message if message else ''}")
    sys.exit(0)


def process_slug() -> str:
    env_slug = os.environ.get("LINCOLN_PROCESS_SLUG")
    if env_slug:
        return env_slug

    state_file = resolve_state_path(None, PROJECT_ROOT)
    if state_file and state_file.exists():
        try:
            state = load_yaml(state_file)
            return get_process_slug(state, state_file)
        except Exception:
            pass
    return "lincoln-process"


def process_root() -> Path:
    slug = process_slug()
    root = PROJECT_ROOT / slug
    if root.exists():
        return root
    return PROJECT_ROOT


def process_path(*parts: str) -> Path:
    return process_root().joinpath(*parts)


def load_state() -> dict[str, Any] | None:
    state_file = resolve_state_path(None, PROJECT_ROOT)
    if not state_file or not state_file.exists():
        return None
    try:
        return load_yaml(state_file)
    except Exception:
        return None


def get_latest_node_for_stage(state: dict[str, Any], stage_id: str) -> dict[str, Any] | None:
    nodes = state.get("nodes", [])
    matching = [n for n in nodes if n.get("stage_id") == stage_id]
    return matching[-1] if matching else None


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def check_file_exists(path: str) -> None:
    target = PROJECT_ROOT / path
    if not target.exists():
        fail(f"File does not exist: {target}")
    pass_check(str(target))


def check_artifact_exists(path: str) -> None:
    target = process_path(path)
    if not target.exists() or target.stat().st_size == 0:
        fail(f"Artifact missing or empty: {target}")
    pass_check(str(target))


def check_audio_format_supported(path: str) -> None:
    supported = {".mp3", ".m4a", ".wav", ".mp4", ".mov"}
    ext = Path(path).suffix.lower()
    if ext not in supported:
        fail(f"Unsupported audio format: {ext}. Supported: {', '.join(supported)}")
    pass_check(ext)


def check_artifacts_present() -> None:
    # Deprecated: stage_loader.py now evaluates artifacts_present from stage YAML.
    # Kept for direct CLI usage; without args it cannot determine which artifacts.
    pass_check("artifacts_present delegated to stage_loader")


def check_previous_stage_completed(prev_stage_id: str) -> None:
    state = load_state()
    if state is None:
        fail("No state file found")
    prev_node = get_latest_node_for_stage(state, prev_stage_id)
    if prev_node and prev_node.get("status") == "completed":
        pass_check(f"previous stage '{prev_stage_id}' completed")
    fail(f"Previous stage '{prev_stage_id}' not completed")


def check_human_approved() -> None:
    state = load_state()
    if state is None:
        fail("No state file found")
    current_stage = state.get("current_run", {}).get("current_stage")
    if not current_stage:
        fail("No current stage in state")
    latest_node = get_latest_node_for_stage(state, current_stage)
    if latest_node and latest_node.get("gate_passed") and latest_node.get("approved_by"):
        pass_check(f"human approved for stage '{current_stage}'")
    fail(f"Stage '{current_stage}' not approved")


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

ENTRY_CHECKS = {
    "file_exists": check_file_exists,
    "artifact_exists": check_artifact_exists,
    "audio_format_supported": check_audio_format_supported,
    "previous_stage_completed": check_previous_stage_completed,
}

EXIT_CHECKS = {
    "file_exists": check_file_exists,
    "artifact_exists": check_artifact_exists,
    "artifacts_present": check_artifacts_present,
    "human_approved": check_human_approved,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Lincoln structural validators")
    parser.add_argument("--phase", required=True, choices=["entry", "exit"])
    parser.add_argument("--check", required=True)
    parser.add_argument("--args", default="", help="Comma-separated arguments for the check")
    parser.add_argument("--state-file", type=Path, default=None, help="Path to workflow state file")
    args = parser.parse_args()

    registry = ENTRY_CHECKS if args.phase == "entry" else EXIT_CHECKS
    check_fn = registry.get(args.check)
    if not check_fn:
        fail(f"Unknown check: {args.check}. Available: {', '.join(registry.keys())}")

    check_args = [a.strip() for a in args.args.split(",")] if args.args else []
    try:
        check_fn(*check_args)
    except TypeError as e:
        fail(f"Invalid arguments for check '{args.check}': {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
