from pathlib import Path

import yaml


def test_build_codebase_knowledge_skill_exists():
    root = Path(__file__).resolve().parents[1]
    skill = root / ".claude" / "skills" / "lc-build-codebase-knowledge" / "SKILL.md"
    assert skill.exists()
    assert "build codebase knowledge" in skill.read_text(encoding="utf-8").lower()


def test_explore_opensource_skill_exists():
    root = Path(__file__).resolve().parents[1]
    skill = root / ".claude" / "skills" / "lc-explore-opensource" / "SKILL.md"
    assert skill.exists()
    prompt = root / ".claude" / "skills" / "lc-explore-opensource" / "prompts" / "explore-opensource.md"
    assert prompt.exists()


def test_new_stages_registered_in_bundle_skill():
    root = Path(__file__).resolve().parents[1]
    skill_md = root / ".claude" / "skills" / "lc-workflow" / "SKILL.md"
    assert skill_md.exists()
    text = skill_md.read_text(encoding="utf-8").lower()
    assert "lc-build-codebase-knowledge" in text
    assert "lc-explore-opensource" in text
    assert "lc-workflow-router" in text
