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
from scripts.lincoln_index import (
    VERSION_COMMENT_RE,
    extract_html_markdown,
    extract_html_meta,
)
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
    if path.suffix == ".html":
        text = path.read_text(encoding="utf-8")
        match = VERSION_COMMENT_RE.search(text)
        return match.group(1) if match else None
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


def check_portal_index_exists() -> None:
    target = process_root() / "index.html"
    if not target.exists():
        fail(f"Portal index missing: {target}")
    pass_check(f"portal index exists: {target}")


# ---------------------------------------------------------------------------
# Schema 3.0.0 placeholder checks (registered but not yet implemented)
# ---------------------------------------------------------------------------


def check_artifact_meta_complete() -> None:
    """Verify that declared HTML artifacts carry the meta tags the portal needs."""
    state_file = resolve_state_path(None, PROJECT_ROOT)
    if not state_file or not state_file.exists():
        fail("No state file found")
    state = load_yaml(state_file)
    stage_id = state.get("current_run", {}).get("current_stage")
    if not stage_id:
        fail("No current stage in state")

    stage_path = PROJECT_ROOT / ".claude" / "stages" / f"{stage_id}.yaml"
    if not stage_path.exists():
        fail(f"Stage YAML not found: {stage_path}")
    stage = load_yaml(stage_path)

    variables = state.get("current_run", {}).get("variables", {})
    process_slug = str(variables.get("process_slug") or get_process_slug(state, state_file))

    artifacts = stage.get("artifacts", {})
    required = artifacts.get("required", [])
    html_artifacts = [str(art) for art in required if str(art).endswith(".html")]
    if not html_artifacts:
        pass_check("no HTML artifacts to check")

    missing: list[str] = []
    for art in html_artifacts:
        path = art.replace("{process_slug}", process_slug)
        for key, value in variables.items():
            path = path.replace(f"{{{key}}}", str(value))
        target = PROJECT_ROOT / path
        if "*" in path:
            # Glob artifact: check all present matches.
            for match in PROJECT_ROOT.glob(path):
                meta = extract_html_meta(match)
                rel = str(match.relative_to(PROJECT_ROOT))
                if not meta.get("nav_label"):
                    missing.append(f"{rel}: missing nav-label")
                if not meta.get("uid"):
                    missing.append(f"{rel}: missing doc-uid/page-uid")
            continue
        if not target.exists():
            missing.append(f"{path}: file not found")
            continue
        meta = extract_html_meta(target)
        if not meta.get("nav_label"):
            missing.append(f"{path}: missing nav-label")
        if not meta.get("uid"):
            missing.append(f"{path}: missing doc-uid/page-uid")

    if missing:
        fail("Artifact meta incomplete:\n  - " + "\n  - ".join(missing))
    pass_check("all HTML artifacts have required meta tags")


def check_ids_valid() -> None:
    """Placeholder: verify referenced IDs (session/design/change/etc.) are valid. Not yet implemented."""
    pass_check("not implemented")


def check_portal_index_fresh() -> None:
    """Placeholder: verify portal index is up to date with artifacts. Not yet implemented."""
    pass_check("not implemented")


# ---------------------------------------------------------------------------
# PRD checks
# ---------------------------------------------------------------------------


# 递进骨架（issue-129）：版本说明 → 修订记录 → 功能列表 → 需求展开。
# 章节编号不参与匹配，PM 可按需求类型在骨架内增插业务章节。
REQUIRED_PRD_SECTIONS = [
    "版本说明",
    "修订记录",
    "功能列表",
    "需求背景",
    "用户故事",
    "功能拆解",
    "业务流程图",
    "验收标准",
    "业务规则",
    "非功能需求",
    "关联系统/接口",
    "相关产物链接",
    "风险与开放问题",
]

PRD_SECTION_PATTERNS = [
    (name, re.compile(rf"^##\s*(?:\d+\s*[.、．]?\s*)?{re.escape(name)}\s*$", re.MULTILINE))
    for name in REQUIRED_PRD_SECTIONS
]

# PRD 正文禁则：过程性疑问在对话中解决，技术内容归归档页（issue-129 第 4/6 条）。
PRD_FORBIDDEN_PROCESS_RE = re.compile(r"待确认|待人类|待补充|待\s*PM|TODO|FIXME", re.IGNORECASE)
PRD_FORBIDDEN_TECH_HEADING_RE = re.compile(
    r"^##+\s*.*(技术调研|技术方案|可行性研究|架构设计|接口设计|数据库设计)",
    re.MULTILINE,
)

