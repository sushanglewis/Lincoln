#!/usr/bin/env python3
"""Validate business-complete, Axure-style prototype review annotations."""

from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from typing import Any

REQUIRED_STATE_KINDS = ("default", "loading", "empty", "success", "error")
ANNOTATION_SECTIONS = ("overview", "sections", "interactions", "states", "exceptions", "data")
TECHNICAL_NARRATIVE_RE = re.compile(
    r"\b(?:API|HTTP|JSON|CSS|HTML|Token|Webhook|Redis)\b|data-uid|数据库|状态码|接口返回|\b[45]\d{2}\b",
    re.IGNORECASE,
)
TARGET_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")


class _PageDataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.inside = False
        self.chunks: list[str] = []
        self.blocks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "script" and dict(attrs).get("id") == "pageData":
            self.inside = True
            self.chunks = []

    def handle_data(self, data: str) -> None:
        if self.inside:
            self.chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self.inside:
            self.blocks.append("".join(self.chunks))
            self.inside = False


def _page_data(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    parser = _PageDataParser()
    try:
        parser.feed(path.read_text(encoding="utf-8"))
        parser.close()
    except (OSError, UnicodeError) as exc:
        return None, f"PAGE_READ_ERROR: {path}: {exc}"
    if len(parser.blocks) != 1:
        return None, f"PAGE_DATA_ERROR: {path}: expected one script#pageData block"
    try:
        data = json.loads(parser.blocks[0])
    except json.JSONDecodeError as exc:
        return None, f"PAGE_DATA_ERROR: {path}: invalid JSON at line {exc.lineno}: {exc.msg}"
    if not isinstance(data, dict):
        return None, f"PAGE_DATA_ERROR: {path}: pageData must be an object"
    return data, None


def _missing_text(value: Any) -> bool:
    return not isinstance(value, str) or not value.strip()


def _check_fields(item: Any, fields: tuple[str, ...], code: str, errors: list[str]) -> None:
    if not isinstance(item, dict):
        errors.append(f"{code}: entry must be an object")
        return
    for field in fields:
        if _missing_text(item.get(field)):
            errors.append(f"{code}: {field}")


def _target_exists(source: str, target: str) -> bool:
    normalized = source.replace('\\"', '"').replace("\\'", "'")
    return any(
        marker in normalized
        for marker in (
            f'data-uid="{target}"',
            f"data-uid='{target}'",
            f'id="{target}"',
            f"id='{target}'",
        )
    )


def _validate_target(source: str, target: Any, errors: list[str]) -> None:
    if not isinstance(target, str) or not target.strip() or not TARGET_RE.fullmatch(target):
        errors.append(f"ANNOTATION_TARGET_INVALID: {target!r}; use a stable data-uid")
        return
    if not _target_exists(source, target):
        errors.append(f"ANNOTATION_TARGET_MISSING: {target}")


def _validate_narrative(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"target", "page", "flow", "kind", "not_applicable"}:
                continue
            _validate_narrative(child, f"{path}.{key}" if path else key, errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_narrative(child, f"{path}[{index}]", errors)
    elif isinstance(value, str):
        match = TECHNICAL_NARRATIVE_RE.search(value)
        if match:
            errors.append(
                f"TECHNICAL_NARRATIVE: {path}: replace {match.group(0)!r} with user-visible business language"
            )


def _validate_states(root: Path, states: Any, errors: list[str]) -> set[str]:
    if not isinstance(states, list):
        return set()
    by_kind: dict[str, Any] = {}
    for state in states:
        if not isinstance(state, dict) or _missing_text(state.get("kind")):
            errors.append("STATE_FIELD: kind")
            continue
        kind = state["kind"]
        if kind in by_kind:
            errors.append(f"STATE_DUPLICATE: {kind}")
        by_kind[kind] = state
        if state.get("not_applicable") is True:
            if _missing_text(state.get("reason")):
                errors.append(f"STATE_NA_REASON: {kind}")
            continue
        _check_fields(state, ("name", "when", "data", "feedback", "recovery", "page"), "STATE_FIELD", errors)
        page = state.get("page")
        if not _missing_text(page):
            candidate = PurePosixPath(page)
            if candidate.is_absolute() or ".." in candidate.parts or candidate.parts[:2] != ("pages", "prototype"):
                errors.append(f"STATE_PAGE_INVALID: {page}")
            elif not (root / candidate).is_file():
                errors.append(f"STATE_PAGE_MISSING: {page}")
    for kind in REQUIRED_STATE_KINDS:
        if kind not in by_kind:
            errors.append(f"STATE_MISSING: {kind}")
    return {kind for kind, state in by_kind.items() if state.get("not_applicable") is not True}


def _validate_page(root: Path, page: Path) -> list[str]:
    data, error = _page_data(page)
    if error:
        return [error]
    assert data is not None
    annotations = data.get("annotations")
    if annotations is None:
        return [f"ANNOTATIONS_MISSING: {page.relative_to(root).as_posix()}"]
    if not isinstance(annotations, dict):
        return [f"ANNOTATIONS_INVALID: {page.relative_to(root).as_posix()} must be an object"]

    errors: list[str] = []
    for section in ANNOTATION_SECTIONS:
        if section not in annotations:
            errors.append(f"ANNOTATIONS_SECTION_MISSING: {section}")
    source = page.read_text(encoding="utf-8")

    overview = annotations.get("overview")
    _check_fields(
        overview,
        ("role", "scenario", "goal", "entry", "completion", "current_state", "flow"),
        "OVERVIEW_FIELD",
        errors,
    )
    if isinstance(overview, dict):
        covered_states = _validate_states(root, annotations.get("states"), errors)
        current_state = overview.get("current_state")
        if isinstance(current_state, str) and current_state not in covered_states:
            errors.append(f"CURRENT_STATE_UNKNOWN: {current_state}")
    else:
        _validate_states(root, annotations.get("states"), errors)

    sections = annotations.get("sections")
    if not isinstance(sections, list) or not sections:
        errors.append("SECTIONS_EMPTY: describe the page structure at least once")
        sections = []
    for section in sections:
        _check_fields(section, ("title", "purpose", "content"), "SECTION_FIELD", errors)
        if isinstance(section, dict):
            _validate_target(source, section.get("target"), errors)

    interactions = annotations.get("interactions")
    if not isinstance(interactions, list) or not interactions:
        errors.append("INTERACTIONS_EMPTY: describe at least one user action and system response")
        interactions = []
    for interaction in interactions:
        _check_fields(interaction, ("name", "trigger", "response", "rule", "next"), "INTERACTION_FIELD", errors)
        if isinstance(interaction, dict):
            _validate_target(source, interaction.get("target"), errors)

    exceptions = annotations.get("exceptions")
    if not isinstance(exceptions, list) or not exceptions:
        errors.append("EXCEPTIONS_EMPTY: describe at least one failure and its recovery path")
        exceptions = []
    for exception in exceptions:
        _check_fields(exception, ("name", "trigger", "feedback", "recovery"), "EXCEPTION_FIELD", errors)
        if isinstance(exception, dict):
            _validate_target(source, exception.get("target"), errors)

    data_items = annotations.get("data")
    if not isinstance(data_items, list) or not data_items:
        if _missing_text(annotations.get("data_not_applicable")):
            errors.append("DATA_EMPTY: describe page data or set data_not_applicable with a business reason")
        data_items = []
    for item in data_items:
        _check_fields(item, ("name", "meaning", "values", "empty", "validation", "source"), "DATA_FIELD", errors)

    _validate_narrative(annotations, "annotations", errors)
    relative = page.relative_to(root).as_posix()
    return [f"{error}: {relative}" for error in errors]


def validate_annotations(process_root: str | Path) -> list[str]:
    """Return all annotation contract failures across a prototype package."""
    root = Path(process_root)
    if not root.is_dir():
        return [f"PROCESS_ROOT_MISSING: {root}"]
    prototype_root = root / "pages" / "prototype"
    pages = sorted(prototype_root.rglob("*.html")) if prototype_root.is_dir() else []
    if not pages:
        return [f"PROTOTYPE_EMPTY: no HTML pages under {prototype_root}"]
    errors: list[str] = []
    for page in pages:
        errors.extend(_validate_page(root, page))
    return sorted(dict.fromkeys(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("process_root", type=Path, help="Issue package root containing pages/prototype/")
    args = parser.parse_args(argv)
    errors = validate_annotations(args.process_root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"Prototype annotations failed with {len(errors)} error(s).", file=sys.stderr)
        return 1
    print(f"Prototype annotations OK: {args.process_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
