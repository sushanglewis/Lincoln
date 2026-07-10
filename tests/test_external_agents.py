"""Tests for imported external agent files under .claude/agents/external/."""
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = ROOT / ".claude" / "agents"
EXTERNAL_DIR = AGENTS_DIR / "external"


def parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        return yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return {}


@pytest.fixture
def external_agent_files():
    return list(EXTERNAL_DIR.rglob("agents/*.md"))


# ---------------------------------------------------------------------------
# Frontmatter schema tests
# ---------------------------------------------------------------------------


def test_external_agent_files_exist(external_agent_files):
    if not external_agent_files:
        pytest.skip(f"No imported agent files found under {EXTERNAL_DIR}/**/agents/; run scripts/sync-external-agents.sh")


@pytest.mark.parametrize("agent_path", list(EXTERNAL_DIR.rglob("agents/*.md")), ids=lambda p: str(p.relative_to(ROOT)))
def test_external_agent_has_required_frontmatter(agent_path):
    text = agent_path.read_text(encoding="utf-8")
    front = parse_frontmatter(text)

    assert "name" in front, f"{agent_path.name}: missing 'name'"
    assert "description" in front, f"{agent_path.name}: missing 'description'"
    assert "source" in front, f"{agent_path.name}: missing 'source'"
    assert "ref" in front, f"{agent_path.name}: missing 'ref'"
    assert "license" in front, f"{agent_path.name}: missing 'license'"
    assert "original_name" in front, f"{agent_path.name}: missing 'original_name'"


@pytest.mark.parametrize("agent_path", list(EXTERNAL_DIR.rglob("agents/*.md")), ids=lambda p: str(p.relative_to(ROOT)))
def test_external_agent_has_attribution_comment(agent_path):
    text = agent_path.read_text(encoding="utf-8")
    assert "Imported from" in text, f"{agent_path.name}: missing import attribution comment"
    assert "Original name:" in text, f"{agent_path.name}: missing original name attribution"


@pytest.mark.parametrize("agent_path", list(EXTERNAL_DIR.rglob("agents/*.md")), ids=lambda p: str(p.relative_to(ROOT)))
def test_external_agent_name_is_prefixed(agent_path):
    text = agent_path.read_text(encoding="utf-8")
    front = parse_frontmatter(text)
    name = front.get("name", "")
    stem = agent_path.stem
    assert name == stem, f"{agent_path.name}: frontmatter name '{name}' does not match filename '{stem}'"
    assert "-" in name, f"{agent_path.name}: name '{name}' missing prefix separator"


# ---------------------------------------------------------------------------
# Global uniqueness tests
# ---------------------------------------------------------------------------


def test_external_agent_names_are_globally_unique():
    names = set()
    for agent_path in EXTERNAL_DIR.rglob("agents/*.md"):
        front = parse_frontmatter(agent_path.read_text(encoding="utf-8"))
        name = front.get("name")
        assert name not in names, f"Duplicate external agent name: {name}"
        names.add(name)

    # Ensure no collision with Lincoln native agents.
    for native_path in AGENTS_DIR.glob("*.md"):
        front = parse_frontmatter(native_path.read_text(encoding="utf-8"))
        name = front.get("name")
        if name:
            assert name not in names, f"External agent name collides with native agent: {name}"


# ---------------------------------------------------------------------------
# extends resolution tests
# ---------------------------------------------------------------------------


def test_lincoln_role_extends_resolve():
    """Lincoln role agents must only extend files that exist."""
    claude_dir = ROOT / ".claude"
    for role_path in AGENTS_DIR.glob("*.md"):
        front = parse_frontmatter(role_path.read_text(encoding="utf-8"))
        for extends_ref in front.get("extends", []):
            resolved = claude_dir / extends_ref
            if not resolved.exists():
                pytest.skip(
                    f"{role_path.name}: extends '{extends_ref}' does not resolve; "
                    f"run scripts/sync-external-agents.sh"
                )
