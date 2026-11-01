#!/usr/bin/env python3
"""Validate bidirectional traceability between PRD requirements and HTML prototypes."""

from __future__ import annotations

import argparse
import json
import sys
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

METADATA_LIST_FIELDS = ("requirement_ids", "story_ids", "flow_step_ids")
DEFAULT_SIDECAR = "pages/docs/prd-traceability.yaml"


class _PageDataParser(HTMLParser):
    """Collect the contents of script#pageData without executing page scripts."""

    def __init__(self) -> None:
        super().__init__()
        self._inside_page_data = False
        self._chunks: list[str] = []
        self.blocks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "script":
            return
        attributes = dict(attrs)
        if attributes.get("id") == "pageData":
            self._inside_page_data = True
            self._chunks = []

    def handle_data(self, data: str) -> None:
        if self._inside_page_data:
            self._chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._inside_page_data:
            self.blocks.append("".join(self._chunks))
            self._inside_page_data = False
            self._chunks = []


def _string_list(value: Any) -> bool:
    return isinstance(value, list) and all(
        isinstance(item, str) and bool(item.strip()) for item in value
    )


def _metadata_ids(data: dict[str, Any], field: str) -> list[str]:
    value = data.get(field)
    return value if _string_list(value) else []


def _registered_path(value: Any) -> tuple[str | None, str | None]:
    if not isinstance(value, str) or not value.strip():
        return None, "prototype page paths must be non-empty strings"
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        return None, "path must stay relative to the process root"
    if path.parts[:2] != ("pages", "prototype") or path.suffix.lower() != ".html":
        return None, "path must identify an HTML file under pages/prototype/"
    return path.as_posix(), None


