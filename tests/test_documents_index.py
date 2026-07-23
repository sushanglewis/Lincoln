import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.lincoln_documents import (  # noqa: E402
    build_documents_index,
    extract_markdown_version,
    is_team_package_state,
    package_relative,
    write_documents_index,
)


def make_state(nodes, issue_number="52", current_stage="clarify"):
    return {
        "schema_version": "2.0.0",
        "current_run": {
            "issue_number": issue_number,
            "current_stage": current_stage,
            "variables": {"process_slug": "issue-52"},
        },
        "nodes": nodes,
        "recovery": {},
    }


def test_package_relative_strips_process_slug():
    assert package_relative("issue-52/requirements/s/prd.md", "issue-52") == "requirements/s/prd.md"
    assert package_relative("knowledge/03-features/x.md", "issue-52") == "knowledge/03-features/x.md"


def test_build_index_merges_duplicate_artifacts_preferring_human_approval():
    state = make_state([
        {
            "stage_id": "clarify",
            "node_id": "clarify-1",
            "status": "in_progress",
            "gate_passed": False,
            "approved_by": None,
            "artifacts": ["issue-52/requirements/s/prd.md"],
        },
        {
            "stage_id": "clarify",
            "node_id": "clarify-2",
            "status": "completed",
            "gate_passed": True,
            "approved_by": "human-pm",
            "artifacts": ["issue-52/requirements/s/prd.md"],
        },
        {
            "stage_id": "clarify",
            "node_id": "clarify-completed",
            "status": "completed",
            "gate_passed": True,
            "approved_by": "system",
            "artifacts": ["issue-52/requirements/s/prd.md"],
        },
    ])
    index = build_documents_index(state, "issue-52", generated_at="2026-07-14T00:00:00Z")
    assert index["issue_number"] == "52"
    assert index["current_stage"] == "clarify"
    assert index["last_updated"] == "2026-07-14T00:00:00Z"
    assert len(index["documents"]) == 1
    doc = index["documents"][0]
    assert doc["path"] == "requirements/s/prd.md"
    assert doc["stage"] == "clarify"
    assert doc["status"] == "completed"
    assert doc["gate_passed"] is True
    assert doc["human_confirmed"] is True
    assert doc["approved_by"] == "human-pm"


def test_build_index_marks_unconfirmed_documents():
    state = make_state([
        {
            "stage_id": "ingest",
            "node_id": "ingest-1",
            "status": "in_progress",
            "gate_passed": False,
            "approved_by": None,
            "artifacts": ["issue-52/interviews/s/summary.md"],
        },
    ])
    index = build_documents_index(state, "issue-52")
    doc = index["documents"][0]
    assert doc["gate_passed"] is False
    assert doc["human_confirmed"] is False
    assert doc["approved_by"] is None


def test_write_documents_index_only_for_team_packages(tmp_path):
    package = tmp_path / "issue-52"
    package.mkdir()
    state_file = package / "workflow-stage.yaml"
    state = make_state([])
    state_file.write_text(yaml.dump(state), encoding="utf-8")

    index_path = write_documents_index(state, state_file, generated_at="2026-07-14T00:00:00Z")
    assert index_path == package / "documents.yaml"
    written = yaml.safe_load(index_path.read_text(encoding="utf-8"))
    assert written["process_slug"] == "issue-52"
    assert written["documents"] == []

    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    root_state = claude_dir / "workflow-stage.yaml"
    root_state.write_text(yaml.dump(state), encoding="utf-8")
    assert write_documents_index(state, root_state) is None
    assert not (claude_dir / "documents.yaml").exists()

    solo_state = tmp_path / ".context" / "workflow" / "bug-fix.yaml"
    solo_state.parent.mkdir(parents=True)
    solo_state.write_text(yaml.dump(state), encoding="utf-8")
    assert write_documents_index(state, solo_state) is None
    assert is_team_package_state(state_file) is True
    assert is_team_package_state(solo_state) is False


def test_cli_regenerates_index(tmp_path):
    package = tmp_path / "issue-52"
    package.mkdir()
    state = make_state([
        {
            "stage_id": "ingest",
            "node_id": "ingest-1",
            "status": "completed",
            "gate_passed": True,
            "approved_by": "system",
            "artifacts": ["issue-52/interviews/s/transcript.md"],
        },
    ])
    state_file = package / "workflow-stage.yaml"
    state_file.write_text(yaml.dump(state), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "lincoln_documents.py"), "--state-file", str(state_file)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    written = yaml.safe_load((package / "documents.yaml").read_text(encoding="utf-8"))
    assert written["documents"][0]["path"] == "interviews/s/transcript.md"
    assert written["documents"][0]["gate_passed"] is True
    assert written["documents"][0]["human_confirmed"] is False


def test_build_index_extracts_root_prd_version_from_marker(tmp_path):
    package = tmp_path / "issue-52"
    package.mkdir()
    prd = package / "prd.md"
    prd.write_text("<!-- version: v1.1 -->\n# PRD", encoding="utf-8")

    state = make_state([
        {
            "stage_id": "clarify",
            "node_id": "clarify-1",
            "status": "completed",
            "gate_passed": True,
            "approved_by": "human-pm",
            "artifacts": ["issue-52/prd.md"],
        },
    ])
    index = build_documents_index(state, "issue-52", project_root=tmp_path)
    docs = {d["path"]: d for d in index["documents"]}
    assert docs["prd.md"]["version"] == "v1.1"
    assert docs["prd.md"]["human_confirmed"] is True


