"""Tests for scripts/lincoln_dependency_manager.py."""

import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from scripts.lincoln_dependency_manager import (
    check_clis,
    check_skills,
    detect_platform,
    get_install_command,
    init_openspec_config,
    install_cli,
    install_skill,
    load_dependencies,
)


@pytest.fixture
def project_root():
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def sample_manifest():
    return {
        "schema_version": "1.0.0",
        "skills": {
            "superpowers": {
                "source": "https://github.com/obra/superpowers.git",
                "ref": "main",
                "type": "skill",
                "required": True,
                "license": "MIT",
            },
            "gsd": {
                "source": "https://github.com/gsd-build/get-shit-done.git",
                "ref": "main",
                "type": "skill",
                "required": True,
                "license": "MIT",
            },
            "openspec": {
                "source": "https://github.com/Fission-AI/openspec.git",
                "ref": "v0.5.0",
                "type": "cli",
                "binary": "openspec",
                "required": True,
                "platforms": {
                    "macos": "npm install -g @fission-ai/openspec",
                    "linux": "npm install -g @fission-ai/openspec",
                },
            },
            "gh": {
                "source": "https://cli.github.com/",
                "type": "cli",
                "binary": "gh",
                "required": True,
                "platforms": {
                    "macos": "brew install gh",
                    "linux": "sudo apt-get install gh",
                },
            },
            "oh-my-claudecode": {
                "source": "https://github.com/Yeachan-Heo/oh-my-claudecode.git",
                "ref": "main",
                "type": "plugin",
                "required": False,
                "default_install": True,
                "license": "MIT",
                "platforms": {
                    "macos": "git clone --branch main ...",
                    "linux": "git clone --branch main ...",
                },
            },
            "lc-status": {
                "source": "inline",
                "type": "skill",
                "path": ".claude/skills/lc-status",
                "required": True,
            },
        },
    }


def test_load_dependencies_reads_yaml(project_root):
    manifest = load_dependencies(project_root)
    assert manifest["schema_version"] == "1.0.0"
    assert "superpowers" in manifest["skills"]
    assert "openspec" in manifest["skills"]


def test_load_dependencies_raises_when_file_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_dependencies(tmp_path)


def test_detect_platform_returns_macos_or_linux():
    platform = detect_platform()
    assert platform in ("macos", "linux", None)


@patch("scripts.lincoln_dependency_manager.shutil.which")
def test_check_clis_returns_missing_only(mock_which, sample_manifest):
    def fake_which(cmd):
        return "/usr/bin/gh" if cmd == "gh" else None

    mock_which.side_effect = fake_which
    missing = check_clis(sample_manifest)

    names = {m["name"] for m in missing}
    assert "openspec" in names
    assert "gh" not in names
    assert "oh-my-claudecode" not in names  # plugin handled by check_skills


@patch("scripts.lincoln_dependency_manager.shutil.which")
def test_check_clis_includes_install_command(mock_which, sample_manifest):
    mock_which.return_value = None
    missing = check_clis(sample_manifest, platform_name="macos")

    openspec = next(m for m in missing if m["name"] == "openspec")
    assert openspec["install_command"] == "npm install -g @fission-ai/openspec"


def test_check_skills_returns_missing_external_skills(tmp_path, sample_manifest):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    # Create the inline skill file so only external skills are reported missing.
    inline_path = tmp_path / ".claude" / "skills" / "lc-status"
    (inline_path / "SKILL.md").parent.mkdir(parents=True)
    (inline_path / "SKILL.md").write_text("# skill", encoding="utf-8")
    # Don't create superpowers or gsd directories
    missing = check_skills(sample_manifest, tmp_path, skills_dir)

    names = {m["name"] for m in missing}
    assert "superpowers" in names
    assert "gsd" in names
    assert "lc-status" not in names  # inline skill present in repo
    assert "oh-my-claudecode" in names  # default_install plugin


def test_check_skills_skips_present_skills(tmp_path, sample_manifest):
    skills_dir = tmp_path / "skills"
    (skills_dir / "superpowers" / "SKILL.md").parent.mkdir(parents=True)
    (skills_dir / "superpowers" / "SKILL.md").write_text("# skill", encoding="utf-8")

    missing = check_skills(sample_manifest, tmp_path, skills_dir)
    names = {m["name"] for m in missing}
    assert "superpowers" not in names
    assert "gsd" in names


