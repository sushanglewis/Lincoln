from pathlib import Path

import yaml

from scripts.lincoln_paths import discover_process_state_paths, resolve_state_path


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
