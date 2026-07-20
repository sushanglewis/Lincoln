"""Tests for deterministic plugin packaging (#68)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SCRIPT = ROOT / "scripts" / "package-lincoln-plugin.py"


def _run(root: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    environment = {
        "HOME": str(Path.home()),
        "SOURCE_DATE_EPOCH": "0",
    }
    if env:
        environment.update(env)
    return subprocess.run(
        [sys.executable, str(PACKAGE_SCRIPT), "--root", str(root), *args],
        cwd=root,
        capture_output=True,
        text=True,
        env={**os.environ, **environment},
    )


def _make_minimal_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()

    (root / ".claude").mkdir()
    (root / ".claude" / "agents").mkdir()
    (root / ".claude" / "agents" / "default.md").write_text("---\n", encoding="utf-8")
    (root / ".claude-plugin").mkdir()
    (root / ".claude-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
    (root / "scripts").mkdir()
    (root / "scripts" / "stub.py").write_text("# stub\n", encoding="utf-8")
    (root / "tools").mkdir()
    (root / "tools" / "stub.py").write_text("# stub\n", encoding="utf-8")

    for name in ("README.md", "CLAUDE.md", "LICENSE", "RELEASE.md", "requirements.txt"):
        (root / name).write_text(f"# {name}\n", encoding="utf-8")

    (root / ".version-bump.json").write_text(
        '{"version": "9.9.9", "manifests": []}\n', encoding="utf-8"
    )

    subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "--quiet", "-m", "initial"], cwd=root, check=True)
    return root


def test_check_passes_on_clean_tree(tmp_path):
    root = _make_minimal_repo(tmp_path)
    result = _run(root, "check")
    assert result.returncode == 0, result.stderr
    assert "Package manifest OK" in result.stdout


def test_check_rejects_denylisted_path(tmp_path):
    root = _make_minimal_repo(tmp_path)
    (root / ".claude" / "oss").mkdir()
    (root / ".claude" / "oss" / "secret.txt").write_text("", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "--quiet", "-m", "add denylisted"], cwd=root, check=True)

    result = _run(root, "check")
    assert result.returncode == 1
    assert "denylist violation" in (result.stdout + result.stderr)


def test_check_dirty_rejects_dirty_tree(tmp_path):
    root = _make_minimal_repo(tmp_path)
    (root / "README.md").write_text("changed\n", encoding="utf-8")

    result = _run(root, "check", "--check-dirty")
    assert result.returncode == 1
    assert "uncommitted" in result.stderr.lower()


def test_package_refuses_dirty_tree(tmp_path):
    root = _make_minimal_repo(tmp_path)
    (root / "README.md").write_text("changed\n", encoding="utf-8")

    result = _run(root, "package")
    assert result.returncode == 1
    assert "dirty" in result.stderr.lower()


def test_package_builds_reproducible_archive(tmp_path):
    root = _make_minimal_repo(tmp_path)
    output_dir = root / "dist"

    result1 = _run(root, "package", "--output-dir", str(output_dir))
    assert result1.returncode == 0, result1.stderr

    archive = output_dir / "lincoln-9.9.9.tar.gz"
    checksum = output_dir / "lincoln-9.9.9.tar.gz.sha256"
    assert archive.exists()
    assert checksum.exists()

    # Clean and rebuild with the same SOURCE_DATE_EPOCH for byte reproducibility.
    os.remove(archive)
    os.remove(checksum)
    result2 = _run(root, "package", "--output-dir", str(output_dir))
    assert result2.returncode == 0, result2.stderr
    assert archive.read_bytes() == (output_dir / "lincoln-9.9.9.tar.gz").read_bytes()


def test_package_archive_excludes_denylisted_entries(tmp_path):
    root = _make_minimal_repo(tmp_path)
    output_dir = root / "dist"

    result = _run(root, "package", "--output-dir", str(output_dir))
    assert result.returncode == 0, result.stderr

    archive = output_dir / "lincoln-9.9.9.tar.gz"
    with tarfile.open(archive, "r:gz") as tar:
        names = tar.getnames()

    denylist_hits = {
        name
        for name in names
        if any(
            banned in Path(name).parts or name.startswith(banned.rstrip("/"))
            for banned in (".git", ".context", ".venv", "issue-", "__pycache__", ".DS_Store")
        )
    }
    assert not denylist_hits, f"denylist entries found in archive: {denylist_hits}"


def test_package_archive_has_normalized_timestamps(tmp_path):
    root = _make_minimal_repo(tmp_path)
    output_dir = root / "dist"

    result = _run(root, "package", "--output-dir", str(output_dir), env={"SOURCE_DATE_EPOCH": "0"})
    assert result.returncode == 0, result.stderr

    archive = output_dir / "lincoln-9.9.9.tar.gz"
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar.getmembers():
            assert member.mtime == 0, f"{member.name} mtime not normalized"
