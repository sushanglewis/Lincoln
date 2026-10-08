"""Tests for the 少即是多 (Less is More) artifact-writing policy (#126).

The policy must live outside the universal agent contract (default.md):
it applies only when generating deliverable artifacts, not during
exploration / research / deep-thinking stages.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / ".claude" / "policies" / "less-is-more.md"
POLICY_REF = ".claude/policies/less-is-more.md"

# Surfaces that generate human-facing artifacts and must reference the policy.
ARTIFACT_GENERATING_FILES = [
    ROOT / ".claude" / "agents" / "pm.md",
    ROOT / ".claude" / "skills" / "clarify-requirements" / "prompts" / "main.md",
    ROOT / ".claude" / "skills" / "draft-product-design" / "prompts" / "main.md",
    ROOT / ".claude" / "skills" / "build-product-prototype" / "prompts" / "main.md",
    ROOT / ".claude" / "skills" / "lc-handoff" / "SKILL.md",
    ROOT / ".claude" / "skills" / "lc-research-report" / "prompts" / "main.md",
]


def test_policy_exists_with_core_principles():
    text = POLICY_PATH.read_text(encoding="utf-8")
    assert "少即是多" in text
    assert "结论先行" in text
    assert "删除测试" in text
    assert "三分钟可读" in text
    # Reader/purpose-driven generation
    assert "读者" in text and "用途" in text
    # Explicitly scoped: not for research/exploration stages
    assert "不适用" in text


def test_policy_not_in_universal_contract():
    default = (ROOT / ".claude" / "agents" / "default.md").read_text(encoding="utf-8")
    assert "少即是多" not in default, (
        "少即是多 must not live in default.md — it would be injected into "
        "research/exploration stages where it does not apply"
    )


def test_artifact_generating_surfaces_reference_policy():
    for path in ARTIFACT_GENERATING_FILES:
        text = path.read_text(encoding="utf-8")
        assert POLICY_REF in text, (
            f"{path.relative_to(ROOT)}: artifact-generating surface must "
            f"reference {POLICY_REF}"
        )