CROSS_VALIDATION_PASS_RE = re.compile(
    r"<!--\s*cross-validation:\s*pass\s+prd-version:\s*(v\d+\.\d+)\s*-->"
)


def _read_prd_text(target: Path) -> str:
    if target.suffix == ".html":
        return extract_html_markdown(target)
    return target.read_text(encoding="utf-8")


def _prd_hygiene_violations(text: str) -> list[str]:
    violations = sorted(set(PRD_FORBIDDEN_PROCESS_RE.findall(text)))
    violations.extend(sorted(set(PRD_FORBIDDEN_TECH_HEADING_RE.findall(text))))
    return violations


def check_prd_has_required_sections(path: str) -> None:
    target = PROJECT_ROOT / path
    if not target.exists():
        fail(f"PRD missing: {target}")

    text = _read_prd_text(target)

    missing = [name for name, pattern in PRD_SECTION_PATTERNS if not pattern.search(text)]
    if missing:
        fail(f"PRD missing required sections: {', '.join(missing)}")

    pass_check("PRD has all required sections")


def check_prd_content_hygiene(path: str) -> None:
    target = PROJECT_ROOT / path
    if not target.exists():
        fail(f"PRD missing: {target}")

    violations = _prd_hygiene_violations(_read_prd_text(target))
    if violations:
        fail(
            "PRD contains content that belongs in conversation or archived pages, "
            f"not the PRD: {', '.join(violations)}"
        )

    pass_check("PRD content hygiene OK")


def check_prd_snapshot_present(path: str) -> None:
    target = PROJECT_ROOT / path
    if not target.exists():
        fail(f"PRD missing: {target}")

    version = extract_markdown_version(target) if target.suffix != ".html" else _extract_document_version(target)
    if not version:
        fail(f"PRD missing version marker: {target}")

    if target.suffix == ".html":
        snapshot_path = target.parent / "snapshots" / f"prd-{version}.html"
    else:
        snapshot_path = target.with_name(f"prd-{version}.md")
    if not snapshot_path.exists():
        fail(f"PRD snapshot missing: {snapshot_path}. Run 'python scripts/lincoln_prd.py freeze' after approval.")

    pass_check(f"PRD snapshot present: {snapshot_path}")


def check_prd_cross_validated(path: str) -> None:
    target = PROJECT_ROOT / path
    if not target.exists():
        fail(f"Cross-validation report missing: {target}")

    match = CROSS_VALIDATION_PASS_RE.search(_read_prd_text(target))
    if not match:
        fail(
            "Cross-validation report has no pass marker. Every gap must be closed by a "
            "human-PM decision (PRD fix with re-freeze, or accepted with recorded "
            "rationale) before adding '<!-- cross-validation: pass prd-version: vX.Y -->'."
        )

    prd_path = target.parent / "prd.html"
    if not prd_path.exists():
        fail(f"PRD missing next to cross-validation report: {prd_path}")

    prd_version = _extract_document_version(prd_path)
    if prd_version != match.group(1):
        fail(
            f"Cross-validation pass marker is for PRD {match.group(1)}, but the PRD is now "
            f"{prd_version or 'unversioned'}. Re-run cross-validation against the current PRD."
        )

    violations = _prd_hygiene_violations(_read_prd_text(prd_path))
    if violations:
        fail(
            f"PRD regressed after cross-validation pass: {', '.join(violations)}. "
            "Fix the PRD, bump its version, re-freeze, and re-run cross-validation."
        )

    pass_check(f"PRD cross-validation pass marker matches PRD {prd_version}")


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

ENTRY_CHECKS = {
    "file_exists": check_file_exists,
    "artifact_exists": check_artifact_exists,
    "audio_format_supported": check_audio_format_supported,
    "previous_stage_completed": check_previous_stage_completed,
    "artifact_meta_complete": check_artifact_meta_complete,
    "ids_valid": check_ids_valid,
    "portal_index_fresh": check_portal_index_fresh,
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
    "prd_content_hygiene": check_prd_content_hygiene,
    "prd_cross_validated": check_prd_cross_validated,
    "portal_index_exists": check_portal_index_exists,
    "artifact_meta_complete": check_artifact_meta_complete,
    "ids_valid": check_ids_valid,
    "portal_index_fresh": check_portal_index_fresh,
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
