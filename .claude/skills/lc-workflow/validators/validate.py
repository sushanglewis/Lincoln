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

PROJECT_ROOT = Path(__file__).resolve().parents[4]
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

try:
    from scripts.lincoln_documents import extract_markdown_version
except Exception:  # pragma: no cover - validator can be copied standalone
    extract_markdown_version = None  # type: ignore[assignment]

try:
    from scripts.lincoln_index import extract_html_markdown
except Exception:  # pragma: no cover - validator can be copied standalone
    extract_html_markdown = None  # type: ignore[assignment]


def fail(message: str):
    print(f"FAIL: {message}")
    sys.exit(1)


def pass_check(message: str = ""):
    print(f"PASS{' - ' + message if message else ''}")
    sys.exit(0)


def has_any_heading(content: str, aliases: list[str]) -> bool:
    return any(heading in content for heading in aliases)


def missing_heading_groups(content: str, required_groups: dict[str, list[str]]) -> list[str]:
    return [
        label
        for label, aliases in required_groups.items()
        if not has_any_heading(content, aliases)
    ]


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
    return "lc-process"


def process_root() -> Path:
    slug = process_slug()
    root = PROJECT_ROOT / slug
    if root.exists():
        return root
    return PROJECT_ROOT


def process_path(*parts: str) -> Path:
    return process_root().joinpath(*parts)


def doc_page(name: str) -> Path:
    """Return the path of an HTML doc page under pages/docs/."""
    return process_path("pages", "docs", f"{name}.html")


def read_document_file(path: Path) -> str:
    """Return document text; HTML doc pages yield their embedded Markdown source."""
    if path.suffix.lower() == ".html" and extract_html_markdown is not None:
        return extract_html_markdown(path)
    return path.read_text(encoding="utf-8")


def design_base(design_id: str) -> Path:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", design_id):
        fail(f"Invalid design_id '{design_id}'. Use kebab-case, e.g. checkout-redesign")
    return process_path("designs", design_id)


def require_nonempty_file(path: Path, label: str):
    if not path.exists() or not path.is_file() or path.stat().st_size == 0:
        fail(f"{label} missing or empty: {path}")


def read_required_file(path: Path, label: str) -> str:
    require_nonempty_file(path, label)
    return read_document_file(path)


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
    req = doc_page("requirements")
    if not req.exists():
        fail(f"Requirements document missing: {req}")
    content = read_document_file(req)
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
    content = read_required_file(doc_page("design-review"), "Design review")
    if not has_approval_marker(content, "设计文档"):
        fail("Product design docs are not marked as approved")
    pass_check(f"Product design approved: {design_id}")


def check_prototype_ready(design_id: str):
    validate_prototype_artifact_complete(design_id)
    content = read_required_file(doc_page("ui-spec"), "UI spec")
    if "<!-- prototype-status: approved -->" not in content and "[x] PM 已确认原型" not in content:
        fail("Prototype is not marked as approved")
    pass_check(f"Prototype ready: {design_id}")


def check_tdd_plan_ready(design_id: str):
    validate_tdd_plan_complete(design_id)
    content = read_required_file(doc_page("tdd-plan"), "TDD plan")
    if "<!-- status: ready-for-openspec -->" not in content:
        fail("TDD plan is not marked as ready for OpenSpec")
    pass_check(f"TDD plan ready: {design_id}")


# ---------------------------------------------------------------------------
# Exit checks
# ---------------------------------------------------------------------------

def check_transcript_has_timestamps(session_id: str):
    transcript = process_path("interviews", session_id, "transcript.md")
    if not transcript.exists():
        fail(f"Transcript missing: {transcript}")
    content = transcript.read_text(encoding="utf-8")
    if not re.search(r"\d{2}:\d{2}:\d{2}", content):
        fail("Transcript does not contain timestamps")
    pass_check()


def check_summary_has_key_topics(session_id: str):
    summary = process_path("interviews", session_id, "summary.md")
    if not summary.exists():
        fail(f"Summary missing: {summary}")
    content = summary.read_text(encoding="utf-8")
    required = {
        "关键主题": ["关键主题", "Key topics", "Key Topics"],
        "决策": ["决策", "Decisions"],
        "行动项": ["行动项", "Action items", "Action Items"],
    }
    missing = missing_heading_groups(content, required)
    if missing:
        fail(f"Summary missing sections: {', '.join(missing)}")
    pass_check()


