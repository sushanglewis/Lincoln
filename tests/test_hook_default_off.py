"""Tests that globally-installed Lincoln hooks default to inactive."""

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_global_hook_exits_when_no_marker(tmp_path):
    # Simulate a globally-installed Lincoln plugin (via CLAUDE_PLUGIN_ROOT)
    # pointing at a project that has not opted in via .lincoln.yaml.
    global_plugin_root = tmp_path / "global-lincoln"
    global_plugin_root.mkdir(parents=True)

    # Provide a Python interpreter with pyyaml available under the global root.
    venv_bin = global_plugin_root / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    (venv_bin / "python3").symlink_to(Path(sys.executable).resolve())

    project_root = tmp_path / "project"
    project_root.mkdir(parents=True)

    env = {
        "HOME": str(tmp_path / "home"),
        "CLAUDE_PLUGIN_ROOT": str(global_plugin_root),
    }
    result = subprocess.run(
        ["bash", str(ROOT / ".claude" / "hooks" / "on-session-start.sh")],
        cwd=str(project_root),
        env=env,
        capture_output=True,
    )
    assert result.returncode == 0
    assert b"Lincoln inactive" in result.stdout
