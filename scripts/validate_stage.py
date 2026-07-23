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
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lincoln_documents import extract_markdown_version
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
    return "lc-process"


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


def _extract_yaml_version(path: Path) -> str | None:
    """Read a top-level `version` or `contract_version` field from YAML."""
    if not path.exists():
        return None
    try:
        data = load_yaml(path)
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    return data.get("version") or data.get("contract_version")


def _extract_document_version(path: Path) -> str | None:
    if path.suffix in (".md", ".markdown"):
        return extract_markdown_version(path)
    if path.suffix in (".yaml", ".yml"):
        return _extract_yaml_version(path)
    return None


def check_handoff_contract_valid(path: str) -> None:
    target = PROJECT_ROOT / path
    if not target.exists():
        fail(f"Handoff contract missing: {target}")

    try:
        data = load_yaml(target)
    except Exception as exc:
        fail(f"Handoff contract is not valid YAML: {target} ({exc})")

    if not isinstance(data, dict):
        fail(f"Handoff contract must be a YAML mapping: {target}")

    required_keys = [
        "contract_version",
        "issue_number",
        "feature_slug",
        "from_stage",
        "to_stage",
        "from_agent",
        "to_agent",
        "handoff_type",
        "human_master_doc",
        "based_on",
        "context_pack",
        "reading_rules",
        "open_questions",
        "approval",
    ]
    missing = [key for key in required_keys if key not in data]
    if missing:
        fail(f"Handoff contract missing required keys: {', '.join(missing)}")

    human_doc = data.get("human_master_doc", {})
    if not human_doc.get("path") or not human_doc.get("version"):
        fail("Handoff contract human_master_doc must have path and version")

    pass_check(f"handoff contract valid: {target}")


def check_handoff_versions_match(path: str) -> None:
    target = PROJECT_ROOT / path
    if not target.exists():
        fail(f"Handoff contract missing: {target}")

    try:
        data = load_yaml(target)
    except Exception as exc:
        fail(f"Handoff contract is not valid YAML: {target} ({exc})")

    if not isinstance(data, dict):
        fail(f"Handoff contract must be a YAML mapping: {target}")

    based_on = data.get("based_on", [])
    if not isinstance(based_on, list):
        fail("Handoff contract based_on must be a list")

    mismatches = []
    for item in based_on:
        if not isinstance(item, dict):
            continue
        doc_path = item.get("path", "")
        expected_version = item.get("version", "")
        if not doc_path or not expected_version:
            continue
        full_path = PROJECT_ROOT / doc_path
        actual_version = _extract_document_version(full_path)
        if actual_version is None:
            mismatches.append(f"{doc_path}: could not detect version")
        elif actual_version != expected_version:
            mismatches.append(f"{doc_path}: expected {expected_version}, found {actual_version}")

    if mismatches:
        fail("Handoff version mismatches:\n  - " + "\n  - ".join(mismatches))

    pass_check("handoff versions match")


# ---------------------------------------------------------------------------
# PRD checks
# ---------------------------------------------------------------------------


REQUIRED_PRD_SECTIONS = [
    "## 1. 需求背景",
    "## 2. 用户故事",
    "## 3. 功能拆解",
    "## 4. 业务流程图",
    "## 5. 验收标准",
    "## 6. 业务规则",
    "## 7. 非功能需求",
    "## 8. 关联系统/接口",
    "## 9. 相关产物链接",
    "## 10. 风险与开放问题",
]


def check_prd_has_required_sections(path: str) -> None:
    target = PROJECT_ROOT / path
    if not target.exists():
        fail(f"PRD missing: {target}")

    text = target.read_text(encoding="utf-8")
    missing = [section for section in REQUIRED_PRD_SECTIONS if section not in text]
    if missing:
        fail(f"PRD missing required sections: {', '.join(missing)}")

    pass_check("PRD has all required sections")


def check_prd_snapshot_present(path: str) -> None:
    target = PROJECT_ROOT / path
    if not target.exists():
        fail(f"PRD missing: {target}")

    version = extract_markdown_version(target)
    if not version:
        fail(f"PRD missing version marker: {target}")

    snapshot_path = target.with_name(f"prd-{version}.md")
    if not snapshot_path.exists():
        fail(f"PRD snapshot missing: {snapshot_path}. Run 'python scripts/lincoln_prd.py freeze' after approval.")

    pass_check(f"PRD snapshot present: {snapshot_path}")


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
    "handoff_contract_valid": check_handoff_contract_valid,
    "handoff_versions_match": check_handoff_versions_match,
    "prd_has_required_sections": check_prd_has_required_sections,
    "prd_snapshot_present": check_prd_snapshot_present,
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