def check_requirements_has_background_problem_solution_acceptance(session_id: str):
    req = doc_page("requirements")
    if not req.exists():
        fail(f"Requirements missing: {req}")
    content = read_document_file(req)
    required = {
        "背景": ["背景", "Background"],
        "问题": ["问题", "Problem"],
        "用户": ["用户", "Users", "Personas"],
        "方案": ["方案", "Proposed Solution", "Solution"],
        "验收标准": ["验收标准", "Acceptance Criteria"],
    }
    missing = missing_heading_groups(content, required)
    if missing:
        fail(f"Requirements missing sections: {', '.join(missing)}")
    pass_check()


def check_human_approved(session_id: str):
    req = doc_page("requirements")
    if not req.exists():
        fail(f"Requirements missing: {req}")
    content = read_document_file(req)
    if "<!-- status: approved -->" not in content and "[x] PM 已确认" not in content:
        fail("Human PM approval marker not found")
    pass_check()


def check_openspec_artifact_complete(change_name: str, design_id: str = ""):
    base = process_path("openspec", "changes", change_name)
    required_files = ["proposal.md", "design.md", "tasks.md"]
    required_dirs = ["specs"]
    for f in required_files:
        p = base / f
        if not p.exists() or p.stat().st_size == 0:
            fail(f"OpenSpec artifact missing or empty: {p}")
    for d in required_dirs:
        p = base / d
        if not p.exists() or not any(p.iterdir()):
            fail(f"OpenSpec artifact directory missing or empty: {p}")
    if design_id:
        slug = process_slug()
        required_refs = [
            f"{slug}/pages/docs/tdd-plan.html",
            f"{slug}/pages/prototype/",
            f"{slug}/pages/docs/design-review.html",
        ]
        combined = "\n".join((base / f).read_text(encoding="utf-8") for f in required_files)
        missing_refs = [ref for ref in required_refs if ref not in combined]
        if missing_refs:
            fail(f"OpenSpec artifact missing design references: {', '.join(missing_refs)}")
    pass_check()


def check_tasks_extracted(change_name: str):
    tasks = process_path("openspec", "changes", change_name, "tasks.md")
    if not tasks.exists():
        fail(f"Tasks file missing: {tasks}")
    content = tasks.read_text(encoding="utf-8")
    matches = re.findall(r"[-*]\s+\[.?\]\s+(.+)", content)
    if len(matches) < 1:
        fail("No tasks extracted from OpenSpec tasks.md")
    pass_check(f"{len(matches)} tasks found")


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
    req = doc_page("requirements")
    if not linked.exists():
        fail("Linked issues file missing")
    if not req.exists():
        fail("Requirements file missing")
    req_content = read_document_file(req)
    issues = re.findall(r"issue_number:\s*(\d+)", linked.read_text(encoding="utf-8"))
    missing = [i for i in issues if f"#{i}" not in req_content]
    if missing:
        fail(f"Requirements do not link back to issues: {', '.join(missing)}")
    pass_check()


def check_feature_doc_has_business_and_technical_sections(feature_slug: str):
    doc = PROJECT_ROOT / "docs" / "knowledge" / "03-features" / f"{feature_slug}.md"
    if not doc.exists():
        fail(f"Feature doc missing: {doc}")
    content = doc.read_text(encoding="utf-8")
    required = {
        "业务知识": ["业务知识", "Business Knowledge"],
        "技术知识": ["技术知识", "Technical Knowledge"],
    }
    missing = missing_heading_groups(content, required)
    if missing:
        fail(f"Feature doc missing sections: {', '.join(missing)}")
    pass_check()


def check_feature_doc_has_links(feature_slug: str):
    doc = PROJECT_ROOT / "docs" / "knowledge" / "03-features" / f"{feature_slug}.md"
    if not doc.exists():
        fail(f"Feature doc missing: {doc}")
    content = doc.read_text(encoding="utf-8")
    links = re.findall(r"\[\[([^\]]+)\]\]", content)
    if len(links) < 3:
        fail(f"Feature doc has too few wikilinks: {len(links)}")
    pass_check(f"{len(links)} wikilinks found")


def check_no_conflict_with_existing_knowledge(feature_slug: str):
    # Placeholder for semantic conflict detection.
    # v1: ensure no other feature doc has the same ID in frontmatter.
    doc = PROJECT_ROOT / "docs" / "knowledge" / "03-features" / f"{feature_slug}.md"
    if not doc.exists():
        fail(f"Feature doc missing: {doc}")
    content = doc.read_text(encoding="utf-8")
    id_match = re.search(r"^id:\s*(.+)$", content, re.MULTILINE)
    if not id_match:
        pass_check("No id in frontmatter; skipping conflict check")
    feat_id = id_match.group(1).strip()
    features_dir = PROJECT_ROOT / "docs" / "knowledge" / "03-features"
    conflicts = []
    for other in features_dir.glob("*.md"):
        if other.name == doc.name:
            continue
        other_content = other.read_text(encoding="utf-8")
        other_id_match = re.search(r"^id:\s*(.+)$", other_content, re.MULTILINE)
        if other_id_match and other_id_match.group(1).strip() == feat_id:
            conflicts.append(other.name)
    if conflicts:
        fail(f"Conflicting feature ID found in: {', '.join(conflicts)}")
    pass_check()