def test_check_skills_inline_skill_missing(tmp_path, sample_manifest):
    missing = check_skills(sample_manifest, tmp_path, tmp_path / "skills")
    inline = [m for m in missing if m["name"] == "lc-status"]
    assert len(inline) == 1
    assert inline[0]["type"] == "skill"
    assert "inline" in inline[0]["source"]


def test_get_install_command_for_cli(sample_manifest):
    openspec = sample_manifest["skills"]["openspec"]
    assert get_install_command(openspec, "macos") == "npm install -g @fission-ai/openspec"
    assert get_install_command(openspec, "linux") == "npm install -g @fission-ai/openspec"
    assert get_install_command(openspec, "windows") is None


def test_get_install_command_for_skill(sample_manifest):
    superpowers = sample_manifest["skills"]["superpowers"]
    assert "git clone" in get_install_command(superpowers, "macos")
    assert "--branch main" in get_install_command(superpowers, "macos")


@patch("scripts.lincoln_dependency_manager.subprocess.run")
def test_install_skill_clones_when_missing(mock_run, tmp_path):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)

    result = install_skill(
        "superpowers",
        "https://github.com/obra/superpowers.git",
        "main",
        skills_dir,
    )

    assert result["installed"] is True
    assert result["name"] == "superpowers"
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert args[0] == "git"
    assert "--branch" in args
    assert "main" in args


@patch("scripts.lincoln_dependency_manager.subprocess.run")
def test_install_skill_skips_when_already_at_ref(mock_run, tmp_path):
    skills_dir = tmp_path / "skills"
    skill_dir = skills_dir / "superpowers"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# skill", encoding="utf-8")

    # Simulate git describing the exact ref
    def fake_run(cmd, **kwargs):
        if "describe" in cmd:
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="v1.2.0\n")
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="")

    mock_run.side_effect = fake_run

    result = install_skill(
        "superpowers",
        "https://github.com/sushanglewis/claude-superpowers.git",
        "v1.2.0",
        skills_dir,
    )

    assert result["installed"] is False
    assert result["skipped"] is True


@patch("scripts.lincoln_dependency_manager.subprocess.run")
def test_install_skill_skips_when_branch_head_matches_remote(mock_run, tmp_path):
    skills_dir = tmp_path / "skills"
    skill_dir = skills_dir / "superpowers"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# skill", encoding="utf-8")

    def fake_run(cmd, **kwargs):
        if "describe" in cmd:
            return subprocess.CompletedProcess(args=cmd, returncode=1, stdout="", stderr="no tags")
        if "rev-parse" in cmd:
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="abc123\n")
        if "ls-remote" in cmd:
            return subprocess.CompletedProcess(
                args=cmd, returncode=0, stdout="abc123\trefs/heads/main\n"
            )
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="")

    mock_run.side_effect = fake_run

    result = install_skill(
        "superpowers",
        "https://github.com/obra/superpowers.git",
        "main",
        skills_dir,
    )

    assert result["installed"] is False
    assert result["skipped"] is True
    called_cmds = [c[0][0] for c in mock_run.call_args_list]
    assert not any("fetch" in cmd for cmd in called_cmds)


@patch("scripts.lincoln_dependency_manager.subprocess.run")
def test_install_skill_fetches_when_branch_head_differs(mock_run, tmp_path):
    skills_dir = tmp_path / "skills"
    skill_dir = skills_dir / "superpowers"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# skill", encoding="utf-8")

    def fake_run(cmd, **kwargs):
        if "describe" in cmd:
            return subprocess.CompletedProcess(args=cmd, returncode=1, stdout="", stderr="no tags")
        if "rev-parse" in cmd:
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="abc123\n")
        if "ls-remote" in cmd:
            return subprocess.CompletedProcess(
                args=cmd, returncode=0, stdout="def456\trefs/heads/main\n"
            )
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="")

    mock_run.side_effect = fake_run

    result = install_skill(
        "superpowers",
        "https://github.com/obra/superpowers.git",
        "main",
        skills_dir,
    )

    assert result["installed"] is True
    called_cmds = [c[0][0] for c in mock_run.call_args_list]
    assert any("fetch" in cmd for cmd in called_cmds)
    checkout_cmd = next(cmd for cmd in called_cmds if "checkout" in cmd)
    assert "FETCH_HEAD" in checkout_cmd


