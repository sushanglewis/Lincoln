"""Tests for behavioral-shaping contract consistency (#65)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = ROOT / ".claude" / "agents"
SKILLS_DIR = ROOT / ".claude" / "skills"


def _load_after_frontmatter(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return text
    end = text.find("---", 3)
    if end == -1:
        return text
    return text[end + 3 :]


@pytest.mark.parametrize("agent_file", sorted(AGENTS_DIR.glob("*.md")), ids=lambda p: p.name)
def test_agent_contains_contract_elements(agent_file: Path):
    body = _load_after_frontmatter(agent_file)
    has_subagent_stop = "<SUBAGENT-STOP>" in body
    has_red_flags = "| Thought |" in body and "| Reality |" in body
    has_announce = "Announce skill use" in body or "Using [" in body
    has_contract_ref = "_contract.md" in body

    assert has_subagent_stop or has_contract_ref, (
        f"{agent_file.name}: missing <SUBAGENT-STOP> or reference to _contract.md"
    )
    assert has_red_flags or has_contract_ref, (
        f"{agent_file.name}: missing Red Flags table or reference to _contract.md"
    )
    assert has_announce or has_contract_ref, (
        f"{agent_file.name}: missing announce skill use rule or reference to _contract.md"
    )


def _first_purpose_paragraph(body: str) -> str:
    """Return the first paragraph under a ## Purpose section, or empty string."""
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
