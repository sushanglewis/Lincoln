"""Pin policy tests for external skill dependencies (#62).

External skills/plugins are behavior-shaping code; they must be pinned to a
known-good full-SHA ref, never a floating branch like `main`.
"""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEPENDENCIES = ROOT / ".claude" / "skills" / "dependencies.yaml"
GIT_SOURCE_PREFIXES = ("http://", "https://", "git@")
FULL_SHA_LENGTH = 40


def _load_dependencies() -> dict:
    return yaml.safe_load(DEPENDENCIES.read_text(encoding="utf-8"))


def _git_sourced_skills() -> dict:
    data = _load_dependencies()
    return {
        name: dep
        for name, dep in data.get("skills", {}).items()
        if dep.get("type") in ("skill", "plugin")
        and str(dep.get("source", "")).startswith(GIT_SOURCE_PREFIXES)
    }


def test_git_sourced_skills_are_pinned_to_full_sha():
    # Arrange / Act
    pinned = _git_sourced_skills()

    # Assert
    assert pinned, "expected at least one git-sourced skill dependency"
    for name, dep in pinned.items():
        ref = str(dep.get("ref", ""))
        assert len(ref) == FULL_SHA_LENGTH and all(
            c in "0123456789abcdef" for c in ref
        ), f"{name}: ref must be a full lowercase SHA, got {ref!r}"


def test_pinned_skills_record_provenance():
    # Arrange / Act
    pinned = _git_sourced_skills()

    # Assert
    for name, dep in pinned.items():
        assert dep.get("license"), f"{name}: license must be recorded"
        assert dep.get("pinned_from"), f"{name}: pinned_from must record the source branch"
        assert dep.get("pinned_at"), f"{name}: pinned_at must record the pin date"
