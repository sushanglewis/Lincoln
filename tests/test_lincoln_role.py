"""Tests for scripts/lincoln_role.py."""

import sys

import pytest

from scripts import lincoln_role as lr


@pytest.fixture
def fake_agents(tmp_path, monkeypatch):
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "pm.md").write_text("---\nname: PM\ndescription: PM role\n---\n\nBody\n", encoding="utf-8")
    monkeypatch.setattr(lr, "AGENTS_DIR", agents_dir)
    return agents_dir


def test_main_prints_role(fake_agents, capsys):
    sys.argv = ["lincoln_role.py", "--role", "pm"]
    assert lr.main() == 0
    out = capsys.readouterr().out
    assert "PM role" in out
    assert "Body" in out


def test_main_with_topic(fake_agents, capsys):
    sys.argv = ["lincoln_role.py", "--role", "pm", "foo", "bar"]
    assert lr.main() == 0
    out = capsys.readouterr().out
    assert "Topic/context: foo bar" in out


def test_main_missing_role(fake_agents, capsys):
    sys.argv = ["lincoln_role.py", "--role", "missing"]
    assert lr.main() == 1
    assert "ERROR: agent role not found" in capsys.readouterr().err


def test_main_invalid_role_name(fake_agents, capsys):
    sys.argv = ["lincoln_role.py", "--role", "../../etc/passwd"]
    assert lr.main() == 1
    err = capsys.readouterr().err
    assert "Invalid" in err
