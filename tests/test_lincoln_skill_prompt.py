"""Tests for scripts/lincoln_skill_prompt.py."""

import sys

import pytest

from scripts import lincoln_skill_prompt as lsp


@pytest.fixture
def fake_skills(tmp_path, monkeypatch):
    skills_dir = tmp_path / "skills"
    skill_dir = skills_dir / "demo-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: Demo\ndescription: Demo skill\n---\n\nSkill body\n", encoding="utf-8")
    (skill_dir / "prompts").mkdir()
    (skill_dir / "prompts" / "main.md").write_text("# Prompt\nDo thing.\n", encoding="utf-8")
    monkeypatch.setattr(lsp, "SKILLS_DIR", skills_dir)
    return skills_dir


def test_main_prints_skill_and_prompt(fake_skills, capsys):
    sys.argv = ["lincoln_skill_prompt.py", "--skill", "demo-skill"]
    assert lsp.main() == 0
    out = capsys.readouterr().out
    assert "Demo skill" in out
    assert "Skill body" in out
    assert "# Prompt" in out


def test_main_missing_skill(fake_skills, capsys):
    sys.argv = ["lincoln_skill_prompt.py", "--skill", "missing"]
    assert lsp.main() == 1
    assert "ERROR: skill not found" in capsys.readouterr().err


def test_main_invalid_skill_name(fake_skills, capsys):
    sys.argv = ["lincoln_skill_prompt.py", "--skill", "../../etc/passwd"]
    assert lsp.main() == 1
    assert "Invalid" in capsys.readouterr().err
