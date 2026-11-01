#!/usr/bin/env python3
"""Record and validate cross-functional reviews for one PRD version."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import jsonschema
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lincoln_paths import atomic_write_text  # noqa: E402

SCHEMA_VERSION = "1.0.0"
ROLES = ("pm", "design", "engineering", "qa")
STATUSES = ("pending", "approved", "changes_requested")
SCHEMA_PATH = PROJECT_ROOT / ".claude" / "schemas" / "prd-review.schema.json"
UTC_TIMESTAMP_ERROR = "reviewed_at must be a UTC ISO8601 timestamp such as 2026-11-01T10:30:00Z"


class ReviewError(RuntimeError):
    """A review document or delivery-baseline validation error."""


def _pending_review() -> dict[str, Any]:
    return {
        "status": "pending",
        "actor": None,
        "reviewed_at": None,
        "notes": "",
    }


def new_review_document(prd_version: str) -> dict[str, Any]:
    """Return a review document with all four roles pending."""
    _validate_prd_version(prd_version)
    return {
        "schema_version": SCHEMA_VERSION,
        "prd_version": prd_version,
        "reviews": {role: _pending_review() for role in ROLES},
    }


def _validate_prd_version(prd_version: str) -> None:
    if not isinstance(prd_version, str) or not prd_version.startswith("v"):
        raise ReviewError("prd_version must use the PRD version format vX.Y")
    parts = prd_version[1:].split(".")
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        raise ReviewError("prd_version must use the PRD version format vX.Y")


def _validate_utc_timestamp(value: str) -> None:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ReviewError(UTC_TIMESTAMP_ERROR)
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except (TypeError, ValueError) as exc:
        raise ReviewError(UTC_TIMESTAMP_ERROR) from exc
    if parsed.tzinfo != timezone.utc or "T" not in value:
        raise ReviewError(UTC_TIMESTAMP_ERROR)


def _schema_validator() -> jsonschema.Draft7Validator:
    schema = yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))
    return jsonschema.Draft7Validator(schema)


def validate_document(document: Any) -> dict[str, Any]:
    """Validate the complete review contract and return the document."""
    errors = sorted(
        _schema_validator().iter_errors(document),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        details = []
        for error in errors:
            location = ".".join(str(part) for part in error.absolute_path) or "document"
            details.append(f"{location}: {error.message}")
        raise ReviewError("Invalid prd-review.yaml: " + "; ".join(details))

    for role in ROLES:
        reviewed_at = document["reviews"][role]["reviewed_at"]
        if reviewed_at is not None:
            try:
                _validate_utc_timestamp(reviewed_at)
            except ReviewError as exc:
                raise ReviewError(f"reviews.{role}.reviewed_at: {exc}") from exc
    return document


def load_review_document(path: Path) -> dict[str, Any]:
    """Load and schema-validate a review document."""
    if not path.exists():
        raise ReviewError(f"Review file not found: {path}")
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ReviewError(f"Could not read review file {path}: {exc}") from exc
    return validate_document(document)


def _write_review_document(path: Path, document: dict[str, Any]) -> None:
    validate_document(document)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(
            path,
            yaml.safe_dump(document, allow_unicode=True, sort_keys=False),
        )
    except OSError as exc:
        raise ReviewError(f"Could not write review file {path}: {exc}") from exc


def record_review(
    path: Path,
    *,
    prd_version: str,
    role: str,
    status: str,
    actor: str | None = None,
    reviewed_at: str | None = None,
    notes: str = "",
) -> dict[str, Any]:
    """Record one role's decision without silently crossing PRD versions."""
    _validate_prd_version(prd_version)
    if role not in ROLES:
        raise ReviewError(f"role must be one of: {', '.join(ROLES)}")
    if status not in STATUSES:
        raise ReviewError(f"status must be one of: {', '.join(STATUSES)}")

    if path.exists():
        document = load_review_document(path)
        if document["prd_version"] != prd_version:
            raise ReviewError(
                f"PRD version drift: review file is {document['prd_version']}, "
                f"but record requested {prd_version}. Run reset-for-version first."
            )
    else:
        document = new_review_document(prd_version)

    if status == "pending":
        if actor is not None or reviewed_at is not None:
            raise ReviewError("pending reviews must not include actor or reviewed_at")
        review = _pending_review()
        review["notes"] = notes
    else:
        if not actor or not actor.strip():
            raise ReviewError(f"actor is required when status is {status}")
        reviewed_at = reviewed_at or datetime.now(timezone.utc).isoformat(
            timespec="seconds"
        ).replace("+00:00", "Z")
        _validate_utc_timestamp(reviewed_at)
        review = {
            "status": status,
            "actor": actor,
            "reviewed_at": reviewed_at,
            "notes": notes,
        }

    document["reviews"][role] = review
    _write_review_document(path, document)
    return document