def validate_design_docs_complete(design_id: str):
    docs = [
        "design-review.html",
        "scenarios.html",
        "feature-catalog.html",
        "data-model.html",
        "flows.html",
        "feasibility.html",
    ]
    for doc in docs:
        require_nonempty_file(process_path("pages", "docs", doc), doc)

    review = read_required_file(doc_page("design-review"), "Design review")
    missing_links = [doc for doc in docs[1:] if doc not in review]
    if missing_links:
        fail(f"Design review missing links to: {', '.join(missing_links)}")

    flows = read_required_file(doc_page("flows"), "Flows")
    if "```mermaid" not in flows:
        fail("flows.html must contain at least one Mermaid diagram")

    feature_catalog = read_required_file(doc_page("feature-catalog"), "Feature catalog")
    if not has_any_heading(feature_catalog, ["验收", "Acceptance"]):
        fail("feature-catalog.html must map features to acceptance criteria")

    data_model = read_required_file(doc_page("data-model"), "Data model")
    if not has_any_heading(data_model, ["字段", "Field", "约束", "Constraint"]):
        fail("data-model.html must describe fields or constraints")

    feasibility = read_required_file(doc_page("feasibility"), "Feasibility")
    required = {
        "业务可行性": ["业务可行性", "Business feasibility"],
        "技术可行性": ["技术可行性", "Technical feasibility"],
        "开源项目": ["开源项目", "Open-source", "Open Source"],
        "技术框架": ["技术框架", "Framework"],
    }
    missing = missing_heading_groups(feasibility, required)
    if missing:
        fail(f"feasibility.html missing sections: {', '.join(missing)}")


def check_design_docs_complete(design_id: str):
    validate_design_docs_complete(design_id)
    pass_check(f"Design docs complete: {design_id}")


def check_design_docs_human_approved(design_id: str):
    validate_design_docs_complete(design_id)
    content = read_required_file(doc_page("design-review"), "Design review")
    if not has_approval_marker(content, "设计文档"):
        fail("Design docs approval marker not found")
    pass_check(f"Design docs approved: {design_id}")


def validate_prototype_artifact_complete(design_id: str):
    fields = read_required_file(doc_page("fields"), "Fields")
    ui_spec = read_required_file(doc_page("ui-spec"), "UI spec")

    prototype_dir = process_path("pages", "prototype")
    prototype_files = (
        [p for p in prototype_dir.rglob("*") if p.is_file() and p.name != ".gitkeep"]
        if prototype_dir.exists()
        else []
    )
    if not prototype_files:
        fail(f"Prototype artifact missing: no files under {prototype_dir}")

    html_files = [p for p in prototype_files if p.suffix.lower() == ".html"]
    missing_nav_label = [
        str(p.relative_to(process_root()))
        for p in html_files
        if '<meta name="nav-label"' not in p.read_text(encoding="utf-8")
    ]
    if missing_nav_label:
        fail(f"Prototype pages missing nav-label meta: {', '.join(missing_nav_label)}")

    required_annotation_metas = [
        ("doc-purpose", 'doc-purpose'),
        ("doc-layout", 'doc-layout'),
        ("doc-fields", 'doc-fields'),
        ("doc-boundaries", 'doc-boundaries'),
        ("doc-exceptions", 'doc-exceptions'),
    ]
    annotation_gaps: dict[str, list[str]] = {}
    for p in html_files:
        text = p.read_text(encoding="utf-8")
        missing = [name for label, name in required_annotation_metas if f'<meta name="{name}"' not in text]
        if missing:
            annotation_gaps[str(p.relative_to(process_root()))] = missing
    if annotation_gaps:
        messages = [f"{path}: missing {', '.join(metas)}" for path, metas in annotation_gaps.items()]
        fail(f"Prototype pages missing required annotation meta tags:\n" + "\n".join(messages))

    # Anti-pattern: in-app tray redraw. The system tray is portal-level chrome.
    in_app_tray_markers = [
        'class="menubar"',
        'class="tray-icon"',
        'class="tray-panel"',
        "bindTray(",
        "trayMenu(",
    ]
    in_app_tray_offenders = []
    for p in html_files:
        text = p.read_text(encoding="utf-8")
        if any(marker in text for marker in in_app_tray_markers):
            in_app_tray_offenders.append(str(p.relative_to(process_root())))
    if in_app_tray_offenders:
        fail(
            "Prototype pages redraw the system tray inside the app (anti-pattern). "
            "Tray scenarios must be thin controllers that postMessage 'lincoln-tray-state' to the portal. "
            "Offending pages: " + ", ".join(in_app_tray_offenders)
        )

    app_dir = prototype_dir / "app"
    app_html_files = (
        [p for p in app_dir.rglob("*.html") if p.is_file()]
        if app_dir.exists()
        else []
    )
    if app_html_files:
        tray_dir = app_dir / "tray"
        tray_pages = [p for p in tray_dir.rglob("*.html") if p.is_file()] if tray_dir.exists() else []
        if not tray_pages:
            fail("App-shell prototype detected but no tray scenario page found under pages/prototype/app/tray/")
        for tp in tray_pages:
            text = tp.read_text(encoding="utf-8")
            if 'lincoln-tray-state' not in text:
                fail(
                    f"Tray scenario page must postMessage 'lincoln-tray-state' to the portal: "
                    f"{tp.relative_to(process_root())}"
                )

    required_fields = {
        "字段": ["字段", "Field"],
        "校验": ["校验", "Validation"],
        "错误状态": ["错误状态", "Error"],
    }
    missing_fields = missing_heading_groups(fields, required_fields)
    if missing_fields:
        fail(f"fields.html missing sections: {', '.join(missing_fields)}")

    required_ui = {
        "界面": ["界面", "Screen", "UI"],
        "交互": ["交互", "Interaction"],
        "状态": ["状态", "State"],
    }
    missing_ui = missing_heading_groups(ui_spec, required_ui)
    if missing_ui:
        fail(f"ui-spec.html missing sections: {', '.join(missing_ui)}")


