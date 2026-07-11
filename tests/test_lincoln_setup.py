"""Tests for scripts/lincoln-setup.py."""

import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SETUP_SCRIPT = ROOT / "scripts" / "lincoln-setup.py"


def _load_setup_module():
    """Load lincoln-setup.py as a module (filename has hyphen)."""
    spec = importlib.util.spec_from_file_location("lincoln_setup", SETUP_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def setup_mod():
    return _load_setup_module()


@pytest.fixture
def tmp_project(tmp_path):
    """Create a minimal temporary Lincoln-like project."""
    root = tmp_path / "lincoln"
    root.mkdir()
    deps = {
        "schema_version": "1.0.0",
        "skills": {
            "superpowers": {
                "source": "https://github.com/sushanglewis/claude-superpowers.git",
                "ref": "v1.2.0",
                "type": "skill",
                "required": True,
            },
            "openspec": {
                "source": "https://github.com/Fission-AI/openspec.git",
                "ref": "v0.5.0",
                "type": "cli",
                "binary": "openspec",
                "required": True,
                "platforms": {"macos": "npm install -g @fission-ai/openspec"},
            },
        },
    }
    (root / ".claude" / "skills").mkdir(parents=True)
    (root / ".claude" / "skills" / "dependencies.yaml").write_text(
        yaml.safe_dump(deps), encoding="utf-8"
    )
    return root


def test_cli_check_subcommand_prints_status(setup_mod, tmp_project, capsys):
    dep_mod = setup_mod.lincoln_dependency_manager
    with patch.object(
        dep_mod,
        "check_skills",
        return_value=[
            {
                "name": "superpowers",
                "type": "skill",
                "required": True,
                "default_install": True,
                "source": "https://github.com/sushanglewis/claude-superpowers.git",
                "ref": "v1.2.0",
                "install_command": "git clone ...",
            }
        ],
    ), patch.object(dep_mod, "check_clis", return_value=[]), patch.object(
        dep_mod, "detect_platform", return_value="macos"
    ):
        exit_code = setup_mod.main(["check", "--root", str(tmp_project)])
        captured = capsys.readouterr()

    assert exit_code == 1  # missing required dependency
    assert "superpowers" in captured.out
    assert "openspec" not in captured.out


def test_cli_check_subcommand_passes_when_all_present(setup_mod, tmp_project, capsys):
    dep_mod = setup_mod.lincoln_dependency_manager
    with patch.object(dep_mod, "check_skills", return_value=[]), patch.object(
        dep_mod, "check_clis", return_value=[]
    ), patch.object(dep_mod, "detect_platform", return_value="macos"):
        exit_code = setup_mod.main(["check", "--root", str(tmp_project)])
        captured = capsys.readouterr()

    assert exit_code == 0
    assert "All declared dependencies are present" in captured.out


def test_cli_install_skills_dry_run(setup_mod, tmp_project):
    dep_mod = setup_mod.lincoln_dependency_manager
    with patch.object(
        dep_mod,
        "check_skills",
        return_value=[
            {
                "name": "superpowers",
                "type": "skill",
                "required": True,
                "default_install": True,
                "source": "https://github.com/sushanglewis/claude-superpowers.git",
                "ref": "v1.2.0",
                "install_command": "git clone ...",
            }
        ],
    ), patch.object(
        dep_mod,
        "install_skill",
        return_value={"name": "superpowers", "installed": False, "dry_run": True, "error": ""},
    ) as mock_install:
        exit_code = setup_mod.main(
            ["install-skills", "--root", str(tmp_project), "--dry-run"]
        )

    assert exit_code == 0
    mock_install.assert_called_once()
    args = mock_install.call_args.kwargs
    assert args["dry_run"] is True


def test_cli_install_skills_asks_for_confirmation_by_default(setup_mod, tmp_project):
    dep_mod = setup_mod.lincoln_dependency_manager
    with patch.object(
        dep_mod,
        "check_skills",
        return_value=[
            {
                "name": "superpowers",
                "type": "skill",
                "required": True,
                "default_install": True,
                "source": "https://github.com/sushanglewis/claude-superpowers.git",
                "ref": "v1.2.0",
                "install_command": "git clone ...",
            }
        ],
    ), patch.object(
        dep_mod,
        "install_skill",
        return_value={"name": "superpowers", "installed": True, "error": ""},
    ) as mock_install, patch.object(
        setup_mod, "confirm", return_value=False
    ):
        exit_code = setup_mod.main(["install-skills", "--root", str(tmp_project)])

    assert exit_code == 1  # required skill skipped due to user decline
    mock_install.assert_not_called()


def test_cli_install_skills_with_yes_flag(setup_mod, tmp_project):
    dep_mod = setup_mod.lincoln_dependency_manager
    with patch.object(
        dep_mod,
        "check_skills",
        return_value=[
            {
                "name": "superpowers",
                "type": "skill",
                "required": True,
                "default_install": True,
                "source": "https://github.com/sushanglewis/claude-superpowers.git",
                "ref": "v1.2.0",
                "install_command": "git clone ...",
            }
        ],
    ), patch.object(
        dep_mod,
        "install_skill",
        return_value={"name": "superpowers", "installed": True, "error": ""},
    ) as mock_install:
        exit_code = setup_mod.main(
            ["install-skills", "--root", str(tmp_project), "--yes"]
        )

    assert exit_code == 0
    mock_install.assert_called_once()


def test_cli_install_clis_with_yes_flag(setup_mod, tmp_project):
    dep_mod = setup_mod.lincoln_dependency_manager
    with patch.object(
        dep_mod,
        "check_clis",
        return_value=[
            {
                "name": "openspec",
                "type": "cli",
                "binary": "openspec",
                "required": True,
                "install_command": "npm install -g @fission-ai/openspec",
            }
        ],
    ), patch.object(
        dep_mod,
        "install_cli",
        return_value={"name": "openspec", "installed": True, "error": ""},
    ) as mock_install:
        exit_code = setup_mod.main(
            ["install-clis", "--root", str(tmp_project), "--yes"]
        )

    assert exit_code == 0
    mock_install.assert_called_once()
    args = mock_install.call_args.args
    assert args[0] == "openspec"
    assert args[1] == "npm install -g @fission-ai/openspec"


def test_cli_init_repo_config_writes_placeholders(setup_mod, tmp_project):
    config_path = tmp_project / ".github" / "openspec-config.yml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "repository:\n  owner: your-org\n  name: your-repo\n  default_branch: main\n",
        encoding="utf-8",
    )

    dep_mod = setup_mod.lincoln_dependency_manager
    with patch.object(
        dep_mod,
        "init_openspec_config",
        return_value={"updated": True, "skipped": False, "error": ""},
    ) as mock_init:
        exit_code = setup_mod.main(
            [
                "init-repo-config",
                "--root",
                str(tmp_project),
                "--owner",
                "my-org",
                "--name",
                "my-repo",
            ]
        )

    assert exit_code == 0
    mock_init.assert_called_once()
    args = mock_init.call_args.args
    assert args[0] == "my-org"
    assert args[1] == "my-repo"


