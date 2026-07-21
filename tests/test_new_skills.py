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


def test_lc_benchmark_skill_exists():
    root = Path(__file__).resolve().parents[1]
    skill = root / ".claude" / "skills" / "lc-benchmark" / "SKILL.md"
    assert skill.exists()
    text = skill.read_text(encoding="utf-8").lower()
    assert "benchmark" in text
    assert "opt-in" in text


def test_new_stages_registered_in_bundle_skill():
    root = Path(__file__).resolve().parents[1]
    skill_md = root / ".claude" / "skills" / "lc-workflow" / "SKILL.md"
    assert skill_md.exists()
    text = skill_md.read_text(encoding="utf-8").lower()
    assert "lc-build-codebase-knowledge" in text
    assert "lc-explore-opensource" in text
    assert "lc-workflow-router" in text



def test_lc_wf_skill_mentions_pm_research():
    root = Path(__file__).resolve().parents[1]
    skill_md = root / ".claude" / "skills" / "lc-wf" / "SKILL.md"
    assert skill_md.exists()
    assert "lc-wf-pm-research" in skill_md.read_text(encoding="utf-8")


def test_pm_research_skills_exist():
    root = Path(__file__).resolve().parents[1]
    names = [
        "lc-research-scope",
        "lc-first-principles",
        "lc-stakeholder-research",
        "lc-market-research",
        "lc-product-research",
        "lc-competitive-analysis",
        "lc-collect-intelligence",
        "lc-analyze-frameworks",
        "lc-storytelling",
        "lc-research-report",
    ]
    for name in names:
        skill_dir = root / ".claude" / "skills" / name
        assert skill_dir.exists(), f"missing skill dir: {name}"
        assert (skill_dir / "SKILL.md").exists(), f"missing SKILL.md: {name}"
        assert (skill_dir / "prompts" / "main.md").exists(), f"missing prompt: {name}"
        text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        assert f"Using [{name}]" in text, f"missing Using clause: {name}"
