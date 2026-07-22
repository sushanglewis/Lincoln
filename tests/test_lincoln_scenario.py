"""Tests for scripts/lincoln_scenario.py."""

import sys
from pathlib import Path

import pytest
import yaml

from scripts import lincoln_scenario as ls


@pytest.fixture
def fake_scenarios(tmp_path, monkeypatch):
    scenarios_path = tmp_path / "scenarios.yaml"
    scenarios_path.parent.mkdir(parents=True, exist_ok=True)
    scenarios_path.write_text(
        yaml.safe_dump(
            {
                "scenarios": {
                    "make-prd": {
                        "description": "Make PRD",
                        "role": "pm",
                        "skills": ["clarify-requirements"],
                        "goal": "PRD",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(ls, "SCENARIOS_PATH", scenarios_path)
    return scenarios_path


def test_main_prints_scenario(fake_scenarios, capsys):
    sys.argv = ["lincoln_scenario.py", "--scenario", "make-prd"]
    assert ls.main() == 0
    out = capsys.readouterr().out
    assert "Make PRD" in out
    assert "Recommended role: pm" in out
    assert "clarify-requirements" in out


def test_main_with_topic(fake_scenarios, capsys):
    sys.argv = ["lincoln_scenario.py", "--scenario", "make-prd", "login", "flow"]
    assert ls.main() == 0
    out = capsys.readouterr().out
    assert "Topic/context: login flow" in out


def test_main_missing_scenario(fake_scenarios, capsys):
    sys.argv = ["lincoln_scenario.py", "--scenario", "missing"]
    assert ls.main() == 1
    err = capsys.readouterr().err
    assert "ERROR: scenario" in err
    assert "make-prd" in err


def test_main_invalid_scenario_name(fake_scenarios, capsys):
    sys.argv = ["lincoln_scenario.py", "--scenario", "../../x"]
    assert ls.main() == 1
    assert "Invalid" in capsys.readouterr().err