def test_cli_bootstrap_runs_all_steps(setup_mod, tmp_project):
    dep_mod = setup_mod.lincoln_dependency_manager
    with patch.object(
        dep_mod,
        "check_skills",
        return_value=[
            {
                "name": "superpowers",
                "type": "skill",
                "required": True,
                "default_install": True,
                "source": "https://github.com/sushanglewis/claude-superpowers.git",
                "ref": "v1.2.0",
                "install_command": "git clone ...",
            }
        ],
    ), patch.object(
        dep_mod,
        "check_clis",
        return_value=[
            {
                "name": "openspec",
                "type": "cli",
                "binary": "openspec",
                "required": True,
                "install_command": "npm install -g @fission-ai/openspec",
            }
        ],
    ), patch.object(
        dep_mod,
        "install_skill",
        return_value={"name": "superpowers", "installed": True, "error": ""},
    ) as mock_install_skill, patch.object(
        dep_mod,
        "install_cli",
        return_value={"name": "openspec", "installed": True, "error": ""},
    ) as mock_install_cli, patch.object(
        dep_mod,
        "init_openspec_config",
        return_value={"updated": True, "skipped": False, "error": ""},
    ) as mock_init_config, patch.object(
        setup_mod, "confirm", return_value=True
    ), patch.object(setup_mod, "run_init_project", return_value=0) as mock_init_project:
        exit_code = setup_mod.main(
            [
                "bootstrap",
                "--root",
                str(tmp_project),
                "--owner",
                "my-org",
                "--name",
                "my-repo",
            ]
        )

    assert exit_code == 0
    mock_install_skill.assert_called()
    mock_install_cli.assert_called()
    mock_init_config.assert_called()
    mock_init_project.assert_called_once()


def test_cli_mark_step_writes_state(setup_mod, tmp_project):
    exit_code = setup_mod.main(
        ["mark-step", "--root", str(tmp_project), "--step", "init_project"]
    )
    state_file = tmp_project / ".context" / "lincoln-setup-state.yaml"
    assert exit_code == 0
    assert state_file.exists()
    data = yaml.safe_load(state_file.read_text(encoding="utf-8"))
    assert data["steps"]["init_project"]["status"] == "completed"


def test_cli_is_setup_complete_returns_nonzero_when_incomplete(setup_mod, tmp_project):
    exit_code = setup_mod.main(["is-setup-complete", "--root", str(tmp_project)])
    assert exit_code == 1


def test_cli_is_setup_complete_returns_zero_when_all_steps_done(setup_mod, tmp_project):
    setup_mod._mark_step(tmp_project, "skills", "completed")
    setup_mod._mark_step(tmp_project, "clis", "completed")
    setup_mod._mark_step(tmp_project, "repo_config", "completed")
    setup_mod._mark_step(tmp_project, "init_project", "completed")
    exit_code = setup_mod.main(["is-setup-complete", "--root", str(tmp_project)])
    assert exit_code == 0


def test_confirm_yes_for_all_matches_single_y():
    setup_mod = _load_setup_module()
    with patch("builtins.input", return_value="y"):
        assert setup_mod.confirm("Install X?", auto_yes=False) is True


def test_confirm_no_for_all_matches_single_n():
    setup_mod = _load_setup_module()
    with patch("builtins.input", return_value="n"):
        assert setup_mod.confirm("Install X?", auto_yes=False) is False


def test_confirm_auto_yes_returns_true_without_input():
    setup_mod = _load_setup_module()
    assert setup_mod.confirm("Install X?", auto_yes=True) is True
