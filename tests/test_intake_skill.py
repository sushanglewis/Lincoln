"""Content guards for the session-intake extension of lc-workflow-router."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / ".claude" / "skills" / "lc-workflow-router"
INTAKE_PROMPT = SKILL_DIR / "prompts" / "intake-prompt.md"


def _read(path):
    return path.read_text(encoding="utf-8")


def test_intake_prompt_exists_with_johari_quadrants():
    content = _read(INTAKE_PROMPT)
    for quadrant in ("知道自己知道", "知道自己不知道", "不知道自己知道", "不知道自己不知道"):
        assert quadrant in content, f"missing Johari quadrant: {quadrant}"


def test_intake_prompt_bounds_recon():
    content = _read(INTAKE_PROMPT)
    assert "摸排" in content
    assert "8" in content, "read-only operation cap missing"
    assert "lc-build-codebase-knowledge" in content, "deep-scan ban missing"


def test_intake_prompt_limits_questions_and_defines_convergence():
    content = _read(INTAKE_PROMPT)
    assert "3" in content, "per-round question cap missing"
    assert "验收标准" in content, "convergence criterion missing"


def test_router_skill_triggers_on_not_started():
    assert "not_started" in _read(SKILL_DIR / "SKILL.md")


def test_router_prompt_references_intake_prompt():
    assert "intake-prompt.md" in _read(SKILL_DIR / "prompts" / "router-prompt.md")


def test_default_agent_contract_mentions_opening_guidance():
    assert "开场引导" in _read(ROOT / ".claude" / "agents" / "default.md")


def test_claude_md_mentions_opening_guidance():
    assert "开场引导" in _read(ROOT / "CLAUDE.md")


def test_clarify_prompt_covers_johari_and_acceptance_criteria():
    prompt = _read(ROOT / ".claude" / "skills" / "clarify-requirements" / "prompts" / "main.md")
    assert "认知象限" in prompt
    assert "验收标准" in prompt


def test_workflow_router_stage_goal_mentions_recon():
    assert "摸排" in _read(ROOT / ".claude" / "stages" / "workflow-router.yaml")
