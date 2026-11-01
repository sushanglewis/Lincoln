"""Tests for the four-role PRD review and version lifecycle contract."""
from __future__ import annotations

import copy
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest
import yaml

from scripts import lincoln_prd_review as review

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "lincoln_prd_review.py"
SCHEMA_PATH = ROOT / ".claude" / "schemas" / "prd-review.schema.json"
TIMESTAMP = "2026-11-01T10:00:00Z"


def approved_document(version: str = "v1.0") -> dict:
    document = review.new_review_document(version)
    for role in review.ROLES:
        document["reviews"][role] = {
            "status": "approved",
            "actor": f"{role}-reviewer",
            "reviewed_at": TIMESTAMP,
            "notes": "approved for test",
        }
    return document


def write_document(path: Path, document: dict) -> None:
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")


def test_schema_is_valid_draft7_and_accepts_complete_document():
    schema = yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft7Validator.check_schema(schema)
    jsonschema.Draft7Validator(schema).validate(approved_document())


@pytest.mark.parametrize(
    "mutate, expected_path",
    [
        (lambda doc: doc["reviews"].pop("qa"), "reviews"),
        (lambda doc: doc["reviews"].update(support=doc["reviews"]["pm"]), "reviews"),
        (lambda doc: doc["reviews"]["pm"].update(status="maybe"), "reviews.pm"),
        (lambda doc: doc.update(prd_version="1.0"), "prd_version"),
        (lambda doc: doc.update(schema_version="2.0.0"), "schema_version"),
    ],
)
def test_schema_rejects_invalid_contract(mutate, expected_path):
    document = approved_document()
    mutate(document)
    with pytest.raises(review.ReviewError, match=expected_path):
        review.validate_document(document)


def test_pending_review_must_not_have_actor_or_timestamp():
    document = review.new_review_document("v1.0")
    document["reviews"]["pm"]["actor"] = "pm-alice"
    with pytest.raises(review.ReviewError, match="reviews.pm"):
        review.validate_document(document)


def test_decided_review_requires_actor_and_timestamp():
    document = review.new_review_document("v1.0")
    document["reviews"]["pm"]["status"] = "approved"
    with pytest.raises(review.ReviewError, match="reviews.pm"):
        review.validate_document(document)


@pytest.mark.parametrize(
    "timestamp",
    [
        "2026-11-01T10:00:00+08:00",
        "2026-11-01T10:00:00",
        "2026-11-01 10:00:00Z",
        "2026-02-30T10:00:00Z",
    ],
)
def test_reviewed_at_requires_real_utc_iso8601(timestamp):
    document = approved_document()
    document["reviews"]["pm"]["reviewed_at"] = timestamp
    with pytest.raises(review.ReviewError):
        review.validate_document(document)


def test_record_creates_file_with_other_roles_pending(tmp_path):
    path = tmp_path / "prd-review.yaml"
    document = review.record_review(
        path,
        prd_version="v1.0",
        role="pm",
        status="approved",
        actor="pm-alice",
        reviewed_at=TIMESTAMP,
        notes="scope confirmed",
    )

    assert document["reviews"]["pm"] == {
        "status": "approved",
        "actor": "pm-alice",
        "reviewed_at": TIMESTAMP,
        "notes": "scope confirmed",
    }
    for role in ("design", "engineering", "qa"):
        assert document["reviews"][role] == {
            "status": "pending",
            "actor": None,
            "reviewed_at": None,
            "notes": "",
        }
    assert review.load_review_document(path) == document


def test_record_generates_utc_timestamp(tmp_path):
    document = review.record_review(
        tmp_path / "prd-review.yaml",
        prd_version="v1.0",
        role="qa",
        status="approved",
        actor="qa-alice",
    )
    timestamp = document["reviews"]["qa"]["reviewed_at"]
    assert timestamp.endswith("Z")
    review._validate_utc_timestamp(timestamp)


def test_record_pending_clears_previous_decision(tmp_path):
    path = tmp_path / "prd-review.yaml"
    review.record_review(
        path,
        prd_version="v1.0",
        role="pm",
        status="approved",
        actor="pm-alice",
        reviewed_at=TIMESTAMP,
    )
    document = review.record_review(
        path,
        prd_version="v1.0",
        role="pm",
        status="pending",
        notes="reopened",
    )
    assert document["reviews"]["pm"] == {
        "status": "pending",
        "actor": None,
        "reviewed_at": None,
        "notes": "reopened",
    }


def test_record_rejects_actor_for_pending(tmp_path):
    with pytest.raises(review.ReviewError, match="pending"):
        review.record_review(
            tmp_path / "prd-review.yaml",
            prd_version="v1.0",
            role="pm",
            status="pending",
            actor="pm-alice",
        )


def test_record_rejects_missing_actor_and_invalid_timestamp(tmp_path):
    path = tmp_path / "prd-review.yaml"
    with pytest.raises(review.ReviewError, match="actor"):
        review.record_review(
            path,
            prd_version="v1.0",
            role="pm",
            status="approved",
        )
    with pytest.raises(review.ReviewError, match="UTC ISO8601"):
        review.record_review(
            path,
            prd_version="v1.0",
            role="pm",
            status="approved",
            actor="pm-alice",
            reviewed_at="2026-11-01T10:00:00+08:00",
        )
    assert not path.exists()


