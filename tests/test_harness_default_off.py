"""Default-off acceptance tests for generated harness artifacts (#64).

Lesson from superpowers (obra/superpowers@7d8d3d4): anything NOT explicitly
declared may be auto-activated by the harness's defaults. Lincoln's harness
manifests declare `capabilities` (hooks/skills/agents/commands); these tests
generate codex/opencode artifacts from the REAL repo and assert that every
capability declared `false` leaves no trace in the output.
"""

import json
from pathlib import Path

import yaml
from scripts import lincoln_harness_adapter

ROOT = Path(__file__).resolve().parents[1]
HARNESSES = ("codex", "opencode")

# Strings that would indicate a hook/capability registration leaking into
# generated artifacts (prose mentions of .claude/hooks are fine).
FORBIDDEN_CONTENT = ("SessionStart", "hooks.json")


def _generate(harness: str, tmp_path: Path) -> list[Path]:
    project_dir = tmp_path / harness / "project"
    home_dir = tmp_path / harness / "home"
    project_dir.mkdir(parents=True)
    home_dir.mkdir(parents=True)
    return lincoln_harness_adapter.generate(ROOT, harness, project_dir, home_dir)


def _manifest(harness: str) -> dict:
    path = ROOT / ".claude" / "harnesses" / f"{harness}.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _is_codex_plugin_manifest(out_path: Path) -> bool:
    return ".codex-plugin" in out_path.parts and out_path.name == "plugin.json"


def test_disabled_hooks_leave_no_trace(tmp_path):
    for harness in HARNESSES:
        manifest = _manifest(harness)
        assert manifest["capabilities"]["hooks"] is False, (
            f"{harness}: this test assumes hooks capability is disabled"
        )
        for out_path in _generate(harness, tmp_path):
            assert "hooks" not in out_path.name.lower(), f"hook artifact leaked: {out_path}"
            # The codex plugin manifest intentionally contains the explicit
            # `"hooks": {}` declaration; everything else must stay clean.
            if _is_codex_plugin_manifest(out_path):
                continue
            content = out_path.read_text(encoding="utf-8")
            for needle in FORBIDDEN_CONTENT:
                assert needle not in content, f"{needle!r} leaked into {out_path}"


def test_disabled_skills_leave_no_trace(tmp_path):
    for harness in HARNESSES:
        manifest = _manifest(harness)
        assert manifest["capabilities"]["skills"] is False, (
            f"{harness}: this test assumes skills capability is disabled"
        )
        for out_path in _generate(harness, tmp_path):
            parts = [p.lower() for p in out_path.parts]
            assert "skills" not in parts, f"skill dir leaked: {out_path}"
            # codex emits .codex-plugin/plugin.json; opencode must not create
            # any plugin directory because skills are disabled.
            if harness == "codex" and ".codex-plugin" in parts:
                continue
            assert "plugin" not in parts, f"plugin dir leaked: {out_path}"


def test_only_lc_commands_are_generated(tmp_path):
    for harness in HARNESSES:
        for out_path in _generate(harness, tmp_path):
            in_command_dir = "prompts" in out_path.parts or "command" in out_path.parts
            if in_command_dir and out_path.suffix == ".md":
                assert out_path.name.startswith("lc-"), (
                    f"non-lc command leaked into {harness} artifacts: {out_path}"
                )


def test_codex_plugin_manifest_explicitly_disables_hooks(tmp_path):
    """Codex plugin.json must contain an explicit `hooks: {}` declaration."""
    project_dir = tmp_path / "codex" / "project"
    home_dir = tmp_path / "codex" / "home"
    project_dir.mkdir(parents=True)
    home_dir.mkdir(parents=True)
    lincoln_harness_adapter.generate(ROOT, "codex", project_dir, home_dir)

    plugin_path = project_dir / ".codex-plugin" / "plugin.json"
    assert plugin_path.exists(), "codex plugin manifest was not generated"
    manifest = json.loads(plugin_path.read_text(encoding="utf-8"))
    assert "hooks" in manifest, "codex plugin manifest must explicitly declare hooks"
    assert manifest["hooks"] == {}, "hooks must be explicitly disabled with an empty object"


def test_codex_plugin_manifest_drops_claude_only_capabilities(tmp_path):
    """Claude-Code-only blocks must not be carried into the codex plugin manifest."""
    project_dir = tmp_path / "codex" / "project"
    home_dir = tmp_path / "codex" / "home"
    project_dir.mkdir(parents=True)
    home_dir.mkdir(parents=True)
    lincoln_harness_adapter.generate(ROOT, "codex", project_dir, home_dir)

    plugin_path = project_dir / ".codex-plugin" / "plugin.json"
    manifest = json.loads(plugin_path.read_text(encoding="utf-8"))
    assert "skills" not in manifest, "skills block must be absent from codex plugin manifest"
    assert "agents" not in manifest, "agents block must be absent from codex plugin manifest"
    # Neutral metadata should be preserved.
    assert manifest.get("name") == "lincoln"
    assert manifest.get("version") == "1.3.0"
