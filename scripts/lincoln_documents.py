#!/usr/bin/env python3
"""Maintain the per-package document index (documents.yaml).

The index lives in the issue-package root and summarizes, per document, which
stage produced it and whether it passed human confirmation, so agents can
understand package contents from a single file instead of scanning the tree.
It is regenerated from workflow-stage.yaml on every state mutation.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.lincoln_paths import STATE_FILENAME

DOCUMENTS_FILENAME = "documents.yaml"

# Matches master-handoff-pm-to-ux-v{MAJOR}.{MINOR}.md
HANDOFF_DOC_PATTERN = re.compile(r"handoffs/pm-to-ux/master-handoff-pm-to-ux-v(\d+)\.(\d+)\.md$")
HANDOFF_YAML_PATTERN = re.compile(r"handoffs/pm-to-ux/pm-to-ux\.handoff\.yaml$")


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def package_relative(path: str, process_slug: str) -> str:
    """Strip the '<process_slug>/' prefix from a repo-relative artifact path."""
    prefix = f"{process_slug}/"
    return path[len(prefix):] if path.startswith(prefix) else path


def is_team_package_state(state_path: Path) -> bool:
    """Only team issue packages (<slug>/workflow-stage.yaml) carry a document index."""
    return state_path.name == STATE_FILENAME and state_path.parent.name != ".claude"


def _extract_document_version(rel_path: str, project_root: Path, process_slug: str) -> str | None:
    """Detect version for PM→UX handoff documents; returns None for others."""
    full_path = project_root / process_slug / rel_path
    if not full_path.exists():
        return None

    md_match = HANDOFF_DOC_PATTERN.search(rel_path)
    if md_match:
        return f"v{md_match.group(1)}.{md_match.group(2)}"

    if HANDOFF_YAML_PATTERN.search(rel_path):
        try:
            data = yaml.safe_load(full_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data.get("human_master_doc", {}).get("version")
        except Exception:
            pass

    return None


def build_documents_index(
    state: dict[str, Any],
    process_slug: str,
    generated_at: str | None = None,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Build the index dict from state nodes; later/higher approvals win per path."""
    current_run = state.get("current_run", {})
    documents: dict[str, dict[str, Any]] = {}
    root = project_root or Path(__file__).resolve().parents[1]
    for node in state.get("nodes") or []:
        stage_id = str(node.get("stage_id") or "")
        for artifact in node.get("artifacts") or []:
            rel = package_relative(str(artifact), process_slug)
            entry = documents.setdefault(
                rel,
                {
                    "path": rel,
                    "stage": stage_id,
                    "status": "",
                    "gate_passed": False,
                    "human_confirmed": False,
                    "approved_by": None,
                    "version": None,
                },
            )
            entry["stage"] = stage_id or entry["stage"]
            entry["status"] = str(node.get("status") or "") or entry["status"]
            version = _extract_document_version(rel, root, process_slug)
            if version:
                entry["version"] = version
            if not node.get("gate_passed"):
                continue
            entry["gate_passed"] = True
            approver = node.get("approved_by")
            if approver and str(approver).startswith("human"):
                entry["human_confirmed"] = True
                entry["approved_by"] = approver
            elif not entry["approved_by"]:
                entry["approved_by"] = approver

    return {
        "process_slug": process_slug,
        "issue_number": str(current_run.get("issue_number") or ""),
        "current_stage": str(current_run.get("current_stage") or ""),
        "last_updated": generated_at or now_iso(),
        "documents": sorted(documents.values(), key=lambda d: d["path"]),
    }


def write_documents_index(
    state: dict[str, Any],
    state_path: Path,
    generated_at: str | None = None,
) -> Path | None:
    """Regenerate documents.yaml next to a team package state file; else return None."""
    if not is_team_package_state(state_path):
        return None
    project_root = state_path.parents[1]
    index = build_documents_index(state, state_path.parent.name, generated_at, project_root)
    index_path = state_path.parent / DOCUMENTS_FILENAME
    index_path.write_text(
        yaml.dump(index, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )
    return index_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate the issue-package document index")
    parser.add_argument("--state-file", required=True, help="Path to the package workflow-stage.yaml")
    args = parser.parse_args()

    state_path = Path(args.state_file).resolve()
    if not state_path.is_file():
        print(f"ERROR: state file not found: {state_path}", file=sys.stderr)
        return 1
    state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    index_path = write_documents_index(state, state_path)
    if index_path is None:
        print(f"SKIP: {state_path} is not a team issue-package state file")
        return 0
    print(f"Updated {index_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
