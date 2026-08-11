"""Tests for behavioral-shaping contract consistency (#65)."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = ROOT / ".claude" / "agents"
SKILLS_DIR = ROOT / ".claude" / "skills"

DEFAULT_PATH = AGENTS_DIR / "default.md"


def _load_after_frontmatter(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return text
    end = text.find("---", 3)
    if end == -1:
        return text
    return text[end + 3:]


def test_default_contract_contains_subagent_principles():
    body = _load_after_frontmatter(DEFAULT_PATH)
    assert "## 核心规则" in body
    assert "子代理调度原则" in body
    assert "优先线性、单会话执行" in body
    assert "fan-out 需要显式许可" in body
    assert "SMART 简报是强制的" in body


def test_default_contract_contains_red_flags():
    body = _load_after_frontmatter(DEFAULT_PATH)
    assert "## 红灯思维（Red Flags）" in body
    assert "| 想法 | 现实 |" in body
    assert "human_gate" in body and "显式确认" in body
    assert "产物必须落回状态文件" in body


def test_default_contract_contains_announce_skill_use():
    body = _load_after_frontmatter(DEFAULT_PATH)
    assert "Using [skill] to [purpose]" in body
    assert "技能使用规则" in body


def test_default_contract_contains_handoff_contract():
    body = _load_after_frontmatter(DEFAULT_PATH)
    assert "交接契约（Handoff Contract）" in body
    assert "Tier 0" in body


@pytest.mark.parametrize("agent_file", sorted(AGENTS_DIR.glob("*.md")), ids=lambda p: p.name)
def test_agent_extends_default_contract(agent_file: Path):
    text = agent_file.read_text(encoding="utf-8")
    assert "agents/default.md" in text, (
        f"{agent_file.name}: must extend agents/default.md"
    )
    assert "_contract.md" not in text, (
        f"{agent_file.name}: must not reference deprecated _contract.md"
    )


def _first_purpose_paragraph(body: str) -> str:
    """Return the first paragraph under a ## Purpose section, or empty string."""
    import re
    match = re.search(r"## Purpose\s*\n\s*(.+?)(?:\n\n|\n## |\Z)", body, re.DOTALL)
    if not match:
        return ""
    return match.group(1).strip()


@pytest.mark.parametrize("skill_file", sorted(SKILLS_DIR.glob("*/SKILL.md")), ids=lambda p: p.parent.name)
def test_skill_opens_with_announce(skill_file: Path):
    body = _load_after_frontmatter(skill_file)
    first_para = _first_purpose_paragraph(body)
    assert "Using [" in first_para, (
        f"{skill_file.parent.name}: Purpose section must declare skill use with 'Using [skill] to ...'"
    )
