"""Integration tests for core-v2 checks in the shared workflow validator."""

from pathlib import Path
import shutil

from scripts.lincoln_prd_review import record_review

from .conftest import run_validator

ROOT = Path(__file__).resolve().parents[2]


def _copy_trace_package(tmp_project: Path) -> Path:
    source = ROOT / "tests" / "fixtures" / "traceability" / "valid" / "issue-144"
    target = tmp_project / "lc-test"
    shutil.copytree(source, target)
    prd = target / "pages" / "docs" / "prd.html"
    prd.write_text("<!-- prd-contract: core-v2 -->\n" + prd.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def test_core_v2_quality_check_runs_through_shared_registry(tmp_project):
    docs = tmp_project / "lc-test" / "pages" / "docs"
    docs.mkdir(parents=True)
    shutil.copy(ROOT / "tests" / "fixtures" / "prd-quality" / "core-v2-golden.md", docs / "prd.html")

    assert run_validator(tmp_project, "prd_quality_contract", "lc-test/pages/docs/prd.html") == 0


def test_legacy_package_skips_new_trace_and_review_gates(tmp_project):
    docs = tmp_project / "lc-test" / "pages" / "docs"
    docs.mkdir(parents=True)
    (docs / "prd.html").write_text("<!-- version: v1.0 -->\n# Legacy PRD", encoding="utf-8")

    assert run_validator(tmp_project, "prd_traceability", "tdd") == 0
    assert run_validator(tmp_project, "prototype_traceability") == 0
    assert run_validator(tmp_project, "prototype_annotations_complete") == 0
    assert run_validator(tmp_project, "prd_review_complete", "lc-test/pages/docs/prd-review.yaml") == 0


def test_core_v2_trace_and_prototype_checks_share_one_package(tmp_project):
    _copy_trace_package(tmp_project)

    assert run_validator(tmp_project, "prd_traceability", "tdd") == 0
    assert run_validator(tmp_project, "prototype_traceability") == 0


def test_core_v2_trace_gate_fails_when_sidecar_is_missing(tmp_project):
    docs = tmp_project / "lc-test" / "pages" / "docs"
    docs.mkdir(parents=True)
    (docs / "prd.html").write_text("<!-- prd-contract: core-v2 -->\n<!-- version: v1.0 -->", encoding="utf-8")

    assert run_validator(tmp_project, "prd_traceability", "clarify") == 1


def test_core_v2_marker_detection_cannot_be_bypassed_by_case(tmp_project):
    docs = tmp_project / "lc-test" / "pages" / "docs"
    docs.mkdir(parents=True)
    (docs / "prd.html").write_text("<!-- PRD-CONTRACT: CORE-V2 -->\n<!-- version: v1.0 -->", encoding="utf-8")

    assert run_validator(tmp_project, "prd_traceability", "clarify") == 1


def test_core_v2_requires_structured_prototype_annotations(tmp_project):
    package = _copy_trace_package(tmp_project)
    assert run_validator(tmp_project, "prototype_annotations_complete") == 1


def test_review_gate_requires_four_roles_on_current_prd_version(tmp_project):
    package = _copy_trace_package(tmp_project)
    review = package / "pages" / "docs" / "prd-review.yaml"
    for role in ("pm", "design", "engineering", "qa"):
        record_review(review, prd_version="v1.0", role=role, status="approved", actor=role)

    assert run_validator(tmp_project, "prd_review_complete", "lc-test/pages/docs/prd-review.yaml") == 0

    prd = package / "pages" / "docs" / "prd.html"
    prd.write_text(prd.read_text(encoding="utf-8").replace("v1.0", "v1.1"), encoding="utf-8")
    assert run_validator(tmp_project, "prd_review_complete", "lc-test/pages/docs/prd-review.yaml") == 1