def check_prototype_artifact_complete(design_id: str):
    validate_prototype_artifact_complete(design_id)
    pass_check(f"Prototype artifacts complete: {design_id}")


def validate_tdd_plan_complete(design_id: str):
    content = read_required_file(doc_page("tdd-plan"), "TDD plan")
    required = {
        "验收映射": ["验收映射", "Acceptance mapping", "验收标准映射"],
        "测试场景": ["测试场景", "Test scenarios"],
        "红绿重构": ["红/绿/重构", "红绿重构", "Red/Green/Refactor"],
        "任务切片": ["任务切片", "Task slices"],
        "回归范围": ["回归范围", "Regression"],
    }
    missing = missing_heading_groups(content, required)
    if missing:
        fail(f"tdd-plan.html missing sections: {', '.join(missing)}")
    slug = process_slug()
    required_refs = [
        f"{slug}/pages/docs/requirements.html",
        f"{slug}/pages/docs/design-review.html",
        f"{slug}/pages/docs/fields.html",
        f"{slug}/pages/docs/ui-spec.html",
        f"{slug}/pages/prototype/",
    ]
    missing_refs = [ref for ref in required_refs if ref not in content]
    if missing_refs:
        fail(f"tdd-plan.html missing source references: {', '.join(missing_refs)}")


def check_tdd_plan_complete(design_id: str):
    validate_tdd_plan_complete(design_id)
    pass_check(f"TDD plan complete: {design_id}")


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


def check_prd_has_required_sections(path: str):
    target = PROJECT_ROOT / path
    if not target.exists():
        fail(f"PRD missing: {target}")

    text = read_document_file(target)
    missing = [section for section in REQUIRED_PRD_SECTIONS if section not in text]
    if missing:
        fail(f"PRD missing required sections: {', '.join(missing)}")

    pass_check("PRD has all required sections")


def check_prd_snapshot_present(path: str):
    target = PROJECT_ROOT / path
    if not target.exists():
        fail(f"PRD missing: {target}")

    if extract_markdown_version is None:
        fail("markdown version extraction is not available")

    version = extract_markdown_version(target)
    if not version:
        fail(f"PRD missing version marker: {target}")

    if target.suffix.lower() == ".html":
        snapshot_path = target.parent / "snapshots" / f"prd-{version}.html"
    else:
        snapshot_path = target.with_name(f"prd-{version}.md")
    if not snapshot_path.exists():
        fail(
            f"PRD snapshot missing: {snapshot_path}. "
            "Run 'python scripts/lincoln_prd.py freeze' after approval."
        )

    pass_check(f"PRD snapshot present: {snapshot_path}")


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
    "prd_has_required_sections": check_prd_has_required_sections,
    "prd_snapshot_present": check_prd_snapshot_present,
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
