"""Extended tests for scripts/lincoln_harness_adapter.py.

Covers Phase 1 / P0 additions: copy transform with path metadata,
mcp-config transform, and claude-code source consistency checks.
"""

import json
from pathlib import Path

import pytest
import yaml

from scripts.lincoln_harness_adapter import (
    check_drift,
    generate,
)


def _write_manifest(root: Path, name: str, data: dict) -> Path:
    harness_dir = root / ".claude" / "harnesses"
    harness_dir.mkdir(parents=True, exist_ok=True)
    path = harness_dir / f"{name}.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def _command_map(root: Path) -> Path:
    harness_dir = root / ".claude" / "harnesses"
    harness_dir.mkdir(parents=True, exist_ok=True)
    path = harness_dir / "command-map.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "commands": {
                    "lc-status": {
                        "description": "Show current Lincoln stage status",
                        "action": "python3 scripts/lincoln-status.py",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    return path


def _plugin_json(root: Path) -> Path:
    plugin_dir = root / ".claude-plugin"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    path = plugin_dir / "plugin.json"
    path.write_text(
        json.dumps(
            {
                "name": "lincoln",
                "version": "1.2.0",
                "description": "Test plugin",
                "author": {"name": "Lincoln contributors"},
                "repository": "https://github.com/sushanglewis/Lincoln",
                "homepage": "https://github.com/sushanglewis/Lincoln",
                "license": "MIT",
                "keywords": ["test"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def _setup_repo(root: Path) -> None:
    """Create a minimal fake .claude/ source tree."""
    (root / ".claude" / "agents").mkdir(parents=True, exist_ok=True)
    (root / ".claude" / "agents" / "default.md").write_text(
        "---\nname: default\n---\n\nDefault agent contract.\n", encoding="utf-8"
    )
    (root / ".claude" / "skills" / "lc-explore-opensource").mkdir(parents=True, exist_ok=True)
    (root / ".claude" / "skills" / "lc-explore-opensource" / "SKILL.md").write_text(
        "---\nname: lc-explore-opensource\n---\n\nExplore open source.\n", encoding="utf-8"
    )
    (root / ".claude" / "rules" / "ecc" / "common").mkdir(parents=True, exist_ok=True)
    (root / ".claude" / "rules" / "ecc" / "common" / "coding-style.md").write_text(
        "# Coding style\n\nKeep it simple.\n", encoding="utf-8"
    )
    (root / ".claude" / "hooks").mkdir(parents=True, exist_ok=True)
    (root / ".claude" / "hooks" / "pre-tool-use.sh").write_text(
        "#!/bin/bash\necho pre-tool-use\n", encoding="utf-8"
    )
    (root / ".claude" / "hooks" / "pre-tool-use.sh").chmod(0o755)
    (root / ".claude" / "hooks" / "on-session-start.sh").write_text(
        "#!/bin/bash\necho on-session-start\n", encoding="utf-8"
    )
    (root / ".claude" / "hooks" / "on-session-start.sh").chmod(0o755)
    (root / ".claude" / "hooks" / "hooks.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0.0",
                "hooks": [
                    {"name": "pre-tool-use", "file": "pre-tool-use.sh", "events": ["pre_tool_use"], "harnesses": ["claude-code"], "order": 10},
                    {"name": "on-session-start", "file": "on-session-start.sh", "events": ["session_start"], "harnesses": ["claude-code"], "order": 10},
                ],
            }
        ),
        encoding="utf-8",
    )
    (root / ".claude" / "mcp").mkdir(parents=True, exist_ok=True)
    (root / ".claude" / "mcp" / "mcp.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0.0",
                "servers": {
                    "pencil": {
                        "command": "npx",
                        "args": ["-y", "@pencil/mcp-server"],
                        "env": {"PENCIL_API_KEY": "${PENCIL_API_KEY}"},
                        "enabled": True,
                        "harness_overrides": {
                            "codex": {"enabled": False},
                            "opencode": {"enabled": False},
                        },
                    },
                    "github": {
                        "command": "npx",
                        "args": ["-y", "@modelcontextprotocol/server-github"],
                        "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"},
                        "enabled": True,
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    (root / ".claude" / "policies").mkdir(parents=True, exist_ok=True)
    (root / ".claude" / "policies" / "security.yaml").write_text(
        yaml.safe_dump({"schema_version": "1.0.0", "policies": []}),
        encoding="utf-8",
    )
    _command_map(root)
    _plugin_json(root)
    _write_manifest(
        root,
        "claude-code",
        {
            "name": "claude-code",
            "capabilities": {"hooks": True, "skills": True, "agents": True, "commands": True},
            "command_map_source": "command-map.yaml",
            "targets": [],
        },
    )


def _codex_manifest():
    return {
        "name": "codex",
        "capabilities": {"hooks": True, "skills": True, "agents": True, "commands": True},
        "command_map_source": "command-map.yaml",
        "targets": [
            {
                "kind": "agents-md",
                "source": ".claude/agents/*.md",
                "output": "{project}/AGENTS.md",
                "scope": "project",
                "transform": "concat",
            },
            {
                "kind": "skill",
                "source": ".claude/skills/*/SKILL.md",
                "output": "{home}/.codex/skills/{parent}/{name}.md",
                "scope": "home",
                "transform": "copy",
            },
            {
                "kind": "rule",
                "source": ".claude/rules/**/*.md",
                "output": "{project}/.codex/rules/{relative_path}.md",
                "scope": "project",
                "transform": "copy",
            },
            {
                "kind": "hook",
                "source": ".claude/hooks/*.sh",
                "output": "{project}/.codex/hooks/{name}.sh",
                "scope": "project",
                "transform": "copy",
            },
            {
                "kind": "mcp",
                "source": ".claude/mcp/mcp.yaml",
                "output": "{project}/.codex/mcp.json",
                "scope": "project",
                "transform": "mcp-config",
            },
            {
                "kind": "plugin",
                "source": ".claude-plugin/plugin.json",
                "output": "{project}/.codex-plugin/{name}.json",
                "scope": "project",
                "transform": "plugin-json",
            },
        ],
    }


def _opencode_manifest():
    return {
        "name": "opencode",
        "capabilities": {"hooks": True, "skills": True, "agents": True, "commands": True},
        "command_map_source": "command-map.yaml",
        "targets": [
            {
                "kind": "agent",
                "source": ".claude/agents/*.md",
                "output": "{project}/.opencode/agent/{name}.md",
                "scope": "project",
                "transform": "frontmatter",
                "fields": ["description", "mode", "model", "permission", "tools"],
            },
            {
                "kind": "skill",
                "source": ".claude/skills/*/SKILL.md",
                "output": "{project}/.opencode/skills/{parent}/{name}.md",
                "scope": "project",
                "transform": "copy",
            },
            {
                "kind": "rule",
                "source": ".claude/rules/**/*.md",
                "output": "{project}/.opencode/rules/{relative_path}.md",
                "scope": "project",
                "transform": "copy",
            },
            {
                "kind": "hook",
                "source": ".claude/hooks/*.sh",
                "output": "{project}/.opencode/hooks/{name}.sh",
                "scope": "project",
                "transform": "copy",
            },
            {
                "kind": "mcp",
                "source": ".claude/mcp/mcp.yaml",
                "output": "{project}/.opencode/mcp.json",
                "scope": "project",
                "transform": "mcp-config",
            },
        ],
    }


@pytest.fixture
def fake_repo(tmp_path):
    root = tmp_path / "repo"
    _setup_repo(root)
    return root


def test_copy_transform_uses_parent_placeholder(fake_repo, tmp_path):
    _write_manifest(fake_repo, "codex", _codex_manifest())
    project = tmp_path / "project"
    home = tmp_path / "home"
    project.mkdir()
    home.mkdir()
    written = generate(fake_repo, "codex", project_dir=project, home_dir=home)
    skill_file = home / ".codex" / "skills" / "lc-explore-opensource" / "SKILL.md"
    assert skill_file in written
    assert skill_file.exists()
    assert "自动生成" in skill_file.read_text(encoding="utf-8")


def test_copy_transform_uses_relative_path_placeholder(fake_repo, tmp_path):
    _write_manifest(fake_repo, "codex", _codex_manifest())
    project = tmp_path / "project"
    home = tmp_path / "home"
    project.mkdir()
    home.mkdir()
    generate(fake_repo, "codex", project_dir=project, home_dir=home)
    rule_file = project / ".codex" / "rules" / "ecc" / "common" / "coding-style.md"
    assert rule_file.exists()
    assert "Coding style" in rule_file.read_text(encoding="utf-8")


def test_copy_transform_generates_hooks(fake_repo, tmp_path):
    _write_manifest(fake_repo, "codex", _codex_manifest())
    project = tmp_path / "project"
    home = tmp_path / "home"
    project.mkdir()
    home.mkdir()
    generate(fake_repo, "codex", project_dir=project, home_dir=home)
    hook_file = project / ".codex" / "hooks" / "pre-tool-use.sh"
    assert hook_file.exists()
    assert "pre-tool-use" in hook_file.read_text(encoding="utf-8")


def test_mcp_config_transform_applies_harness_overrides(fake_repo, tmp_path):
    _write_manifest(fake_repo, "codex", _codex_manifest())
    project = tmp_path / "project"
    home = tmp_path / "home"
    project.mkdir()
    home.mkdir()
    generate(fake_repo, "codex", project_dir=project, home_dir=home)
    mcp_file = project / ".codex" / "mcp.json"
    assert mcp_file.exists()
    config = json.loads(mcp_file.read_text(encoding="utf-8"))
    assert "mcpServers" in config
    # pencil is disabled for codex by harness_override.
    assert "pencil" not in config["mcpServers"]
    assert "github" in config["mcpServers"]
    # Placeholders must be preserved, not resolved.
    assert config["mcpServers"]["github"]["env"]["GITHUB_PERSONAL_ACCESS_TOKEN"] == "${GITHUB_PERSONAL_ACCESS_TOKEN}"


def test_mcp_config_transform_keeps_enabled_servers(fake_repo, tmp_path):
    _write_manifest(fake_repo, "opencode", _opencode_manifest())
    project = tmp_path / "project"
    home = tmp_path / "home"
    project.mkdir()
    home.mkdir()
    generate(fake_repo, "opencode", project_dir=project, home_dir=home)
    mcp_file = project / ".opencode" / "mcp.json"
    config = json.loads(mcp_file.read_text(encoding="utf-8"))
    # opencode also disables pencil in the fixture overrides.
    assert "pencil" not in config["mcpServers"]
    assert "github" in config["mcpServers"]


def test_claude_code_check_passes_for_valid_sources(fake_repo, tmp_path):
    project = tmp_path / "project"
    home = tmp_path / "home"
    diffs = check_drift(fake_repo, "claude-code", project_dir=project, home_dir=home)
    assert diffs == []


def test_claude_code_check_reports_missing_hook_file(fake_repo, tmp_path):
    (fake_repo / ".claude" / "hooks" / "pre-tool-use.sh").unlink()
    project = tmp_path / "project"
    home = tmp_path / "home"
    diffs = check_drift(fake_repo, "claude-code", project_dir=project, home_dir=home)
    assert any("missing hook" in d for d in diffs)


def test_claude_code_check_reports_missing_mcp_config(fake_repo, tmp_path):
    (fake_repo / ".claude" / "mcp" / "mcp.yaml").unlink()
    project = tmp_path / "project"
    home = tmp_path / "home"
    diffs = check_drift(fake_repo, "claude-code", project_dir=project, home_dir=home)
    assert any("mcp.yaml" in d for d in diffs)


def test_claude_code_check_reports_missing_risk_policy(fake_repo, tmp_path):
    (fake_repo / ".claude" / "policies" / "security.yaml").unlink()
    project = tmp_path / "project"
    home = tmp_path / "home"
    diffs = check_drift(fake_repo, "claude-code", project_dir=project, home_dir=home)
    assert any("security.yaml" in d for d in diffs)


def test_claude_code_generate_is_no_op(fake_repo, tmp_path):
    project = tmp_path / "project"
    home = tmp_path / "home"
    project.mkdir()
    home.mkdir()
    written = generate(fake_repo, "claude-code", project_dir=project, home_dir=home)
    assert written == []