def validate_review(path: Path, *, prd_version: str) -> dict[str, Any]:
    """Require all four roles to approve the exact requested PRD version."""
    document = load_review_document(path)
    if document["prd_version"] != prd_version:
        raise ReviewError(
            f"PRD version drift: review file is {document['prd_version']}, "
            f"but delivery baseline is {prd_version}. Reset and re-review the current PRD."
        )

    failures = []
    for role in ROLES:
        status = document["reviews"][role]["status"]
        if status == "changes_requested":
            failures.append(f"{role}: changes_requested must be resolved")
        elif status != "approved":
            failures.append(f"{role}: review is {status}, expected approved")
    if failures:
        raise ReviewError(
            f"PRD {prd_version} is not an approved delivery baseline: "
            + "; ".join(failures)
        )
    return document


def reset_for_version(path: Path, *, prd_version: str) -> dict[str, Any]:
    """Invalidate all old decisions by resetting reviews for a new PRD version."""
    document = new_review_document(prd_version)
    _write_review_document(path, document)
    return document


def _add_file_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--file",
        type=Path,
        default=Path("prd-review.yaml"),
        help="Review sidecar path (default: prd-review.yaml)",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Record and validate four-role PRD review baselines"
    )
    subparsers = parser.add_subparsers(dest="action", required=True)

    record_parser = subparsers.add_parser("record", help="Record one role review")
    _add_file_argument(record_parser)
    record_parser.add_argument("--prd-version", required=True)
    record_parser.add_argument("--role", required=True, choices=ROLES)
    record_parser.add_argument("--status", required=True, choices=STATUSES)
    record_parser.add_argument("--actor")
    record_parser.add_argument("--reviewed-at", help="UTC ISO8601; defaults to now")
    record_parser.add_argument("--notes", default="")

    validate_parser = subparsers.add_parser(
        "validate", help="Validate the four-role delivery baseline"
    )
    _add_file_argument(validate_parser)
    validate_parser.add_argument("--prd-version", required=True)

    reset_parser = subparsers.add_parser(
        "reset-for-version", help="Reset all reviews after a PRD version change"
    )
    _add_file_argument(reset_parser)
    reset_parser.add_argument("--prd-version", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.action == "record":
            document = record_review(
                args.file,
                prd_version=args.prd_version,
                role=args.role,
                status=args.status,
                actor=args.actor,
                reviewed_at=args.reviewed_at,
                notes=args.notes,
            )
            print(
                f"Recorded {args.role}={args.status} for PRD "
                f"{document['prd_version']} in {args.file}"
            )
        elif args.action == "validate":
            document = validate_review(args.file, prd_version=args.prd_version)
            print(f"PRD review baseline approved: {document['prd_version']}")
        elif args.action == "reset-for-version":
            document = reset_for_version(args.file, prd_version=args.prd_version)
            print(f"Reset all PRD reviews to pending for {document['prd_version']}")
    except ReviewError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
