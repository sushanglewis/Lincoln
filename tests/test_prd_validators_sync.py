"""Dual-registry consistency for the two Lincoln PRD validators (issue-129).

The PRD structural rules live in two places that must stay in lockstep:
- scripts/validate_stage.py (stage YAML gates, run by stage_loader)
- .claude/skills/lc-workflow/validators/validate.py (workflow YAML exit_checks)

These tests fail as soon as one side gains a PRD section or check the other lacks.
"""

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(ROOT / ".claude" / "skills" / "lc-workflow" / "validators"))
import validate  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "validate_stage_sync_check", ROOT / "scripts" / "validate_stage.py"
)
validate_stage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_stage)

PRD_EXIT_CHECKS = {
    "prd_has_required_sections",
    "prd_snapshot_present",
    "prd_content_hygiene",
    "prd_cross_validated",
}


def test_prd_exit_checks_registered_in_both_validators():
    for name in PRD_EXIT_CHECKS:
        assert name in validate.EXIT_CHECKS, f"lc-workflow validator missing exit check: {name}"
        assert name in validate_stage.EXIT_CHECKS, f"validate_stage missing exit check: {name}"


def test_required_prd_sections_match():
    assert validate.REQUIRED_PRD_SECTIONS == validate_stage.REQUIRED_PRD_SECTIONS
