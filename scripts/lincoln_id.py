#!/usr/bin/env python3
"""One-id index manager for Lincoln issue packages.

Provides stable, machine-readable identifiers for PRD themes, features, user
stories, data models, APIs, flows, fields, and pages. Agents can query by ID
instead of reading whole documents.

Examples:
    python scripts/lincoln_id.py lookup page/checkout-cart
    python scripts/lincoln_id.py list --type page
    python scripts/lincoln_id.py related feature/checkout-redesign
    python scripts/lincoln_id.py create page/checkout-cart \
        --title "购物车" \
        --path "pages/prototype/web/checkout-cart/page.html" \
        --feature feature/checkout-redesign
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import yaml

from scripts.lincoln_paths import (
    PROJECT_ROOT as _PROJECT_ROOT,
    get_process_slug,
    load_yaml,
    resolve_state_path,
)

ONE_ID_DIR = ".lincoln/one-id"

ID_RE = re.compile(r"^(doc|feature|story|model|api|flow|field|page)/[a-z0-9][a-z0-9-]*$")

TYPE_TO_FILE = {
    "doc": "docs.yaml",
    "feature": "features.yaml",
    "story": "stories.yaml",
    "model": "models.yaml",
    "api": "apis.yaml",
    "flow": "flows.yaml",
    "field": "fields.yaml",
    "page": "pages.yaml",
}

FILE_TO_TYPE = {v: k for k, v in TYPE_TO_FILE.items()}


def _load_state() -> dict[str, Any] | None:
    state_path = resolve_state_path(None, PROJECT_ROOT)
    if not state_path.exists():
        return None
    try:
        return load_yaml(state_path)
    except Exception:
        return None


def _process_slug() -> str:
    state = _load_state()
    state_path = resolve_state_path(None, PROJECT_ROOT)
    return get_process_slug(state, state_path)


def _one_id_dir() -> Path:
    return PROJECT_ROOT / _process_slug() / ONE_ID_DIR


def _index_path(id_type: str) -> Path:
    filename = TYPE_TO_FILE[id_type]
    path = _one_id_dir() / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _load_index(id_type: str) -> dict[str, Any]:
    path = _index_path(id_type)
    if not path.exists():
        return {}
    try:
        data = load_yaml(path)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_index(id_type: str, data: dict[str, Any]) -> None:
    path = _index_path(id_type)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=True), encoding="utf-8")


def _split_id(full_id: str) -> tuple[str, str]:
    if "/" not in full_id:
        raise ValueError(f"Invalid ID (must contain '/'): {full_id}")
    id_type, name = full_id.split("/", 1)
    if id_type not in TYPE_TO_FILE:
        raise ValueError(f"Unknown ID type '{id_type}': {full_id}")
    if not ID_RE.match(full_id):
        raise ValueError(f"Invalid ID format: {full_id}")
    return id_type, name


def _pretty_print(data: Any, indent: int = 0) -> None:
    prefix = "  " * indent
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                print(f"{prefix}{key}:")
                _pretty_print(value, indent + 1)
            else:
                print(f"{prefix}{key}: {value}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                print(f"{prefix}-")
                _pretty_print(item, indent + 1)
            else:
                print(f"{prefix}- {item}")
    else:
        print(f"{prefix}{data}")


def cmd_lookup(full_id: str) -> int:
    """Print the complete entry for an ID, searching across all index files."""
    try:
        id_type, name = _split_id(full_id)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    index = _load_index(id_type)
    entry = index.get(full_id)
    if entry is None:
        print(f"NOT FOUND: {full_id}")
        return 1

    print(f"{full_id}:")
    _pretty_print(entry, indent=1)
    return 0


def cmd_list(id_type: str | None) -> int:
    """List all IDs, optionally filtered by type."""
    if id_type:
        if id_type not in TYPE_TO_FILE:
            print(f"ERROR: unknown type '{id_type}'", file=sys.stderr)
            return 1
        types = [id_type]
    else:
        types = list(TYPE_TO_FILE.keys())

    found = False
    for t in types:
        index = _load_index(t)
        for full_id in sorted(index):
            print(full_id)
            found = True
    if not found:
        print("No IDs indexed yet.")
    return 0


def _collect_related(
    full_id: str,
    visited: set[str],
    collected: dict[str, list[dict[str, Any]]],
) -> None:
    """Recursively collect entries related to *full_id* via cross-reference fields."""
    if full_id in visited:
        return
    visited.add(full_id)

    try:
        id_type, _ = _split_id(full_id)
    except ValueError:
        return

    index = _load_index(id_type)
    entry = index.get(full_id)
    if entry is None:
        return

    collected.setdefault(id_type, []).append({full_id: entry})

    relation_fields = (
        "source",
        "pages",
        "flows",
        "stories",
        "fields",
        "apis",
        "models",
        "features",
        "docs",
    )
    for field in relation_fields:
        value = entry.get(field)
        if not value:
            continue
        refs = value if isinstance(value, list) else [value]
        for ref in refs:
            ref_id = str(ref).split("#")[0]
            if "/" not in ref_id:
                continue
            try:
                _split_id(ref_id)
            except ValueError:
                continue
            _collect_related(ref_id, visited, collected)


def cmd_related(full_id: str) -> int:
    """Print all entries reachable from *full_id* through cross-references."""
    try:
        _split_id(full_id)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    collected: dict[str, list[dict[str, Any]]] = {}
    _collect_related(full_id, set(), collected)

    if not collected:
        print(f"No related entries found for {full_id}")
        return 0

    for id_type in sorted(collected):
        print(f"## {id_type}")
        for item in collected[id_type]:
            for key, value in item.items():
                print(f"{key}:")
                _pretty_print(value, indent=1)
        print()
    return 0


def cmd_create(
    full_id: str,
    title: str | None,
    path: str | None,
    source: str | None,
    relations: list[str],
) -> int:
    """Create or update a one-id entry."""
    try:
        id_type, name = _split_id(full_id)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    index = _load_index(id_type)
    entry: dict[str, Any] = index.get(full_id, {})

    if title:
        entry["title"] = title
    if path:
        entry["path"] = path
    if source:
        entry["source"] = source

    # Relations are stored as simple list values under the inferred type key.
    for relation in relations:
        try:
            rel_type, _ = _split_id(relation)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        plural = rel_type + "s"
        existing = entry.setdefault(plural, [])
        if relation not in existing:
            existing.append(relation)

    index[full_id] = entry
    _save_index(id_type, index)
    print(f"Created/updated {full_id}")
    return 0


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lincoln one-id index manager")
    subparsers = parser.add_subparsers(dest="command", required=True)

    lookup_parser = subparsers.add_parser("lookup", help="Look up an ID across all indexes")
    lookup_parser.add_argument("id", help="Full ID (e.g. page/checkout-cart)")

    list_parser = subparsers.add_parser("list", help="List indexed IDs")
    list_parser.add_argument("--type", help=f"Filter by type ({', '.join(TYPE_TO_FILE)})")

    related_parser = subparsers.add_parser("related", help="Show entries related to an ID")
    related_parser.add_argument("id", help="Full ID (e.g. feature/checkout-redesign)")

    create_parser = subparsers.add_parser("create", help="Create or update an ID entry")
    create_parser.add_argument("id", help="Full ID (e.g. page/checkout-cart)")
    create_parser.add_argument("--title", help="Human-readable title")
    create_parser.add_argument("--path", help="Artifact path (repo-relative)")
    create_parser.add_argument("--source", help="Source document ID or URL fragment")
    create_parser.add_argument(
        "--relation",
        action="append",
        default=[],
        help="Related full ID (can be repeated)",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_argument_parser()
    args = parser.parse_args(argv)

    if args.command == "lookup":
        return cmd_lookup(args.id)
    if args.command == "list":
        return cmd_list(args.type)
    if args.command == "related":
        return cmd_related(args.id)
    if args.command == "create":
        return cmd_create(args.id, args.title, args.path, args.source, args.relation)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
