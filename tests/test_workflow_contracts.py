import re
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def workflow():
    root = Path(__file__).resolve().parents[1]
    workflow_path = root / ".claude" / "workflows" / "interview-to-knowledge.yaml"
    return yaml.safe_load(workflow_path.read_text(encoding="utf-8"))


@pytest.fixture
def validator_source():
    root = Path(__file__).resolve().parents[1]
    validator_path = root / ".claude" / "skills" / "lc-workflow" / "validators" / "validate.py"
    return validator_path.read_text(encoding="utf-8")


def _extract_registry_names(source, registry_name):
    pattern = rf"{registry_name}\s*=\s*\{{([^}}]+)\}}"
    match = re.search(pattern, source, re.DOTALL)
    if not match:
        raise ValueError(f"Could not find {registry_name} in validator source")
    return set(re.findall(r'"(\w+)"', match.group(1)))


def test_workflow_checks_exist_in_validator_registry(workflow, validator_source):
    entry_names = _extract_registry_names(validator_source, "ENTRY_CHECKS")
    exit_names = _extract_registry_names(validator_source, "EXIT_CHECKS")

    used_entry = set()
    used_exit = set()
    for step in workflow["workflow"]["steps"]:
        for check in step.get("entry_checks", []):
            used_entry.add(check["check"])
        for check in step.get("exit_checks", []):
            used_exit.add(check["check"])

    assert used_entry <= entry_names, f"Missing entry checks: {used_entry - entry_names}"
    assert used_exit <= exit_names, f"Missing exit checks: {used_exit - exit_names}"


def test_propose_step_requires_tdd_plan_ready(workflow):
    propose = next(s for s in workflow["workflow"]["steps"] if s["id"] == "propose")
    entry_checks = [c["check"] for c in propose.get("entry_checks", [])]
    assert "tdd_plan_ready" in entry_checks


def test_propose_step_uses_tdd_plan_as_input_file(workflow):
    propose = next(s for s in workflow["workflow"]["steps"] if s["id"] == "propose")
    assert propose.get("input_file") == "{process_slug}/designs/{design_id}/tdd-plan.md"


def test_process_artifacts_are_scoped_to_process_slug(workflow):
    process_prefixes = (
        "designs/",
        "docs/research/",
        "interviews/",
        "openspec/changes/",
        "recordings/",
        "requirements/",
    )
    for step in workflow["workflow"]["steps"]:
        for artifact in step.get("artifacts", []):
            assert not artifact.startswith(process_prefixes), (
                f"Process artifact is not process-scoped: {artifact}"
            )


def test_sync_knowledge_uses_root_knowledge(workflow):
    sync = next(s for s in workflow["workflow"]["steps"] if s["id"] == "sync-knowledge")
    artifacts = sync.get("artifacts", [])
    assert any(a.startswith("knowledge/03-features/") for a in artifacts)
    assert not any(a.startswith("docs/knowledge/") for a in artifacts)


def test_clarify_artifacts_use_root_prd_path(workflow):
    clarify = next(s for s in workflow["workflow"]["steps"] if s["id"] == "clarify")
    artifacts = [a for a in clarify.get("artifacts", [])]
    assert any(a == "{process_slug}/prd.md" for a in artifacts)
    assert not any("requirements/{session_id}/prd.md" in a for a in artifacts)


def test_clarify_exit_checks_include_prd_validators(workflow, validator_source):
    clarify = next(s for s in workflow["workflow"]["steps"] if s["id"] == "clarify")
    exit_checks = {c["check"] for c in clarify.get("exit_checks", [])}
    exit_names = _extract_registry_names(validator_source, "EXIT_CHECKS")
    assert "prd_has_required_sections" in exit_checks
    assert "prd_snapshot_present" in exit_checks
    assert exit_checks <= exit_names