@patch("scripts.lincoln_dependency_manager.subprocess.run")
def test_install_skill_dry_run_when_branch_head_differs(mock_run, tmp_path):
    skills_dir = tmp_path / "skills"
    skill_dir = skills_dir / "superpowers"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# skill", encoding="utf-8")

    def fake_run(cmd, **kwargs):
        if "describe" in cmd:
            return subprocess.CompletedProcess(args=cmd, returncode=1, stdout="", stderr="no tags")
        if "rev-parse" in cmd:
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="abc123\n")
        if "ls-remote" in cmd:
            return subprocess.CompletedProcess(
                args=cmd, returncode=0, stdout="def456\trefs/heads/main\n"
            )
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="")

    mock_run.side_effect = fake_run

    result = install_skill(
        "superpowers",
        "https://github.com/obra/superpowers.git",
        "main",
        skills_dir,
        dry_run=True,
    )

    assert result["installed"] is False
    assert result["skipped"] is False
    assert result["error"]
    called_cmds = [c[0][0] for c in mock_run.call_args_list]
    assert not any("fetch" in cmd for cmd in called_cmds)


@patch("scripts.lincoln_dependency_manager.subprocess.run")
def test_install_skill_aborts_when_dirty(mock_run, tmp_path):
    skills_dir = tmp_path / "skills"
    skill_dir = skills_dir / "superpowers"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# skill", encoding="utf-8")

    def fake_run(cmd, **kwargs):
        if "status" in cmd:
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout=" M SKILL.md\n")
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="")

    mock_run.side_effect = fake_run

    result = install_skill(
        "superpowers",
        "https://github.com/sushanglewis/claude-superpowers.git",
        "v1.2.0",
        skills_dir,
    )

    assert result["installed"] is False
    assert "dirty" in result["error"].lower()


@patch("scripts.lincoln_dependency_manager.subprocess.run")
def test_install_cli_runs_command(mock_run):
    mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
    result = install_cli("openspec", "npm install -g @fission-ai/openspec", dry_run=False)
    assert result["installed"] is True
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert args == ["npm", "install", "-g", "@fission-ai/openspec"]


def test_install_cli_dry_run_does_not_execute():
    result = install_cli("openspec", "npm install -g @fission-ai/openspec", dry_run=True)
    assert result["installed"] is False
    assert result["dry_run"] is True


@patch("scripts.lincoln_dependency_manager.subprocess.run")
def test_install_cli_returns_failure_on_error(mock_run):
    mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=1, stderr="npm error")
    result = install_cli("openspec", "npm install -g @fission-ai/openspec")
    assert result["installed"] is False
    assert "npm error" in result["error"]


def test_init_openspec_config_writes_file(tmp_path):
    config_path = tmp_path / ".github" / "openspec-config.yml"
    config_path.parent.mkdir(parents=True)
    result = init_openspec_config("my-org", "my-repo", "main", config_path)

    assert result["updated"] is True
    text = config_path.read_text(encoding="utf-8")
    assert "my-org" in text
    assert "my-repo" in text
    assert "main" in text


def test_init_openspec_config_does_not_overwrite_real_values(tmp_path):
    config_path = tmp_path / ".github" / "openspec-config.yml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "repository:\n  owner: existing-org\n  name: existing-repo\n  default_branch: develop\n",
        encoding="utf-8",
    )
    result = init_openspec_config("my-org", "my-repo", "main", config_path)
    assert result["updated"] is False
    assert "existing-org" in config_path.read_text(encoding="utf-8")


def test_init_openspec_config_overwrites_placeholders(tmp_path):
    config_path = tmp_path / ".github" / "openspec-config.yml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "repository:\n  owner: your-org\n  name: your-repo\n  default_branch: main\n",
        encoding="utf-8",
    )
    result = init_openspec_config("my-org", "my-repo", "main", config_path)
    assert result["updated"] is True
    text = config_path.read_text(encoding="utf-8")
    assert "my-org" in text
    assert "your-org" not in text