def _read_page_data(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    parser = _PageDataParser()
    try:
        parser.feed(path.read_text(encoding="utf-8"))
        parser.close()
    except (OSError, UnicodeError) as exc:
        return None, [f"PAGE_READ_ERROR: {path}: {exc}"]

    if not parser.blocks:
        return None, ["MISSING_PAGE_DATA: expected exactly one script#pageData JSON block"]
    if len(parser.blocks) > 1:
        return None, ["DUPLICATE_PAGE_DATA: expected exactly one script#pageData JSON block"]

    try:
        data = json.loads(parser.blocks[0])
    except json.JSONDecodeError as exc:
        return None, [f"INVALID_PAGE_DATA: invalid JSON at line {exc.lineno}, column {exc.colno}"]
    if not isinstance(data, dict):
        return None, ["INVALID_PAGE_DATA: script#pageData must contain a JSON object"]

    errors: list[str] = []
    for field in METADATA_LIST_FIELDS:
        if field not in data or not _string_list(data[field]):
            errors.append(f"INVALID_METADATA: {field} must be an array of non-empty strings")
    for field in ("requirement_ids", "flow_step_ids"):
        if field in data and _string_list(data[field]) and not data[field]:
            errors.append(f"ORPHAN_PAGE: {field} must contain at least one ID")
    return data, errors


def validate_prototype_traceability(
    process_root: str | Path,
    sidecar_path: str | Path = DEFAULT_SIDECAR,
) -> list[str]:
    """Return actionable errors for prototype/PRD traceability; an empty list passes."""
    root = Path(process_root)
    sidecar = Path(sidecar_path)
    if not sidecar.is_absolute():
        sidecar = root / sidecar

    if not root.is_dir():
        return [f"PROCESS_ROOT_MISSING: {root}"]
    if not sidecar.is_file():
        return [f"SIDECAR_MISSING: {sidecar}"]

    try:
        document = yaml.safe_load(sidecar.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        return [f"SIDECAR_READ_ERROR: {sidecar}: {exc}"]
    if not isinstance(document, dict) or not isinstance(document.get("requirements"), list):
        return ["SIDECAR_INVALID: requirements must be an array"]

    errors: list[str] = []
    requirements: list[dict[str, Any]] = []
    requirement_ids: set[str] = set()
    all_flow_ids: set[str] = set()
    registrations: dict[str, list[str]] = {}

    for index, raw_requirement in enumerate(document["requirements"]):
        if not isinstance(raw_requirement, dict):
            errors.append(f"SIDECAR_INVALID: requirements[{index}] must be an object")
            continue
        requirement_id = raw_requirement.get("id")
        if not isinstance(requirement_id, str) or not requirement_id.strip():
            errors.append(f"SIDECAR_INVALID: requirements[{index}].id must be a non-empty string")
            continue
        if requirement_id in requirement_ids:
            errors.append(f"DUPLICATE_REQUIREMENT_ID: {requirement_id}")
        requirement_ids.add(requirement_id)

        flow_ids = raw_requirement.get("flow_step_ids", [])
        page_values = raw_requirement.get("prototype_pages", [])
        if not _string_list(flow_ids):
            errors.append(f"SIDECAR_INVALID: {requirement_id}.flow_step_ids must be a string array")
            flow_ids = []
        if not isinstance(page_values, list):
            errors.append(f"SIDECAR_INVALID: {requirement_id}.prototype_pages must be an array")
            page_values = []
        all_flow_ids.update(flow_ids)
        is_core = raw_requirement.get("core") is True

        if is_core and not flow_ids:
            errors.append(f"CORE_FLOW_MISSING: core requirement {requirement_id} has no flow_step_ids")
        if is_core and not page_values:
            errors.append(
                f"MISSING_PROTOTYPE_PAGE: core requirement {requirement_id} has no prototype_pages"
            )

        page_paths: list[str] = []
        for raw_path in page_values:
            page_path, path_error = _registered_path(raw_path)
            if path_error:
                errors.append(f"SIDECAR_INVALID: {requirement_id}: {raw_path!r}: {path_error}")
                continue
            assert page_path is not None
            page_paths.append(page_path)
            registrations.setdefault(page_path, []).append(requirement_id)
            if not (root / page_path).is_file():
                errors.append(f"PAGE_FILE_MISSING: {requirement_id} registers missing file {page_path}")

        requirements.append(
            {
                "id": requirement_id,
                "core": is_core,
                "flow_step_ids": flow_ids,
                "prototype_pages": page_paths,
            }
        )

    prototype_root = root / "pages" / "prototype"
    actual_pages = {
        path.relative_to(root).as_posix(): path
        for path in prototype_root.rglob("*.html")
        if path.is_file()
    } if prototype_root.is_dir() else {}

    for page_path in sorted(set(actual_pages) - set(registrations)):
        errors.append(f"ORPHAN_PAGE: actual HTML is not registered in prototype_pages: {page_path}")

    page_data: dict[str, dict[str, Any]] = {}
    for page_path in sorted(set(actual_pages) | set(registrations)):
        path = root / page_path
        if not path.is_file():
            continue
        data, page_errors = _read_page_data(path)
        for error in page_errors:
            errors.append(f"{error}: {page_path}")
        if data is not None:
            page_data[page_path] = data

    for page_path, data in sorted(page_data.items()):
        for requirement_id in _metadata_ids(data, "requirement_ids"):
            if requirement_id not in requirement_ids:
                errors.append(
                    f"BROKEN_REQUIREMENT_LINK: {page_path} references unknown requirement {requirement_id}"
                )
        for flow_id in _metadata_ids(data, "flow_step_ids"):
            if flow_id not in all_flow_ids:
                errors.append(f"BROKEN_FLOW_LINK: {page_path} references unknown flow step {flow_id}")

    for requirement in requirements:
        requirement_id = requirement["id"]
        flow_ids = set(requirement["flow_step_ids"])
        for page_path in requirement["prototype_pages"]:
            data = page_data.get(page_path)
            if data is None:
                continue
            page_requirement_ids = set(_metadata_ids(data, "requirement_ids"))
            page_flow_ids = set(_metadata_ids(data, "flow_step_ids"))
            if requirement_id not in page_requirement_ids:
                errors.append(
                    f"BROKEN_REQUIREMENT_LINK: {page_path} is registered to {requirement_id} "
                    "but does not declare that ID"
                )
            if flow_ids and not (flow_ids & page_flow_ids):
                errors.append(
                    f"BROKEN_FLOW_LINK: {page_path} is registered to {requirement_id} "
                    "but declares none of its flow_step_ids"
                )

        if requirement["core"]:
            for flow_id in requirement["flow_step_ids"]:
                covered = any(
                    requirement_id in _metadata_ids(data, "requirement_ids")
                    and flow_id in _metadata_ids(data, "flow_step_ids")
                    for page_path in requirement["prototype_pages"]
                    for data in [page_data.get(page_path, {})]
                )
                if not covered:
                    errors.append(
                        f"CORE_FLOW_WITHOUT_PAGE: {requirement_id}/{flow_id} has no matching prototype page"
                    )

    return sorted(dict.fromkeys(errors))


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--package",
        "--process-root",
        dest="process_root",
        required=True,
        help="Issue package/process root containing pages/docs/prd-traceability.yaml and pages/prototype/",
    )
    parser.add_argument(
        "--sidecar",
        default=DEFAULT_SIDECAR,
        help="Traceability sidecar path, relative to the process root unless absolute",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    errors = validate_prototype_traceability(args.process_root, args.sidecar)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"Prototype traceability failed with {len(errors)} error(s).", file=sys.stderr)
        return 1
    print(f"Prototype traceability OK: {args.process_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
