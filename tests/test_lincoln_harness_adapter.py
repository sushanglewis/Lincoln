"""Tests for scripts/lincoln_harness_adapter.py."""

import json
from pathlib import Path

import pytest
import yaml

from scripts.lincoln_harness_adapter import (
    HarnessAdapterError,
    check_drift,
    generate,
    load_manifest,
    validate_manifest,
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
                "skills": ["./.claude/skills/test/"],
                "agents": ["./.claude/agents/"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


@pytest.fixture
def fake_repo(tmp_path):
    root = tmp_path / "repo"
    (root / ".claude" / "agents").mkdir(parents=True)
    (root / ".claude" / "agents" / "default.md").write_text(
        "---\nname: default\n---\n\nDefault agent contract.\n", encoding="utf-8"
    )
    _command_map(root)
    _plugin_json(root)
    return root


def _basic_manifest():
    return {
        "name": "opencode",
        "capabilities": {"hooks": False, "skills": False, "agents": True, "commands": True},
        "targets": [
            {
                "kind": "agent",
                "source": ".claude/agents/*.md",
                "output": "{project}/.opencode/agent/{name}.md",
                "scope": "project",
                "transform": "frontmatter",
            }
        ],
        "command_map": {
            "lc-status": {
                "description": "Show current Lincoln stage status",
                "action": "python3 scripts/lincoln-status.py",
            }
        },
    }


def test_load_manifest_reads_yaml(fake_repo):
    _write_manifest(fake_repo, "opencode", _basic_manifest())
    manifest = load_manifest(fake_repo, "opencode")
    assert manifest["name"] == "opencode"
    assert manifest["command_map"]["lc-status"]["action"] == "python3 scripts/lincoln-status.py"


def test_load_manifest_raises_for_missing(fake_repo):
    with pytest.raises(HarnessAdapterError):
        load_manifest(fake_repo, "nonexistent")


def test_validate_manifest_rejects_non_lc_command(fake_repo):
    manifest = _basic_manifest()
    manifest["command_map"]["status"] = manifest["command_map"].pop("lc-status")
    errors = validate_manifest(manifest)
    assert any("lc-" in e for e in errors)


def test_validate_manifest_rejects_missing_fields():
    errors = validate_manifest({"name": "opencode"})
    assert errors


def test_generate_produces_artifacts_with_header(fake_repo, tmp_path):
    _write_manifest(fake_repo, "opencode", _basic_manifest())
    project = tmp_path / "project"
    project.mkdir()
    written = generate(fake_repo, "opencode", project_dir=project, home_dir=tmp_path / "home")
    assert written
    agent_file = project / ".opencode" / "agent" / "default.md"
    assert agent_file.exists()
    text = agent_file.read_text(encoding="utf-8")
    assert "自动生成" in text
    assert ".claude/agents/default.md" in text


def test_generate_is_idempotent(fake_repo, tmp_path):
    _write_manifest(fake_repo, "opencode", _basic_manifest())
    project = tmp_path / "project"
    project.mkdir()
    generate(fake_repo, "opencode", project_dir=project, home_dir=tmp_path / "home")
    first = (project / ".opencode" / "agent" / "default.md").read_text(encoding="utf-8")
    generate(fake_repo, "opencode", project_dir=project, home_dir=tmp_path / "home")
    second = (project / ".opencode" / "agent" / "default.md").read_text(encoding="utf-8")
    assert first == second


def test_check_drift_passes_when_clean(fake_repo, tmp_path):
    _write_manifest(fake_repo, "opencode", _basic_manifest())
    project = tmp_path / "project"
    project.mkdir()
    home = tmp_path / "home"
    generate(fake_repo, "opencode", project_dir=project, home_dir=home)
    assert check_drift(fake_repo, "opencode", project_dir=project, home_dir=home) == []


def test_check_drift_detects_modified_artifact(fake_repo, tmp_path):
    _write_manifest(fake_repo, "opencode", _basic_manifest())
    project = tmp_path / "project"
    project.mkdir()
    home = tmp_path / "home"
    generate(fake_repo, "opencode", project_dir=project, home_dir=home)
    target = project / ".opencode" / "agent" / "default.md"
    target.write_text("tampered", encoding="utf-8")
    diffs = check_drift(fake_repo, "opencode", project_dir=project, home_dir=home)
    assert diffs
    assert any("default.md" in d for d in diffs)


def test_command_map_source_resolves_shared_file(fake_repo):
    """Manifests may reference the shared command-map.yaml instead of embedding."""
    manifest = _basic_manifest()
    del manifest["command_map"]
    manifest["command_map_source"] = "command-map.yaml"
    _write_manifest(fake_repo, "opencode", manifest)
    loaded = load_manifest(fake_repo, "opencode")
    assert loaded["command_map"]["lc-status"]["action"] == "python3 scripts/lincoln-status.py"


def test_frontmatter_fields_override_from_manifest(fake_repo, tmp_path):
    """Target-level `fields` overrides the default frontmatter whitelist."""
    manifest = _basic_manifest()
    manifest["targets"][0]["fields"] = ["description"]
    _write_manifest(fake_repo, "opencode", manifest)
    project = tmp_path / "project"
    project.mkdir()
    generate(fake_repo, "opencode", project_dir=project, home_dir=tmp_path / "home")
    text = (project / ".opencode" / "agent" / "default.md").read_text(encoding="utf-8")
    front = text.split("---")[1]
    assert "name:" not in front


def test_concat_appends_command_listing(fake_repo, tmp_path):
    """concat transform (AGENTS.md) must include the lc-* command listing."""
    manifest = _basic_manifest()
    manifest["targets"] = [
        {
            "kind": "agents-md",
            "source": ".claude/agents/*.md",
            "output": "{project}/AGENTS.md",
            "scope": "project",
            "transform": "concat",
        }
    ]
    _write_manifest(fake_repo, "codex", manifest)
    project = tmp_path / "project"
    project.mkdir()
    generate(fake_repo, "codex", project_dir=project, home_dir=tmp_path / "home")
    text = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "lc-status" in text
    assert "python3 scripts/lincoln-status.py" in text
    assert "stage_loader.py" in text
    assert "Default agent contract." in text


def test_real_command_map_registers_lc_wf_commands():
    """The shared command-map.yaml must register one lc-wf-* command per workflow."""
    root = Path(__file__).resolve().parents[1]
    command_map = yaml.safe_load(
        (root / ".claude" / "harnesses" / "command-map.yaml").read_text(encoding="utf-8")
    )
    commands = command_map["commands"]
    workflow_names = sorted(p.stem for p in (root / ".claude" / "workflows").glob("*.yaml"))
    for name in workflow_names:
        key = f"lc-wf-{name}"
        assert key in commands, f"missing command-map entry: {key}"
        assert commands[key]["action"] == "python3 scripts/lincoln_workflow.py"
    assert "lc-wf-list" in commands
    assert all(k.startswith("lc-") for k in commands)


def test_generated_gate_clause_included(fake_repo, tmp_path):
    """Lightweight gate: generated command templates must mention stage_loader validation."""
    manifest = _basic_manifest()
    manifest["targets"].append(
        {
            "kind": "command",
            "source": "command_map",
            "output": "{project}/.opencode/command/{name}.md",
            "scope": "project",
            "transform": "command-template",
        }
    )
    _write_manifest(fake_repo, "opencode", manifest)
    project = tmp_path / "project"
    project.mkdir()
    generate(fake_repo, "opencode", project_dir=project, home_dir=tmp_path / "home")
    cmd = project / ".opencode" / "command" / "lc-status.md"
    assert cmd.exists()
    text = cmd.read_text(encoding="utf-8")
    assert "stage_loader.py" in text
    assert "python3 scripts/lincoln-status.py" in text


def _codex_manifest():
    return {
        "name": "codex",
        "capabilities": {"hooks": False, "skills": False, "agents": True, "commands": True},
        "targets": [
            {
                "kind": "agents-md",
                "source": ".claude/agents/*.md",
                "output": "{project}/AGENTS.md",
                "scope": "project",
                "transform": "concat",
            },
            {
                "kind": "plugin",
                "source": ".claude-plugin/plugin.json",
                "output": "{project}/.codex-plugin/{name}.json",
                "scope": "project",
                "transform": "plugin-json",
            },
        ],
        "command_map": {
            "lc-status": {
                "description": "Show current Lincoln stage status",
                "action": "python3 scripts/lincoln-status.py",
            }
        },
    }


def test_validate_manifest_rejects_missing_capability_keys():
    manifest = {
        "name": "codex",
        "capabilities": {"hooks": False},
        "targets": [],
        "command_map": {"lc-status": {"description": "x", "action": "y"}},
    }
    errors = validate_manifest(manifest)
    assert any("capabilities.skills" in e for e in errors)
    assert any("capabilities.agents" in e for e in errors)
    assert any("capabilities.commands" in e for e in errors)


def test_generate_produces_codex_plugin_manifest(fake_repo, tmp_path):
    _write_manifest(fake_repo, "codex", _codex_manifest())
    project = tmp_path / "project"
    project.mkdir()
    generate(fake_repo, "codex", project_dir=project, home_dir=tmp_path / "home")

    plugin_path = project / ".codex-plugin" / "plugin.json"
    assert plugin_path.exists()
    manifest = json.loads(plugin_path.read_text(encoding="utf-8"))
    assert manifest.get("hooks") == {}
    assert "skills" not in manifest
    assert "agents" not in manifest
    assert manifest.get("name") == "lincoln"


def test_codex_plugin_manifest_is_idempotent(fake_repo, tmp_path):
    _write_manifest(fake_repo, "codex", _codex_manifest())
    project = tmp_path / "project"
    project.mkdir()
    generate(fake_repo, "codex", project_dir=project, home_dir=tmp_path / "home")
    first = (project / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    generate(fake_repo, "codex", project_dir=project, home_dir=tmp_path / "home")
    second = (project / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    assert first == second
