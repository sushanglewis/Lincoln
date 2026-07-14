from pathlib import Path

import yaml

from scripts.lincoln_paths import (
    discover_process_state_paths,
    discover_solo_state_paths,
    resolve_state_path,
)


def test_resolve_state_path_prefers_process_package(tmp_path):
    package = tmp_path / "checkout-redesign"
    package.mkdir()
    state = package / "workflow-stage.yaml"
    state.write_text(yaml.dump({"schema_version": "2.0.0"}), encoding="utf-8")
    (tmp_path / ".claude").mkdir()
    legacy = tmp_path / ".claude" / "workflow-stage.yaml"
    legacy.write_text(yaml.dump({"schema_version": "legacy"}), encoding="utf-8")

    assert discover_process_state_paths(tmp_path) == [state]
    assert resolve_state_path(None, tmp_path) == state


def test_resolve_state_path_prefers_team_over_solo(tmp_path):
    package = tmp_path / "issue-1"
    package.mkdir()
    team_state = package / "workflow-stage.yaml"
    team_state.write_text(yaml.dump({"schema_version": "2.0.0"}), encoding="utf-8")
    solo_dir = tmp_path / ".context" / "workflow"
    solo_dir.mkdir(parents=True)
    solo_state = solo_dir / "bug-fix.yaml"
    solo_state.write_text(yaml.dump({"schema_version": "2.0.0"}), encoding="utf-8")

    assert discover_solo_state_paths(tmp_path) == [solo_state]
    assert resolve_state_path(None, tmp_path) == team_state


def test_resolve_state_path_falls_back_to_solo(tmp_path):
    solo_dir = tmp_path / ".context" / "workflow"
    solo_dir.mkdir(parents=True)
    solo_state = solo_dir / "bug-fix.yaml"
    solo_state.write_text(yaml.dump({"schema_version": "2.0.0"}), encoding="utf-8")

    assert resolve_state_path(None, tmp_path) == solo_state


def test_resolve_state_path_without_solo_dir(tmp_path):
    assert discover_solo_state_paths(tmp_path) == []
