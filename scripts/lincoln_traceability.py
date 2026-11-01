#!/usr/bin/env python3
"""Validate the structured PRD traceability sidecar for a process package.

The Markdown/HTML PRD remains the narrative source of truth. The sidecar only
stores stable relationships, with completeness requirements increasing from
clarify to prototype to tdd.

Usage:
    python scripts/lincoln_traceability.py --package issue-144 --stage clarify
    python scripts/lincoln_traceability.py --package /path/to/issue-144 --stage tdd
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import unquote, urlsplit

import jsonschema
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lincoln_index import VERSION_COMMENT_RE

SCHEMA_PATH = PROJECT_ROOT / ".claude" / "schemas" / "prd-traceability.schema.json"
SIDECAR_FILENAME = "pages/docs/prd-traceability.yaml"
STAGES = ("clarify", "prototype", "tdd")

REFERENCE_FIELDS = {
    "story_ids": ("US", "user story"),
    "acceptance_criterion_ids": ("AC", "acceptance criterion"),
    "flow_step_ids": ("FLOW", "flow step"),
    "test_scenario_ids": ("TEST", "test scenario"),
}

STAGE_REQUIREMENTS = {
    "clarify": (
        ("sources", "source"),
        ("story_ids", "user story"),
        ("acceptance_criterion_ids", "acceptance criterion"),
    ),
    "prototype": (
        ("flow_step_ids", "flow step"),
        ("prototype_pages", "prototype page"),
    ),
    "tdd": (("test_scenario_ids", "test scenario"),),
}

ID_PATTERNS = {
    "REQ": re.compile(r"^REQ-[A-Z0-9][A-Z0-9_-]*$"),
    "SRC": re.compile(r"^SRC-[A-Z0-9][A-Z0-9_-]*$"),
    "US": re.compile(r"^US-[A-Z0-9][A-Z0-9_-]*$"),
    "AC": re.compile(r"^AC-[A-Z0-9][A-Z0-9_-]*$"),
    "FLOW": re.compile(r"^FLOW-[A-Z0-9][A-Z0-9_-]*$"),
    "TEST": re.compile(r"^TEST-[A-Z0-9][A-Z0-9_-]*$"),
}

ARTIFACT_SUFFIXES = {".html", ".json", ".md", ".txt", ".yaml", ".yml"}


def _artifact_defines(artifact_corpus: str, identifier: str) -> bool:
    """Match a complete identifier, never a prefix of a longer surviving ID."""
    return re.search(
        rf"(?<![A-Z0-9-]){re.escape(identifier)}(?![A-Z0-9-])",
        artifact_corpus,
    ) is not None


def _json_path(parts: list[Any] | tuple[Any, ...]) -> str:
    if not parts:
        return "$"
    output = "$"
    for part in parts:
        if isinstance(part, int):
            output += f"[{part}]"
        else:
            output += f".{part}"
    return output


def _load_yaml(path: Path) -> tuple[Any | None, str | None]:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")), None
    except OSError as exc:
        return None, f"{path}: cannot read sidecar: {exc}"
    except yaml.YAMLError as exc:
        return None, f"{path}: invalid YAML: {exc}; fix the YAML syntax and retry."


def _prd_path(package_root: Path) -> Path:
    html_path = package_root / "pages" / "docs" / "prd.html"
    if html_path.exists():
        return html_path
    legacy_path = package_root / "prd.md"
    if legacy_path.exists():
        return legacy_path
    return html_path


def _read_artifact_corpus(package_root: Path, sidecar_path: Path) -> str:
    """Read textual artifacts used to resolve stable IDs, excluding old snapshots."""
    chunks: list[str] = []
    for path in sorted(package_root.rglob("*")):
        if not path.is_file() or path == sidecar_path or path.suffix.lower() not in ARTIFACT_SUFFIXES:
            continue
        relative = path.relative_to(package_root)
        if "snapshots" in relative.parts or ".git" in relative.parts:
            continue
        try:
            chunks.append(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError):
            # A broken artifact is reported by its owning validator. Traceability
            # only needs a best-effort corpus for resolving identifiers.
            continue
    return "\n".join(chunks)


def _validate_version(package_root: Path, data: dict[str, Any], errors: list[str]) -> None:
    prd_path = _prd_path(package_root)
    if not prd_path.is_file():
        errors.append(
            f"prd_version: PRD not found at {prd_path}; create the narrative PRD or restore prd.md."
        )
        return

    try:
        prd_text = prd_path.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"prd_version: cannot read {prd_path}: {exc}")
        return

    match = VERSION_COMMENT_RE.search(prd_text)
    if not match:
        errors.append(
            f"prd_version: no version marker in {prd_path}; add '<!-- version: vX.Y -->'."
        )
        return

    actual_version = match.group(1)
    sidecar_version = data.get("prd_version")
    if isinstance(sidecar_version, str) and sidecar_version != actual_version:
        errors.append(
            f"prd_version: sidecar declares {sidecar_version}, but {prd_path} declares "
            f"{actual_version}; update the sidecar to the current PRD version."
        )


def _local_source_path(package_root: Path, uri: str) -> Path | None:
    """Resolve a local source URI; external URLs and document fragments are not fetched."""
    parsed = urlsplit(uri)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    candidate = package_root / unquote(parsed.path)
    try:
        candidate.resolve().relative_to(package_root.resolve())
    except ValueError:
        return candidate
    return candidate


def _validate_source(
    package_root: Path,
    source: dict[str, Any],
    source_path: str,
    errors: list[str],
) -> None:
    uri = source.get("uri")
    if not isinstance(uri, str) or not uri:
        return
    local_path = _local_source_path(package_root, uri)
    if local_path is None:
        return
    try:
        local_path.resolve().relative_to(package_root.resolve())
    except ValueError:
        errors.append(
            f"{source_path}.uri: {uri!r} escapes the process package; use a package-relative source URI."
        )
        return
    if not local_path.is_file():
        errors.append(
            f"{source_path}.uri: local source {uri!r} does not exist under {package_root}; "
            "add the evidence file or correct the URI."
        )


def _safe_prototype_path(package_root: Path, value: str) -> Path | None:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "\\" in value:
        return None
    candidate = package_root.joinpath(*path.parts)
    try:
        candidate.resolve().relative_to(package_root.resolve())
    except ValueError:
        return None
    return candidate


def _validate_references(
    requirement: dict[str, Any],
    requirement_path: str,
    requirement_label: str,
    artifact_corpus: str,
    errors: list[str],
) -> None:
    for field, (prefix, description) in REFERENCE_FIELDS.items():
        references = requirement.get(field)
        if not isinstance(references, list):
            continue
        seen: set[str] = set()
        for index, reference in enumerate(references):
            if not isinstance(reference, str):
                continue
            reference_path = f"{requirement_path}.{field}[{index}]"
            if reference in seen:
                errors.append(
                    f"{reference_path}: duplicate {description} ID {reference!r}; remove the repeated reference."
                )
            seen.add(reference)
            if ID_PATTERNS[prefix].fullmatch(reference) and not _artifact_defines(artifact_corpus, reference):
                errors.append(
                    f"{reference_path}: {reference} is not defined in the PRD or package artifacts; "
                    f"define the {description} or remove the stale reference from {requirement_label}."
                )


def _validate_coverage(
    requirement: dict[str, Any],
    requirement_label: str,
    stage: str,
    errors: list[str],
) -> None:
    if requirement.get("core") is not True:
        return
    for required_stage in STAGES[: STAGES.index(stage) + 1]:
        for field, description in STAGE_REQUIREMENTS[required_stage]:
            values = requirement.get(field)
            if isinstance(values, list) and not values:
                errors.append(
                    f"{requirement_label}.{field}: {stage} requires at least one {description} "
                    f"for core requirement {requirement.get('id', '<unknown>')}; add the missing relationship."
                )


def _validate_semantics(
    package_root: Path,
    data: dict[str, Any],
    sidecar_path: Path,
    stage: str,
    errors: list[str],
) -> None:
    _validate_version(package_root, data, errors)
    artifact_corpus = _read_artifact_corpus(package_root, sidecar_path)
    requirements = data.get("requirements")
    if not isinstance(requirements, list):
        return

    requirement_ids: set[str] = set()
    source_ids: set[str] = set()
    for req_index, requirement in enumerate(requirements):
        if not isinstance(requirement, dict):
            continue
        requirement_path = f"requirements[{req_index}]"
        requirement_id = requirement.get("id")
        requirement_label = (
            f"{requirement_path} ({requirement_id})"
            if isinstance(requirement_id, str) and requirement_id
            else requirement_path
        )

        if isinstance(requirement_id, str):
            if requirement_id in requirement_ids:
                errors.append(
                    f"{requirement_path}.id: duplicate requirement ID {requirement_id!r}; "
                    "assign a unique stable REQ-* ID."
                )
            requirement_ids.add(requirement_id)
            if ID_PATTERNS["REQ"].fullmatch(requirement_id) and not _artifact_defines(artifact_corpus, requirement_id):
                errors.append(
                    f"{requirement_path}.id: {requirement_id} is not defined in the PRD or package artifacts; "
                    "add the requirement to the narrative PRD or remove the stale sidecar entry."
                )

        sources = requirement.get("sources")
        if isinstance(sources, list):
            for source_index, source in enumerate(sources):
                if not isinstance(source, dict):
                    continue
                source_path = f"{requirement_path}.sources[{source_index}]"
                source_id = source.get("id")
                if isinstance(source_id, str):
                    if source_id in source_ids:
                        errors.append(
                            f"{source_path}.id: duplicate source ID {source_id!r}; "
                            "reuse the existing source or assign a unique SRC-* ID."
                        )
                    source_ids.add(source_id)
                _validate_source(package_root, source, source_path, errors)

        _validate_references(requirement, requirement_path, requirement_label, artifact_corpus, errors)
        _validate_coverage(requirement, requirement_label, stage, errors)

        pages = requirement.get("prototype_pages")
        if isinstance(pages, list):
            seen_pages: set[str] = set()
            for page_index, page in enumerate(pages):
                if not isinstance(page, str):
                    continue
                page_path = f"{requirement_path}.prototype_pages[{page_index}]"
                if page in seen_pages:
                    errors.append(
                        f"{page_path}: duplicate prototype page {page!r}; remove the repeated path."
                    )
                seen_pages.add(page)
                resolved = _safe_prototype_path(package_root, page)
                if resolved is None:
                    errors.append(
                        f"{page_path}: {page!r} must be a safe package-relative pages/prototype/...html path."
                    )
                elif not resolved.is_file():
                    errors.append(
                        f"{page_path}: prototype page {page!r} does not exist; "
                        "create the HTML page or correct the path."
                    )


def validate_traceability(package_path: str | Path, stage: str) -> list[str]:
    """Return actionable validation errors for a process package and lifecycle stage."""
    if stage not in STAGES:
        raise ValueError(f"Unknown traceability stage {stage!r}; choose one of: {', '.join(STAGES)}")

    package_root = Path(package_path).expanduser()
    if not package_root.is_dir():
        return [f"package: process package does not exist or is not a directory: {package_root}"]

    sidecar_path = package_root / SIDECAR_FILENAME
    if not sidecar_path.is_file():
        return [
            f"{sidecar_path}: sidecar not found; create {SIDECAR_FILENAME} "
            "under the process root using schema version 1.0.0."
        ]

    data, load_error = _load_yaml(sidecar_path)
    if load_error:
        return [load_error]
    if not isinstance(data, dict):
        return [f"{sidecar_path}: top level must be a mapping with schema_version, prd_version, and requirements."]

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft7Validator(schema)
    errors = [
        f"{_json_path(list(error.absolute_path))}: {error.message}; fix the sidecar to match {SCHEMA_PATH.name}."
        for error in sorted(
        validator.iter_errors(data),
        key=lambda error: _json_path(list(error.absolute_path)),
    )
    ]
    _validate_semantics(package_root, data, sidecar_path, stage, errors)
    return errors


# Explicit package-oriented alias for the integration slice.
validate_package = validate_traceability


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate Lincoln PRD traceability by lifecycle stage")
    parser.add_argument("--package", required=True, type=Path, help="Process package root or slug path")
    parser.add_argument("--stage", required=True, choices=STAGES, help="Lifecycle completeness level")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    errors = validate_traceability(args.package, args.stage)
    if errors:
        print(f"FAIL: {args.package} failed {args.stage} PRD traceability validation ({len(errors)} errors)")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PASS: {args.package} satisfies {args.stage} PRD traceability validation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
