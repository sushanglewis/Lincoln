"""Validate the Claude Code Marketplace hooks manifest."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_plugin_hooks_json_matches_files():
    plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert plugin["hooks"] == ".claude-plugin/hooks.json"
    hooks = json.loads((ROOT / ".claude-plugin" / "hooks.json").read_text(encoding="utf-8"))
    for event, script in hooks.items():
        assert (ROOT / script).exists(), f"{event} -> {script} does not exist"
