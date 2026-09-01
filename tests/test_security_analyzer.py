"""Tests for scripts/security_analyzer.py."""

import json
from pathlib import Path

import pytest
import yaml

from scripts.security_analyzer import analyze, load_policy


def _write_policy(root: Path, policies: list | None = None) -> Path:
    policy_dir = root / ".claude" / "policies"
    policy_dir.mkdir(parents=True, exist_ok=True)
    path = policy_dir / "security.yaml"
    data = {
        "schema_version": "1.0.0",
        "policies": policies
        or [
            {
                "name": "recursive-delete",
                "tool": "Bash",
                "condition": 'command matches "rm -r" or "rm -rf"',
                "level": "high",
                "message": "递归删除风险极高，需人工确认。",
                "confirm": True,
            },
            {
                "name": "file-deletion",
                "tool": "Bash",
                "condition": 'command matches any of ["rm", "rmdir"]',
                "level": "high",
                "message": "文件/目录删除操作不可逆，需人工确认。",
                "confirm": True,
            },
            {
                "name": "git-push",
                "tool": "Bash",
                "condition": 'command matches "git push"',
                "level": "medium",
                "message": "git push 将改变远程仓库状态。",
                "confirm": False,
                "log": True,
            },
            {
                "name": "external-api-call",
                "tool": "Bash",
                "condition": 'command matches any external HTTP client (curl, wget)',
                "level": "medium",
                "message": "正在调用外部 API。",
                "confirm": False,
                "log": True,
            },
            {
                "name": "file-write-outside-process",
                "tool": "Write|Edit",
                "condition": "target outside current process_slug",
                "level": "high",
                "message": "不允许写入当前 issue 工作包之外的产物目录。",
                "confirm": True,
            },
            {
                "name": "file-write-inside-process",
                "tool": "Write|Edit",
                "condition": "target inside current process_slug",
                "level": "medium",
                "message": "写入当前 issue 工作包内的文件。",
                "confirm": False,
                "log": True,
            },
        ],
    }
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


@pytest.fixture
def fake_repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    _write_policy(root)
    return root


def test_load_policy_reads_yaml(fake_repo):
    policy = load_policy(fake_repo)
    assert policy["schema_version"] == "1.0.0"
    assert len(policy["policies"]) == 6


def test_load_policy_returns_empty_when_missing(tmp_path):
    policy = load_policy(tmp_path / "repo")
    assert policy == {"policies": []}


def test_analyze_rm_is_high_and_requires_confirm(fake_repo):
    result = analyze(fake_repo, "Bash", {"command": "rm foo.txt"}, process_slug="issue-1")
    assert result["level"] == "high"
    assert result["confirm_required"] is True
    assert "删除" in result["message"]


def test_analyze_rm_rf_is_high_and_requires_confirm(fake_repo):
    result = analyze(fake_repo, "Bash", {"command": "rm -rf /tmp/bar"}, process_slug="issue-1")
    assert result["level"] == "high"
    assert result["confirm_required"] is True
    assert result["policy"] == "recursive-delete"


def test_analyze_git_push_is_medium_no_confirm(fake_repo):
    result = analyze(fake_repo, "Bash", {"command": "git push origin main"}, process_slug="issue-1")
    assert result["level"] == "medium"
    assert result["confirm_required"] is False
    assert result["log"] is True


def test_analyze_curl_is_medium_no_confirm(fake_repo):
    result = analyze(
        fake_repo, "Bash", {"command": "curl https://api.example.com"}, process_slug="issue-1"
    )
    assert result["level"] == "medium"
    assert result["confirm_required"] is False
    assert result["log"] is True


def test_analyze_safe_command_is_low(fake_repo):
    result = analyze(fake_repo, "Bash", {"command": "ls -la"}, process_slug="issue-1")
    assert result["level"] == "low"
    assert result["confirm_required"] is False


def test_analyze_write_inside_process_is_medium(fake_repo):
    result = analyze(
        fake_repo,
        "Write",
        {"file_path": "issue-1/docs/research/note.md"},
        process_slug="issue-1",
    )
    assert result["level"] == "medium"
    assert result["confirm_required"] is False


def test_analyze_write_outside_process_is_high(fake_repo):
    result = analyze(
        fake_repo,
        "Write",
        {"file_path": "issue-2/docs/research/note.md"},
        process_slug="issue-1",
    )
    assert result["level"] == "high"
    assert result["confirm_required"] is True


def test_analyze_logs_to_security_log(fake_repo, tmp_path):
    process_slug = "issue-1"
    log_dir = fake_repo / process_slug / "logs"
    log_dir.mkdir(parents=True)
    result = analyze(
        fake_repo,
        "Bash",
        {"command": "rm -rf foo"},
        process_slug=process_slug,
        log_dir=str(log_dir),
    )
    assert result["level"] == "high"
    log_file = log_dir / "security.log"
    assert log_file.exists()
    lines = log_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["tool"] == "Bash"
    assert entry["level"] == "high"
    assert entry["policy"] == "recursive-delete"
    assert entry["action"] == "blocked"


def test_analyze_respects_permissive_mode(fake_repo):
    import os

    os.environ["LINCOLN_SECURITY_MODE"] = "permissive"
    try:
        result = analyze(fake_repo, "Bash", {"command": "rm foo"}, process_slug="issue-1")
        assert result["level"] == "low"
        assert result["confirm_required"] is False
    finally:
        del os.environ["LINCOLN_SECURITY_MODE"]


def test_analyze_rm_with_sudo_prefix_is_blocked(fake_repo):
    result = analyze(fake_repo, "Bash", {"command": "sudo rm foo.txt"}, process_slug="issue-1")
    assert result["level"] == "high"
    assert result["confirm_required"] is True


def test_analyze_rm_after_cd_and_chain_is_blocked(fake_repo):
    result = analyze(fake_repo, "Bash", {"command": "cd /tmp && rm foo.txt"}, process_slug="issue-1")
    assert result["level"] == "high"
    assert result["confirm_required"] is True


def test_analyze_git_push_with_sudo_prefix_is_logged(fake_repo):
    result = analyze(fake_repo, "Bash", {"command": "sudo git push origin main"}, process_slug="issue-1")
    assert result["level"] == "medium"
    assert result["confirm_required"] is False
    assert result["log"] is True


def test_analyze_absolute_path_inside_package_is_allowed(fake_repo):
    target = str(fake_repo / "issue-1" / "docs" / "research" / "note.md")
    result = analyze(
        fake_repo,
        "Write",
        {"file_path": target},
        process_slug="issue-1",
    )
    assert result["level"] == "medium"
    assert result["confirm_required"] is False


def test_analyze_path_traversal_outside_package_is_blocked(fake_repo):
    target = str(fake_repo / "issue-1" / ".." / ".." / "etc" / "evil.md")
    result = analyze(
        fake_repo,
        "Write",
        {"file_path": target},
        process_slug="issue-1",
    )
    assert result["level"] == "high"
    assert result["confirm_required"] is True
