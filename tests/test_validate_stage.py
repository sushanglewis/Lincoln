"""Tests for scripts/validate_stage.py structural validators."""
import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_stage.py"


def load_validator_module():
    spec = importlib.util.spec_from_file_location("validate_stage", VALIDATOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def validator_mod():
    return load_validator_module()


@pytest.fixture
def state_file(tmp_path):
    """Create a minimal node-based workflow-stage.yaml."""
    state = {
        "schema_version": "2.0.0",
        "workflow": {"name": "test"},
        "current_run": {
            "run_id": "r1",
            "current_stage": "clarify",
            "status": "in_progress",
            "variables": {"process_slug": "test"},
            "started_at": "2026-07-06T00:00:00Z",
            "last_updated_at": "2026-07-06T00:00:00Z",
        },
        "nodes": [],
        "recovery": {},
    }
    path = tmp_path / "test" / "workflow-stage.yaml"
    path.parent.mkdir(parents=True)
    path.write_text(yaml.dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def _call_and_expect(validator_mod, monkeypatch, tmp_path, state_file, fn_name, args, project_root=None):
    project_root = project_root or tmp_path
    monkeypatch.setattr(validator_mod, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(validator_mod, "resolve_state_path", lambda _path=None, _root=None: state_file)
    fn = getattr(validator_mod, fn_name)
    return fn(*args)


# ---------------------------------------------------------------------------
# file_exists
# ---------------------------------------------------------------------------


def test_check_file_exists_passes(validator_mod, tmp_path, monkeypatch):
    target = tmp_path / "exists.txt"
    target.write_text("hello", encoding="utf-8")
    monkeypatch.setattr(validator_mod, "PROJECT_ROOT", tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_file_exists("exists.txt")
    assert exc_info.value.code == 0


def test_check_file_exists_fails(validator_mod, tmp_path, monkeypatch):
    monkeypatch.setattr(validator_mod, "PROJECT_ROOT", tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_file_exists("missing.txt")
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# artifact_exists
# ---------------------------------------------------------------------------


def test_check_artifact_exists_passes(validator_mod, tmp_path, monkeypatch, state_file):
    monkeypatch.setattr(validator_mod, "resolve_state_path", lambda _path=None, _root=None: state_file)
    slug_dir = tmp_path / "test"
    slug_dir.mkdir(exist_ok=True)
    target = slug_dir / "artifact.md"
    target.write_text("hello", encoding="utf-8")
    monkeypatch.setattr(validator_mod, "PROJECT_ROOT", tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_artifact_exists("artifact.md")
    assert exc_info.value.code == 0


def test_check_artifact_exists_fails_when_empty(validator_mod, tmp_path, monkeypatch, state_file):
    monkeypatch.setattr(validator_mod, "resolve_state_path", lambda _path=None, _root=None: state_file)
    slug_dir = tmp_path / "test"
    slug_dir.mkdir(exist_ok=True)
    target = slug_dir / "artifact.md"
    target.write_text("", encoding="utf-8")
    monkeypatch.setattr(validator_mod, "PROJECT_ROOT", tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_artifact_exists("artifact.md")
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# audio_format_supported
# ---------------------------------------------------------------------------


def test_check_audio_format_supported_passes(validator_mod):
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_audio_format_supported("recording.m4a")
    assert exc_info.value.code == 0


def test_check_audio_format_supported_fails(validator_mod):
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_audio_format_supported("recording.ogg")
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# previous_stage_completed
# ---------------------------------------------------------------------------


def test_check_previous_stage_completed_passes(validator_mod, tmp_path, monkeypatch, state_file):
    state = yaml.safe_load(state_file.read_text(encoding="utf-8"))
    state["nodes"].append({
        "stage_id": "ingest",
        "status": "completed",
    })
    state_file.write_text(yaml.dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
    monkeypatch.setattr(validator_mod, "resolve_state_path", lambda _path=None, _root=None: state_file)
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_previous_stage_completed("ingest")
    assert exc_info.value.code == 0


def test_check_previous_stage_completed_fails(validator_mod, tmp_path, monkeypatch, state_file):
    monkeypatch.setattr(validator_mod, "resolve_state_path", lambda _path=None, _root=None: state_file)
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_previous_stage_completed("ingest")
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# human_approved
# ---------------------------------------------------------------------------


def test_check_human_approved_passes(validator_mod, tmp_path, monkeypatch, state_file):
    state = yaml.safe_load(state_file.read_text(encoding="utf-8"))
    state["nodes"].append({
        "stage_id": "clarify",
        "status": "waiting_for_human",
        "gate_passed": True,
        "approved_by": "pm",
    })
    state_file.write_text(yaml.dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
    monkeypatch.setattr(validator_mod, "resolve_state_path", lambda _path=None, _root=None: state_file)
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_human_approved()
    assert exc_info.value.code == 0


def test_check_human_approved_fails(validator_mod, tmp_path, monkeypatch, state_file):
    monkeypatch.setattr(validator_mod, "resolve_state_path", lambda _path=None, _root=None: state_file)
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_human_approved()
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# artifacts_present
# ---------------------------------------------------------------------------


def test_check_artifacts_present_is_delegated(validator_mod):
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_artifacts_present()
    assert exc_info.value.code == 0


# ---------------------------------------------------------------------------
# CLI registry
# ---------------------------------------------------------------------------


def test_main_rejects_unknown_check(validator_mod, monkeypatch, state_file):
    monkeypatch.setattr(validator_mod, "resolve_state_path", lambda _path=None, _root=None: state_file)
    monkeypatch.setattr(sys, "argv", [
        "validate_stage.py", "--phase", "entry", "--check", "not_a_check",
    ])
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.main()
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# PRD checks
# ---------------------------------------------------------------------------


def test_check_prd_has_required_sections_passes(validator_mod, tmp_path, monkeypatch):
    monkeypatch.setattr(validator_mod, "PROJECT_ROOT", tmp_path)
    prd = tmp_path / "issue-52" / "prd.md"
    prd.parent.mkdir(parents=True)
    prd.write_text(
        "<!-- version: v1.0 -->\n"
        "# PRD\n\n"
        "## 1. 需求背景\n-\n"
        "## 2. 用户故事\n-\n"
        "## 3. 功能拆解\n-\n"
        "## 4. 业务流程图\n-\n"
        "## 5. 验收标准\n-\n"
        "## 6. 业务规则\n-\n"
        "## 7. 非功能需求\n-\n"
        "## 8. 关联系统/接口\n-\n"
        "## 9. 相关产物链接\n-\n"
        "## 10. 风险与开放问题\n-\n",
        encoding="utf-8",
    )
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_prd_has_required_sections("issue-52/prd.md")
    assert exc_info.value.code == 0


def test_check_prd_has_required_sections_fails_with_missing_list(validator_mod, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(validator_mod, "PROJECT_ROOT", tmp_path)
    prd = tmp_path / "issue-52" / "prd.md"
    prd.parent.mkdir(parents=True)
    prd.write_text("<!-- version: v1.0 -->\n# PRD\n", encoding="utf-8")
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_prd_has_required_sections("issue-52/prd.md")
    assert exc_info.value.code == 1
    captured = capsys.readouterr().out
    assert "需求背景" in captured or "用户故事" in captured


def test_check_prd_snapshot_present_passes(validator_mod, tmp_path, monkeypatch):
    monkeypatch.setattr(validator_mod, "PROJECT_ROOT", tmp_path)
    package = tmp_path / "issue-52"
    package.mkdir(parents=True)
    (package / "prd.md").write_text("<!-- version: v1.2 -->\n# PRD\n", encoding="utf-8")
    (package / "prd-v1.2.md").write_text("<!-- version: v1.2 -->\n# PRD\n", encoding="utf-8")
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_prd_snapshot_present("issue-52/prd.md")
    assert exc_info.value.code == 0


def test_check_prd_snapshot_present_fails_when_snapshot_missing(validator_mod, tmp_path, monkeypatch):
    monkeypatch.setattr(validator_mod, "PROJECT_ROOT", tmp_path)
    package = tmp_path / "issue-52"
    package.mkdir(parents=True)
    (package / "prd.md").write_text("<!-- version: v1.2 -->\n# PRD\n", encoding="utf-8")
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_prd_snapshot_present("issue-52/prd.md")
    assert exc_info.value.code == 1


def test_check_prd_snapshot_present_fails_when_marker_missing(validator_mod, tmp_path, monkeypatch):
    monkeypatch.setattr(validator_mod, "PROJECT_ROOT", tmp_path)
    package = tmp_path / "issue-52"
    package.mkdir(parents=True)
    (package / "prd.md").write_text("# PRD\n", encoding="utf-8")
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_prd_snapshot_present("issue-52/prd.md")
    assert exc_info.value.code == 1


def test_check_prd_has_required_sections_fails_when_prd_missing(validator_mod, tmp_path, monkeypatch):
    monkeypatch.setattr(validator_mod, "PROJECT_ROOT", tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_prd_has_required_sections("issue-52/prd.md")
    assert exc_info.value.code == 1


def test_check_prd_snapshot_present_fails_when_prd_missing(validator_mod, tmp_path, monkeypatch):
    monkeypatch.setattr(validator_mod, "PROJECT_ROOT", tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_prd_snapshot_present("issue-52/prd.md")
    assert exc_info.value.code == 1


def test_process_slug_fallback_to_state_file(validator_mod, tmp_path, monkeypatch):
    monkeypatch.delenv("LINCOLN_PROCESS_SLUG", raising=False)
    monkeypatch.setattr(validator_mod, "PROJECT_ROOT", tmp_path)
    state_file = tmp_path / "issue-52" / "workflow-stage.yaml"
    state_file.parent.mkdir(parents=True)
    state = {
        "current_run": {"variables": {"process_slug": "issue-52"}},
    }
    state_file.write_text(yaml.dump(state), encoding="utf-8")
    monkeypatch.setattr(validator_mod, "resolve_state_path", lambda _path=None, _root=None: state_file)
    assert validator_mod.process_slug() == "issue-52"


def test_process_slug_defaults_to_lc_process(validator_mod, tmp_path, monkeypatch):
    monkeypatch.delenv("LINCOLN_PROCESS_SLUG", raising=False)
    monkeypatch.setattr(validator_mod, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(validator_mod, "resolve_state_path", lambda _path=None, _root=None: None)
    assert validator_mod.process_slug() == "lc-process"


def test_load_state_returns_none_when_missing(validator_mod, monkeypatch):
    monkeypatch.setattr(validator_mod, "resolve_state_path", lambda _path=None, _root=None: None)
    assert validator_mod.load_state() is None


def test_load_state_returns_none_on_yaml_error(validator_mod, tmp_path, monkeypatch):
    state_file = tmp_path / "bad.yaml"
    state_file.write_text("not: valid: [", encoding="utf-8")
    monkeypatch.setattr(validator_mod, "resolve_state_path", lambda _path=None, _root=None: state_file)
    assert validator_mod.load_state() is None


def test_extract_yaml_version_returns_none_for_missing_file(validator_mod, tmp_path):
    assert validator_mod._extract_yaml_version(tmp_path / "missing.yaml") is None


def test_extract_yaml_version_returns_none_on_invalid_yaml(validator_mod, tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text("not: valid: [", encoding="utf-8")
    assert validator_mod._extract_yaml_version(path) is None


def test_extract_yaml_version_returns_none_when_not_mapping(validator_mod, tmp_path):
    path = tmp_path / "list.yaml"
    path.write_text("- one\n- two\n", encoding="utf-8")
    assert validator_mod._extract_yaml_version(path) is None


def test_extract_document_version_for_markdown(validator_mod, tmp_path):
    path = tmp_path / "doc.md"
    path.write_text("<!-- version: v4.5 -->\n# Doc\n", encoding="utf-8")
    assert validator_mod._extract_document_version(path) == "v4.5"


def test_extract_document_version_for_yaml(validator_mod, tmp_path):
    path = tmp_path / "doc.yaml"
    path.write_text("version: v2.0\n", encoding="utf-8")
    assert validator_mod._extract_document_version(path) == "v2.0"


def test_extract_document_version_for_unknown_extension(validator_mod, tmp_path):
    path = tmp_path / "doc.txt"
    path.write_text("version: v1.0\n", encoding="utf-8")
    assert validator_mod._extract_document_version(path) is None


def test_check_handoff_contract_valid_passes(validator_mod, tmp_path, monkeypatch):
    monkeypatch.setattr(validator_mod, "PROJECT_ROOT", tmp_path)
    handoff = tmp_path / "handoff.yaml"
    handoff.write_text(yaml.dump({
        "contract_version": "1.0",
        "issue_number": 85,
        "feature_slug": "issue-85",
        "from_stage": "clarify",
        "to_stage": "product-design-docs",
        "from_agent": "pm",
        "to_agent": "designer",
        "handoff_type": "human_master_doc",
        "human_master_doc": {"path": "prd.md", "version": "v1.0"},
        "based_on": [],
        "context_pack": [],
        "reading_rules": [],
        "open_questions": [],
        "approval": {},
    }), encoding="utf-8")
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_handoff_contract_valid("handoff.yaml")
    assert exc_info.value.code == 0


def test_check_handoff_contract_valid_fails_when_missing(validator_mod, tmp_path, monkeypatch):
    monkeypatch.setattr(validator_mod, "PROJECT_ROOT", tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_handoff_contract_valid("handoff.yaml")
    assert exc_info.value.code == 1


def test_check_handoff_versions_match_passes(validator_mod, tmp_path, monkeypatch):
    monkeypatch.setattr(validator_mod, "PROJECT_ROOT", tmp_path)
    package = tmp_path / "issue-85"
    package.mkdir(parents=True)
    (package / "prd.md").write_text("<!-- version: v1.0 -->\n# PRD\n", encoding="utf-8")
    handoff = tmp_path / "handoff.yaml"
    handoff.write_text(yaml.dump({
        "contract_version": "1.0",
        "issue_number": 85,
        "feature_slug": "issue-85",
        "from_stage": "clarify",
        "to_stage": "product-design-docs",
        "from_agent": "pm",
        "to_agent": "designer",
        "handoff_type": "human_master_doc",
        "human_master_doc": {"path": "issue-85/prd.md", "version": "v1.0"},
        "based_on": [{"path": "issue-85/prd.md", "version": "v1.0"}],
        "context_pack": [],
        "reading_rules": [],
        "open_questions": [],
        "approval": {},
    }), encoding="utf-8")
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_handoff_versions_match("handoff.yaml")
    assert exc_info.value.code == 0


def test_check_handoff_versions_match_fails_on_version_mismatch(validator_mod, tmp_path, monkeypatch):
    monkeypatch.setattr(validator_mod, "PROJECT_ROOT", tmp_path)
    package = tmp_path / "issue-85"
    package.mkdir(parents=True)
    (package / "prd.md").write_text("<!-- version: v1.1 -->\n# PRD\n", encoding="utf-8")
    handoff = tmp_path / "handoff.yaml"
    handoff.write_text(yaml.dump({
        "contract_version": "1.0",
        "issue_number": 85,
        "feature_slug": "issue-85",
        "from_stage": "clarify",
        "to_stage": "product-design-docs",
        "from_agent": "pm",
        "to_agent": "designer",
        "handoff_type": "human_master_doc",
        "human_master_doc": {"path": "issue-85/prd.md", "version": "v1.0"},
        "based_on": [{"path": "issue-85/prd.md", "version": "v1.0"}],
        "context_pack": [],
        "reading_rules": [],
        "open_questions": [],
        "approval": {},
    }), encoding="utf-8")
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_handoff_versions_match("handoff.yaml")
    assert exc_info.value.code == 1