def test_record_version_drift_fails_without_modifying_file(tmp_path):
    path = tmp_path / "prd-review.yaml"
    original = approved_document("v1.0")
    write_document(path, original)

    with pytest.raises(review.ReviewError, match="version drift.*reset-for-version"):
        review.record_review(
            path,
            prd_version="v1.1",
            role="pm",
            status="approved",
            actor="new-pm",
            reviewed_at=TIMESTAMP,
        )
    assert review.load_review_document(path) == original


def test_validate_requires_all_four_roles_to_approve_same_version(tmp_path):
    path = tmp_path / "prd-review.yaml"
    for role in review.ROLES:
        review.record_review(
            path,
            prd_version="v1.0",
            role=role,
            status="approved",
            actor=f"{role}-reviewer",
            reviewed_at=TIMESTAMP,
        )
    assert review.validate_review(path, prd_version="v1.0")["prd_version"] == "v1.0"


def test_validate_rejects_pending_reviews(tmp_path):
    path = tmp_path / "prd-review.yaml"
    document = approved_document()
    document["reviews"]["qa"] = review._pending_review()
    write_document(path, document)
    with pytest.raises(review.ReviewError, match="qa: review is pending"):
        review.validate_review(path, prd_version="v1.0")


def test_validate_rejects_changes_requested(tmp_path):
    path = tmp_path / "prd-review.yaml"
    document = approved_document()
    document["reviews"]["design"].update(
        status="changes_requested", notes="add empty state"
    )
    write_document(path, document)
    with pytest.raises(review.ReviewError, match="design: changes_requested"):
        review.validate_review(path, prd_version="v1.0")


def test_validate_rejects_version_drift_even_when_old_version_was_approved(tmp_path):
    path = tmp_path / "prd-review.yaml"
    write_document(path, approved_document("v1.0"))
    with pytest.raises(review.ReviewError, match="version drift"):
        review.validate_review(path, prd_version="v1.1")


def test_reset_for_version_invalidates_all_previous_reviews(tmp_path):
    path = tmp_path / "prd-review.yaml"
    write_document(path, approved_document("v1.0"))
    document = review.reset_for_version(path, prd_version="v1.1")

    assert document["schema_version"] == "1.0.0"
    assert document["prd_version"] == "v1.1"
    assert all(
        item == {"status": "pending", "actor": None, "reviewed_at": None, "notes": ""}
        for item in document["reviews"].values()
    )
    with pytest.raises(review.ReviewError, match="pending"):
        review.validate_review(path, prd_version="v1.1")


def test_reset_for_version_can_initialize_missing_file(tmp_path):
    path = tmp_path / "nested" / "prd-review.yaml"
    review.reset_for_version(path, prd_version="v2.0")
    assert review.load_review_document(path)["prd_version"] == "v2.0"


def test_invalid_yaml_and_missing_file_have_actionable_errors(tmp_path):
    path = tmp_path / "prd-review.yaml"
    with pytest.raises(review.ReviewError, match="not found"):
        review.validate_review(path, prd_version="v1.0")
    path.write_text("reviews: [unterminated", encoding="utf-8")
    with pytest.raises(review.ReviewError, match="Could not read"):
        review.validate_review(path, prd_version="v1.0")


def run_cli(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def test_cli_record_validate_and_reset_lifecycle(tmp_path):
    path = tmp_path / "prd-review.yaml"
    for role in review.ROLES:
        result = run_cli(
            tmp_path,
            "record",
            "--file",
            str(path),
            "--prd-version",
            "v1.0",
            "--role",
            role,
            "--status",
            "approved",
            "--actor",
            f"{role}-reviewer",
            "--reviewed-at",
            TIMESTAMP,
        )
        assert result.returncode == 0, result.stderr

    result = run_cli(
        tmp_path, "validate", "--file", str(path), "--prd-version", "v1.0"
    )
    assert result.returncode == 0, result.stderr
    assert "approved: v1.0" in result.stdout

    result = run_cli(
        tmp_path,
        "reset-for-version",
        "--file",
        str(path),
        "--prd-version",
        "v1.1",
    )
    assert result.returncode == 0, result.stderr
    saved = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert saved["prd_version"] == "v1.1"
    assert all(item["status"] == "pending" for item in saved["reviews"].values())


def test_cli_validate_failure_returns_one(tmp_path):
    path = tmp_path / "prd-review.yaml"
    write_document(path, approved_document("v1.0"))
    result = run_cli(
        tmp_path, "validate", "--file", str(path), "--prd-version", "v1.1"
    )
    assert result.returncode == 1
    assert "PRD version drift" in result.stderr


def test_invalid_document_is_not_silently_changed_by_record(tmp_path):
    path = tmp_path / "prd-review.yaml"
    document = approved_document()
    document["reviews"]["pm"]["status"] = "invalid"
    write_document(path, document)
    before = copy.deepcopy(document)
    with pytest.raises(review.ReviewError, match="Invalid prd-review.yaml"):
        review.record_review(
            path,
            prd_version="v1.0",
            role="qa",
            status="approved",
            actor="qa-reviewer",
        )
    assert yaml.safe_load(path.read_text(encoding="utf-8")) == before