def test_build_index_extracts_prd_snapshot_version_from_filename(tmp_path):
    package = tmp_path / "issue-52"
    package.mkdir()
    (package / "prd-v1.0.md").write_text("# PRD", encoding="utf-8")

    state = make_state([
        {
            "stage_id": "clarify",
            "node_id": "clarify-1",
            "status": "completed",
            "gate_passed": True,
            "approved_by": "human-pm",
            "artifacts": ["issue-52/prd-v1.0.md"],
        },
    ])
    index = build_documents_index(state, "issue-52", project_root=tmp_path)
    docs = {d["path"]: d for d in index["documents"]}
    assert docs["prd-v1.0.md"]["version"] == "v1.0"


def test_build_index_extracts_legacy_prd_version_from_marker(tmp_path):
    package = tmp_path / "issue-52"
    legacy_dir = package / "requirements" / "2026-07-22-issue-52"
    legacy_dir.mkdir(parents=True)
    (legacy_dir / "prd.md").write_text("<!-- version: v1.3 -->\n# PRD", encoding="utf-8")

    state = make_state([
        {
            "stage_id": "clarify",
            "node_id": "clarify-1",
            "status": "completed",
            "gate_passed": True,
            "approved_by": "human-pm",
            "artifacts": ["issue-52/requirements/2026-07-22-issue-52/prd.md"],
        },
    ])
    index = build_documents_index(state, "issue-52", project_root=tmp_path)
    docs = {d["path"]: d for d in index["documents"]}
    assert docs["requirements/2026-07-22-issue-52/prd.md"]["version"] == "v1.3"


def test_build_index_prd_version_null_when_marker_missing(tmp_path):
    package = tmp_path / "issue-52"
    package.mkdir()
    (package / "prd.md").write_text("# PRD", encoding="utf-8")

    state = make_state([
        {
            "stage_id": "clarify",
            "node_id": "clarify-1",
            "status": "completed",
            "gate_passed": True,
            "approved_by": "human-pm",
            "artifacts": ["issue-52/prd.md"],
        },
    ])
    index = build_documents_index(state, "issue-52", project_root=tmp_path)
    docs = {d["path"]: d for d in index["documents"]}
    assert docs["prd.md"]["version"] is None


def test_extract_markdown_version_returns_none_for_missing_file(tmp_path):
    missing = tmp_path / "missing.md"
    assert extract_markdown_version(missing) is None


def test_build_index_extracts_handoff_doc_version_from_filename(tmp_path):
    package = tmp_path / "issue-52"
    handoff_dir = package / "handoffs" / "pm-to-ux"
    handoff_dir.mkdir(parents=True)
    (handoff_dir / "master-handoff-pm-to-ux-v2.1.md").write_text("# Handoff", encoding="utf-8")

    state = make_state([
        {
            "stage_id": "product-design-docs",
            "node_id": "design-1",
            "status": "completed",
            "gate_passed": True,
            "approved_by": "human-pm",
            "artifacts": ["issue-52/handoffs/pm-to-ux/master-handoff-pm-to-ux-v2.1.md"],
        },
    ])
    index = build_documents_index(state, "issue-52", project_root=tmp_path)
    docs = {d["path"]: d for d in index["documents"]}
    assert docs["handoffs/pm-to-ux/master-handoff-pm-to-ux-v2.1.md"]["version"] == "v2.1"


def test_build_index_extracts_handoff_yaml_version(tmp_path):
    package = tmp_path / "issue-52"
    handoff_dir = package / "handoffs" / "pm-to-ux"
    handoff_dir.mkdir(parents=True)
    yaml_path = handoff_dir / "pm-to-ux.handoff.yaml"
    yaml_path.write_text(
        yaml.safe_dump({"human_master_doc": {"version": "v3.0"}}),
        encoding="utf-8",
    )

    state = make_state([
        {
            "stage_id": "product-design-docs",
            "node_id": "design-1",
            "status": "completed",
            "gate_passed": True,
            "approved_by": "human-pm",
            "artifacts": ["issue-52/handoffs/pm-to-ux/pm-to-ux.handoff.yaml"],
        },
    ])
    index = build_documents_index(state, "issue-52", project_root=tmp_path)
    docs = {d["path"]: d for d in index["documents"]}
    assert docs["handoffs/pm-to-ux/pm-to-ux.handoff.yaml"]["version"] == "v3.0"


def test_build_index_records_non_human_approver_when_no_human_exists(tmp_path):
    package = tmp_path / "issue-52"
    package.mkdir()
    (package / "artifact.md").write_text("x", encoding="utf-8")

    state = make_state([
        {
            "stage_id": "clarify",
            "node_id": "clarify-1",
            "status": "completed",
            "gate_passed": True,
            "approved_by": "system",
            "artifacts": ["issue-52/artifact.md"],
        },
    ])
    index = build_documents_index(state, "issue-52", project_root=tmp_path)
    doc = index["documents"][0]
    assert doc["approved_by"] == "system"
    assert doc["human_confirmed"] is False


def test_cli_skips_non_team_state_file(tmp_path):
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    state_file = claude_dir / "workflow-stage.yaml"
    state_file.write_text(yaml.dump(make_state([])), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "lincoln_documents.py"), "--state-file", str(state_file)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "SKIP" in result.stdout


def test_cli_fails_when_state_file_missing(tmp_path):
    missing = tmp_path / "missing.yaml"
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "lincoln_documents.py"), "--state-file", str(missing)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "ERROR" in result.stderr
