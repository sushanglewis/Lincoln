"""Tests for scripts/lincoln_prd.py PRD freeze/migrate helper."""
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PRD_SCRIPT = ROOT / "scripts" / "lincoln_prd.py"


def load_prd_module():
    spec = importlib.util.spec_from_file_location("lincoln_prd", PRD_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def prd_mod():
    return load_prd_module()


@pytest.fixture
def sample_prd():
    return "# PRD: test\n\n<!-- version: v1.0 -->\n\n## 1. 需求背景\n\n- background\n"


# ---------------------------------------------------------------------------
# extract_version
# ---------------------------------------------------------------------------


def test_extract_version_reads_marker(prd_mod, tmp_path):
    path = tmp_path / "prd.md"
    path.write_text("<!-- version: v2.3 -->\n# PRD", encoding="utf-8")
    assert prd_mod.extract_version(path) == "v2.3"


def test_extract_version_returns_none_when_missing(prd_mod, tmp_path):
    path = tmp_path / "prd.md"
    path.write_text("# PRD\n", encoding="utf-8")
    assert prd_mod.extract_version(path) is None


# ---------------------------------------------------------------------------
# freeze
# ---------------------------------------------------------------------------


def test_freeze_creates_snapshot(prd_mod, tmp_path, sample_prd):
    package = tmp_path / "issue-52"
    package.mkdir()
    prd_path = package / "prd.md"
    prd_path.write_text(sample_prd, encoding="utf-8")

    prd_mod.freeze(package_root=package)

    snapshot = package / "prd-v1.0.md"
    assert snapshot.exists()
    assert snapshot.read_text(encoding="utf-8") == sample_prd


def test_freeze_refuses_overwrite(prd_mod, tmp_path, sample_prd):
    package = tmp_path / "issue-52"
    package.mkdir()
    prd_path = package / "prd.md"
    prd_path.write_text(sample_prd, encoding="utf-8")
    snapshot = package / "prd-v1.0.md"
    snapshot.write_text("existing", encoding="utf-8")

    with pytest.raises(RuntimeError, match="immutability"):
        prd_mod.freeze(package_root=package)


def test_freeze_fails_without_version_marker(prd_mod, tmp_path):
    package = tmp_path / "issue-52"
    package.mkdir()
    prd_path = package / "prd.md"
    prd_path.write_text("# PRD\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="version marker"):
        prd_mod.freeze(package_root=package)


# ---------------------------------------------------------------------------
# current_version
# ---------------------------------------------------------------------------


def test_current_version_returns_marker(prd_mod, tmp_path, sample_prd):
    package = tmp_path / "issue-52"
    package.mkdir()
    (package / "prd.md").write_text(sample_prd, encoding="utf-8")
    assert prd_mod.current_version(package_root=package) == "v1.0"


def test_current_version_fails_without_marker(prd_mod, tmp_path):
    package = tmp_path / "issue-52"
    package.mkdir()
    (package / "prd.md").write_text("# PRD\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="version marker"):
        prd_mod.current_version(package_root=package)


# ---------------------------------------------------------------------------
# migrate
# ---------------------------------------------------------------------------


def test_migrate_moves_legacy_prd_and_injects_marker(prd_mod, tmp_path):
    package = tmp_path / "issue-52"
    package.mkdir()
    legacy_dir = package / "requirements" / "2026-07-22-issue-52"
    legacy_dir.mkdir(parents=True)
    legacy_prd = legacy_dir / "prd.md"
    legacy_prd.write_text("# PRD\n", encoding="utf-8")

    prd_mod.migrate(package_root=package, session_id="2026-07-22-issue-52")

    root_prd = package / "prd.md"
    assert root_prd.exists()
    assert not legacy_prd.exists()
    content = root_prd.read_text(encoding="utf-8")
    assert "<!-- version: v1.0 -->" in content


def test_migrate_preserves_existing_marker(prd_mod, tmp_path):
    package = tmp_path / "issue-52"
    package.mkdir()
    legacy_dir = package / "requirements" / "2026-07-22-issue-52"
    legacy_dir.mkdir(parents=True)
    legacy_prd = legacy_dir / "prd.md"
    legacy_prd.write_text("<!-- version: v1.2 -->\n# PRD\n", encoding="utf-8")

    prd_mod.migrate(package_root=package, session_id="2026-07-22-issue-52")

    content = (package / "prd.md").read_text(encoding="utf-8")
    assert "<!-- version: v1.2 -->" in content


def test_migrate_fails_when_legacy_missing(prd_mod, tmp_path):
    package = tmp_path / "issue-52"
    package.mkdir()
    with pytest.raises(RuntimeError, match="legacy"):
        prd_mod.migrate(package_root=package, session_id="2026-07-22-issue-52")


def test_migrate_fails_when_root_prd_already_exists(prd_mod, tmp_path):
    package = tmp_path / "issue-52"
    package.mkdir()
    legacy_dir = package / "requirements" / "2026-07-22-issue-52"
    legacy_dir.mkdir(parents=True)
    (legacy_dir / "prd.md").write_text("# PRD\n", encoding="utf-8")
    (package / "prd.md").write_text("# Existing\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="already exists"):
        prd_mod.migrate(package_root=package, session_id="2026-07-22-issue-52")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_cli_freeze_invokes_function(prd_mod, tmp_path, sample_prd, monkeypatch):
    package = tmp_path / "issue-52"
    package.mkdir()
    (package / "prd.md").write_text(sample_prd, encoding="utf-8")
    monkeypatch.setattr(prd_mod, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        prd_mod, "resolve_state_path", lambda _path=None, _root=None: package / "workflow-stage.yaml"
    )
    monkeypatch.setattr(sys, "argv", ["lincoln_prd.py", "freeze"])

    with pytest.raises(SystemExit) as exc_info:
        prd_mod.main()
    assert exc_info.value.code == 0
    assert (package / "prd-v1.0.md").exists()


def test_cli_current_version_prints_version(tmp_path, sample_prd, monkeypatch):
    package = tmp_path / "issue-52"
    package.mkdir()
    (package / "prd.md").write_text(sample_prd, encoding="utf-8")
    monkeypatch.setenv("LINCOLN_PROCESS_SLUG", "issue-52")

    result = subprocess.run(
        [sys.executable, str(PRD_SCRIPT), "current-version"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "v1.0" in result.stdout


def test_cli_migrate_invokes_function(prd_mod, tmp_path, monkeypatch):
    package = tmp_path / "issue-52"
    package.mkdir()
    legacy_dir = package / "requirements" / "2026-07-22-issue-52"
    legacy_dir.mkdir(parents=True)
    (legacy_dir / "prd.md").write_text("# PRD\n", encoding="utf-8")
    monkeypatch.setenv("LINCOLN_PROCESS_SLUG", "issue-52")

    result = subprocess.run(
        [sys.executable, str(PRD_SCRIPT), "migrate", "--session-id", "2026-07-22-issue-52"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert (package / "prd.md").exists()


def test_freeze_requires_package_root(prd_mod):
    with pytest.raises(RuntimeError, match="package_root is required"):
        prd_mod.freeze()


def test_freeze_fails_when_prd_missing(prd_mod, tmp_path):
    package = tmp_path / "issue-52"
    package.mkdir()
    with pytest.raises(RuntimeError, match="prd.md not found"):
        prd_mod.freeze(package_root=package)


def test_current_version_requires_package_root(prd_mod):
    with pytest.raises(RuntimeError, match="package_root is required"):
        prd_mod.current_version()


def test_current_version_fails_when_prd_missing(prd_mod, tmp_path):
    package = tmp_path / "issue-52"
    package.mkdir()
    with pytest.raises(RuntimeError, match="prd.md not found"):
        prd_mod.current_version(package_root=package)


def test_migrate_requires_package_root(prd_mod):
    with pytest.raises(RuntimeError, match="package_root is required"):
        prd_mod.migrate(session_id="s1")


def test_migrate_requires_session_id(prd_mod, tmp_path):
    package = tmp_path / "issue-52"
    package.mkdir()
    with pytest.raises(RuntimeError, match="--session-id is required"):
        prd_mod.migrate(package_root=package)


def test_package_root_from_state_file(prd_mod, tmp_path, monkeypatch):
    monkeypatch.setattr(prd_mod, "PROJECT_ROOT", tmp_path)
    package = tmp_path / "issue-52"
    package.mkdir()
    state_file = package / "workflow-stage.yaml"
    state = {
        "current_run": {"variables": {"process_slug": "issue-52"}},
    }
    import yaml
    state_file.write_text(yaml.dump(state), encoding="utf-8")
    monkeypatch.setattr(
        prd_mod, "resolve_state_path", lambda _path=None, _root=None: state_file
    )

    args = prd_mod.argparse.Namespace()
    args.package = None
    assert prd_mod._package_root(args) == package


def test_package_root_state_load_failure_errors(prd_mod, tmp_path, monkeypatch):
    monkeypatch.setattr(prd_mod, "PROJECT_ROOT", tmp_path)
    package = tmp_path / "issue-52"
    package.mkdir()
    state_file = package / "workflow-stage.yaml"
    state_file.write_text("not: valid: [", encoding="utf-8")
    monkeypatch.setattr(
        prd_mod, "resolve_state_path", lambda _path=None, _root=None: state_file
    )

    args = prd_mod.argparse.Namespace()
    args.package = None
    with pytest.raises(RuntimeError, match="Could not determine package root"):
        prd_mod._package_root(args)


def test_cli_uses_env_slug_fallback_in_cwd(tmp_path, sample_prd):
    package = tmp_path / "issue-52"
    package.mkdir()
    (package / "prd.md").write_text(sample_prd, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(PRD_SCRIPT), "freeze"],
        cwd=str(tmp_path),
        env={**os.environ, "LINCOLN_PROCESS_SLUG": "issue-52"},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert (package / "prd-v1.0.md").exists()


def test_cli_env_slug_fallback_returns_cwd_candidate_on_error(tmp_path):
    result = subprocess.run(
        [sys.executable, str(PRD_SCRIPT), "freeze"],
        cwd=str(tmp_path),
        env={**os.environ, "LINCOLN_PROCESS_SLUG": "issue-52"},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "ERROR:" in result.stderr


def test_cli_freeze_failure_exits_one(tmp_path, sample_prd, monkeypatch):
    monkeypatch.setenv("LINCOLN_PROCESS_SLUG", "issue-52")
    result = subprocess.run(
        [sys.executable, str(PRD_SCRIPT), "freeze"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "ERROR:" in result.stderr
