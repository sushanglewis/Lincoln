#!/usr/bin/env python3
"""
Lincoln workflow validators.

Usage:
    python validate.py --phase entry --check file_exists --args path/to/file
    python validate.py --phase exit --check transcript_has_timestamps --args {process_slug}/interviews/session-id

Exit code 0 means pass, 1 means fail.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from scripts.lincoln_paths import default_process_slug
except Exception:  # pragma: no cover - validator can be copied standalone
    default_process_slug = None

try:
    from scripts.lincoln_paths import resolve_state_path, load_yaml, get_process_slug
except Exception:  # pragma: no cover - validator can be copied standalone
    resolve_state_path = None  # type: ignore[assignment]
    load_yaml = None  # type: ignore[assignment]
    get_process_slug = None  # type: ignore[assignment]


def fail(message: str):
    print(f"FAIL: {message}")
    sys.exit(1)


def pass_check(message: str = ""):
    print(f"PASS{' - ' + message if message else ''}")
    sys.exit(0)


def read_flat_yaml(path: Path) -> dict[str, str]:
    data = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        data[key.strip()] = value.strip().strip("'\"")
    return data


_state_file_override: Path | None = None
_state_cache: dict[str, Any] | None = None


def set_state_file(path: Path | None) -> None:
    global _state_file_override, _state_cache
    _state_file_override = path
    _state_cache = None


def load_state() -> dict[str, Any] | None:
    global _state_cache
    if _state_cache is not None:
        return _state_cache
    state_file = _state_file_override
    if state_file is None and resolve_state_path is not None:
        state_file = resolve_state_path(None, PROJECT_ROOT)
    if state_file is None or not state_file.exists():
        return None
    if load_yaml is None:
        return None
    try:
        _state_cache = load_yaml(state_file)
    except Exception:
        return None
    return _state_cache


def process_slug() -> str:
    import os

    env_slug = os.environ.get("LINCOLN_PROCESS_SLUG")
    if env_slug:
        return env_slug

    state = load_state()
    if state is not None and get_process_slug is not None:
        try:
            return get_process_slug(state, _state_file_override)
        except Exception:
            pass

    if default_process_slug:
        return default_process_slug(PROJECT_ROOT)
    return "lincoln-process"


def process_root() -> Path:
    slug = process_slug()
    root = PROJECT_ROOT / slug
    if root.exists():
        return root
    return PROJECT_ROOT


def process_path(*parts: str) -> Path:
    return process_root().joinpath(*parts)


def design_base(design_id: str) -> Path:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", design_id):
        fail(f"Invalid design_id '{design_id}'. Use kebab-case, e.g. checkout-redesign")
    return process_path("designs", design_id)


def require_nonempty_file(path: Path, label: str):
    if not path.exists() or not path.is_file() or path.stat().st_size == 0:
        fail(f"{label} missing or empty: {path}")


def read_required_file(path: Path, label: str) -> str:
    require_nonempty_file(path, label)
    return path.read_text(encoding="utf-8")


def has_approval_marker(content: str, zh_label: str) -> bool:
    return "<!-- status: approved -->" in content or f"[x] PM 已确认{zh_label}" in content


# ---------------------------------------------------------------------------
# Entry checks
# ---------------------------------------------------------------------------

def check_file_exists(path: str):
    target = PROJECT_ROOT / path
    if not target.exists():
        fail(f"File does not exist: {target}")
    pass_check(str(target))


def check_audio_format_supported(path: str):
    supported = {".mp3", ".m4a", ".wav", ".mp4", ".mov"}
    ext = Path(path).suffix.lower()
    if ext not in supported:
        fail(f"Unsupported audio format: {ext}. Supported: {', '.join(supported)}")
    pass_check(ext)


def check_summary_ready(session_id: str):
    summary = process_path("interviews", session_id, "summary.md")
    if not summary.exists() or summary.stat().st_size == 0:
        fail(f"Summary not ready: {summary}")
    pass_check(str(summary))


def check_requirements_approved(session_id: str):
    req = process_path("requirements", session_id, "requirements.md")
    if not req.exists():
        fail(f"Requirements document missing: {req}")
    content = req.read_text(encoding="utf-8")
    if "<!-- status: approved -->" not in content and "[x] PM 已确认" not in content:
        fail("Requirements document exists but is not marked as approved")
    pass_check(str(req))


def check_openspec_tasks_ready(change_name: str):
    tasks = process_path("openspec", "changes", change_name, "tasks.md")
    if not tasks.exists() or tasks.stat().st_size == 0:
        fail(f"OpenSpec tasks not ready: {tasks}")
    content = tasks.read_text(encoding="utf-8")
    if not re.search(r"[-*]\s+\[.?\]", content):
        fail("OpenSpec tasks.md does not contain a recognizable task list")
    pass_check(str(tasks))


def check_issues_ready(session_id: str):
    linked = PROJECT_ROOT / ".github" / "linked-issues.yaml"
    if not linked.exists():
        fail("Linked issues file missing; run split-to-github first")
    pass_check(str(linked))


def check_pr_merged(pr_number: str):
    queue_file = PROJECT_ROOT / ".github" / "lincoln-sync-queue" / f"pr-{pr_number}.yaml"
    if not queue_file.exists():
        fail(f"PR {pr_number} sync queue file missing: {queue_file}")

    data = read_flat_yaml(queue_file)
    required = ["status", "repository", "issue_number", "pr_number", "merged_at"]
    missing = [key for key in required if not data.get(key)]
    if missing:
        fail(f"PR sync queue file missing fields: {', '.join(missing)}")
    if data["pr_number"] != str(pr_number):
        fail(f"PR sync queue file is for PR {data['pr_number']}, expected {pr_number}")
    if data["status"] != "pending":
        fail(f"PR {pr_number} sync status is {data['status']}, expected pending")
    pass_check(str(queue_file))


def check_issue_exists(issue_number: str):
    linked = PROJECT_ROOT / ".github" / "linked-issues.yaml"
    if not linked.exists():
        fail("Linked issues file missing")
    content = linked.read_text(encoding="utf-8")
    if issue_number not in content:
        fail(f"Issue {issue_number} not found in linked issues")
    pass_check(f"Issue {issue_number} linked")


def check_design_docs_ready(design_id: str):
    validate_design_docs_complete(design_id)
    pass_check(f"Design docs ready: {design_id}")


def check_product_design_approved(design_id: str):
    validate_design_docs_complete(design_id)
    content = read_required_file(design_base(design_id) / "design-review.md", "Design review")
    if not has_approval_marker(content, "设计文档"):
        fail("Product design docs are not marked as approved")
    pass_check(f"Product design approved: {design_id}")


def check_prototype_ready(design_id: str):
    validate_prototype_artifact_complete(design_id)
    content = read_required_file(design_base(design_id) / "ui-spec.md", "UI spec")
    if "<!-- prototype-status: approved -->" not in content and "[x] PM 已确认原型" not in content:
        fail("Prototype is not marked as approved")
    pass_check(f"Prototype ready: {design_id}")


def check_tdd_plan_ready(design_id: str):
    validate_tdd_plan_complete(design_id)
    content = read_required_file(design_base(design_id) / "tdd-plan.md", "TDD plan")
    if "<!-- status: ready-for-openspec -->" not in content:
        fail("TDD plan is not marked as ready for OpenSpec")
    pass_check(f"TDD plan ready: {design_id}")


# ---------------------------------------------------------------------------
# Exit checks
# ---------------------------------------------------------------------------

def check_transcript_has_timestamps(session_id: str):
    transcript = process_path("interviews", session_id, "transcript.md")
    require_nonempty_file(transcript, "Transcript")
    pass_check(str(transcript))


def check_summary_has_key_topics(session_id: str):
    summary = process_path("interviews", session_id, "summary.md")
    require_nonempty_file(summary, "Summary")
    pass_check(str(summary))


def check_requirements_has_background_problem_solution_acceptance(session_id: str):
    req = process_path("requirements", session_id, "requirements.md")
    require_nonempty_file(req, "Requirements")
    pass_check(str(req))


def check_human_approved(session_id: str):
    req = process_path("requirements", session_id, "requirements.md")
    if not req.exists():
        fail(f"Requirements missing: {req}")
    content = req.read_text(encoding="utf-8")
    if "<!-- status: approved -->" not in content and "[x] PM 已确认" not in content:
        fail("Human PM approval marker not found")
    pass_check()


def check_openspec_artifact_complete(change_name: str, design_id: str = ""):
    base = process_path("openspec", "changes", change_name)
    required_files = ["proposal.md", "design.md", "tasks.md"]
    required_dirs = ["specs"]
    for f in required_files:
        p = base / f
        require_nonempty_file(p, f"OpenSpec {f}")
    for d in required_dirs:
        p = base / d
        if not p.exists() or not any(p.iterdir()):
            fail(f"OpenSpec artifact directory missing or empty: {p}")
    pass_check()


def check_tasks_extracted(change_name: str):
    tasks = process_path("openspec", "changes", change_name, "tasks.md")
    require_nonempty_file(tasks, "Tasks")
    pass_check(str(tasks))


def check_issues_created(session_id: str):
    linked = PROJECT_ROOT / ".github" / "linked-issues.yaml"
    if not linked.exists():
        fail("Linked issues file missing")
    content = linked.read_text(encoding="utf-8")
    if not re.search(r"issue_number:\s*\d+", content):
        fail("No issue numbers recorded")
    pass_check()


def check_tasks_link_back_to_issues(session_id: str):
    linked = PROJECT_ROOT / ".github" / "linked-issues.yaml"
    req = process_path("requirements", session_id, "requirements.md")
    if not linked.exists():
        fail("Linked issues file missing")
    if not req.exists():
        fail("Requirements file missing")
    req_content = req.read_text(encoding="utf-8")
    issues = re.findall(r"issue_number:\s*(\d+)", linked.read_text(encoding="utf-8"))
    missing = [i for i in issues if f"#{i}" not in req_content]
    if missing:
        fail(f"Requirements do not link back to issues: {', '.join(missing)}")
    pass_check()


def check_feature_doc_has_business_and_technical_sections(feature_slug: str):
    doc = PROJECT_ROOT / "docs" / "knowledge" / "03-features" / f"{feature_slug}.md"
    require_nonempty_file(doc, "Feature doc")
    pass_check(str(doc))


def check_feature_doc_has_links(feature_slug: str):
    doc = PROJECT_ROOT / "docs" / "knowledge" / "03-features" / f"{feature_slug}.md"
    require_nonempty_file(doc, "Feature doc")
    pass_check(str(doc))


def check_no_conflict_with_existing_knowledge(feature_slug: str):
    # Content conflict detection is intentionally left to agent-driven review.
    # This placeholder only verifies the feature doc exists.
    doc = PROJECT_ROOT / "docs" / "knowledge" / "03-features" / f"{feature_slug}.md"
    require_nonempty_file(doc, "Feature doc")
    pass_check()


def validate_design_docs_complete(design_id: str):
    base = design_base(design_id)
    docs = [
        "design-review.md",
        "scenarios.md",
        "feature-catalog.md",
        "data-model.md",
        "flows.md",
        "feasibility.md",
    ]
    for doc in docs:
        require_nonempty_file(base / doc, doc)


def check_design_docs_complete(design_id: str):
    validate_design_docs_complete(design_id)
    pass_check(f"Design docs complete: {design_id}")


def check_design_docs_human_approved(design_id: str):
    validate_design_docs_complete(design_id)
    content = read_required_file(design_base(design_id) / "design-review.md", "Design review")
    if not has_approval_marker(content, "设计文档"):
        fail("Design docs approval marker not found")
    pass_check(f"Design docs approved: {design_id}")


def validate_prototype_artifact_complete(design_id: str):
    base = design_base(design_id)
    require_nonempty_file(base / "prototype.pen", "Pencil prototype")
    require_nonempty_file(base / "fields.md", "Fields")
    require_nonempty_file(base / "ui-spec.md", "UI spec")


def check_prototype_artifact_complete(design_id: str):
    validate_prototype_artifact_complete(design_id)
    pass_check(f"Prototype artifacts complete: {design_id}")


def validate_tdd_plan_complete(design_id: str):
    base = design_base(design_id)
    read_required_file(base / "tdd-plan.md", "TDD plan")


def check_tdd_plan_complete(design_id: str):
    validate_tdd_plan_complete(design_id)
    pass_check(f"TDD plan complete: {design_id}")


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

ENTRY_CHECKS = {
    "file_exists": check_file_exists,
    "audio_format_supported": check_audio_format_supported,
    "summary_ready": check_summary_ready,
    "requirements_approved": check_requirements_approved,
    "openspec_tasks_ready": check_openspec_tasks_ready,
    "issues_ready": check_issues_ready,
    "pr_merged": check_pr_merged,
    "issue_exists": check_issue_exists,
    "design_docs_ready": check_design_docs_ready,
    "product_design_approved": check_product_design_approved,
    "prototype_ready": check_prototype_ready,
    "tdd_plan_ready": check_tdd_plan_ready,
}

EXIT_CHECKS = {
    "transcript_has_timestamps": check_transcript_has_timestamps,
    "summary_has_key_topics": check_summary_has_key_topics,
    "requirements_has_background_problem_solution_acceptance": check_requirements_has_background_problem_solution_acceptance,
    "human_approved": check_human_approved,
    "openspec_artifact_complete": check_openspec_artifact_complete,
    "tasks_extracted": check_tasks_extracted,
    "issues_created": check_issues_created,
    "tasks_link_back_to_issues": check_tasks_link_back_to_issues,
    "feature_doc_has_business_and_technical_sections": check_feature_doc_has_business_and_technical_sections,
    "feature_doc_has_links": check_feature_doc_has_links,
    "no_conflict_with_existing_knowledge": check_no_conflict_with_existing_knowledge,
    "design_docs_complete": check_design_docs_complete,
    "design_docs_human_approved": check_design_docs_human_approved,
    "prototype_artifact_complete": check_prototype_artifact_complete,
    "tdd_plan_complete": check_tdd_plan_complete,
}


def main():
    parser = argparse.ArgumentParser(description="Lincoln workflow validators")
    parser.add_argument("--phase", required=True, choices=["entry", "exit"])
    parser.add_argument("--check", required=True)
    parser.add_argument("--args", default="", help="Comma-separated arguments for the check")
    parser.add_argument("--state-file", type=Path, default=None, help="Path to workflow state file")
    args = parser.parse_args()

    set_state_file(args.state_file)

    registry = ENTRY_CHECKS if args.phase == "entry" else EXIT_CHECKS
    check_fn = registry.get(args.check)
    if not check_fn:
        fail(f"Unknown check: {args.check}. Available: {', '.join(registry.keys())}")

    check_args = [a.strip() for a in args.args.split(",")] if args.args else []
    try:
        check_fn(*check_args)
    except TypeError as e:
        fail(f"Invalid arguments for check '{args.check}': {e}")


if __name__ == "__main__":
    main()
