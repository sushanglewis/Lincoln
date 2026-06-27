#!/usr/bin/env python3
"""
Track artifacts produced by side-effect tools and update workflow-state.yaml.

Usage:
    python scripts/track-artifacts.py --state-file .claude/workflow-state.yaml \
        --tool Write --args '{"file_path": "designs/foo/bar.md"}'
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml


# Paths that are considered workflow artifacts (relative to project root).
ARTIFACT_PREFIXES = (
    "interviews/",
    "requirements/",
    "designs/",
    "openspec/",
    "docs/knowledge/",
    ".github/linked-issues.yaml",
    ".github/lincoln-sync-queue/",
)


def load_state(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def save_state(path: Path, state: dict) -> None:
    path.write_text(yaml.dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")


def extract_paths(tool: str, args: str, project_root: Path) -> list[str]:
    """Extract relative file paths from tool arguments (best-effort)."""
    paths: list[str] = []

    # For Write/Edit the argument is JSON with file_path
    if tool in ("Write", "Edit"):
        try:
            data = json.loads(args)
            file_path = data.get("file_path") or data.get("path")
            if file_path:
                paths.append(str(file_path))
        except json.JSONDecodeError:
            pass

    # For Bash, scan for common output paths in the command string
    if tool == "Bash":
        try:
            data = json.loads(args)
            command = data.get("command", "")
        except json.JSONDecodeError:
            command = args
        # Match paths that look like output files
        for match in re.finditer(r"(?:\s|=|>\s?)([\w\-./]+\.(?:md|yaml|yml|json|pen))", command):
            paths.append(match.group(1))

    # For Pencil MCP tools, we can't easily know exported files; skip.

    # Normalize and filter to project-relative artifact paths
    result: list[str] = []
    for p in paths:
        p = p.strip().lstrip("/")
        if any(p.startswith(prefix) for prefix in ARTIFACT_PREFIXES):
            result.append(p)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-file", type=Path, required=True)
    parser.add_argument("--tool", required=True)
    parser.add_argument("--args", default="{}")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    if not args.state_file.exists():
        return 0

    state = load_state(args.state_file)
    current_stage = state.get("current_run", {}).get("current_stage")
    if not current_stage:
        return 0

    new_paths = extract_paths(args.tool, args.args, args.project_root)
    if not new_paths:
        return 0

    stage_state = state.setdefault("stages", {}).setdefault(current_stage, {})
    existing = set(stage_state.get("artifacts_produced", []))
    updated = existing | set(new_paths)
    stage_state["artifacts_produced"] = sorted(updated)
    save_state(args.state_file, state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
