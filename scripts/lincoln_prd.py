#!/usr/bin/env python3
"""PRD lifecycle helper: freeze snapshots, read current version, migrate legacy paths."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lincoln_documents import extract_markdown_version
from scripts.lincoln_paths import (
    atomic_write_text,
    get_process_slug,
    load_yaml,
    process_package_root,
    resolve_state_path,
)

# Backwards-compatible alias used by early tests.
extract_version = extract_markdown_version

VERSION_MARKER_RE = re.compile(r"\n?\s*\n?\Z", re.MULTILINE)


def _error(message: str) -> None:
    raise RuntimeError(message)


def _package_root(args: argparse.Namespace) -> Path:
    if args.package:
        return PROJECT_ROOT / args.package

    env_slug = os.environ.get("LINCOLN_PROCESS_SLUG")
    if env_slug:
        root = PROJECT_ROOT / env_slug
        if root.exists():
            return root
        cwd_root = Path.cwd() / env_slug
        if cwd_root.exists():
            return cwd_root
        return cwd_root

    state_path = resolve_state_path(None, PROJECT_ROOT)
    if state_path is not None and state_path.parent.exists():
        try:
            if state_path.exists():
                state = load_yaml(state_path)
                return process_package_root(
                    state=state, state_path=state_path, project_root=PROJECT_ROOT
                )
            return state_path.parent
        except Exception:
            pass

    _error(
        "Could not determine package root. "
        "Use --package or run from a Lincoln project with a state file."
    )


def freeze(package_root: Path | None = None, *, args: argparse.Namespace | None = None) -> Path:
    """Copy prd.md to an immutable prd-v{X}.{Y}.md snapshot based on its version marker."""
    root = package_root or (args and _package_root(args))
    if not root:
        _error("package_root is required")
    prd_path = root / "prd.md"
    if not prd_path.exists():
        _error(f"prd.md not found: {prd_path}")

    version = extract_markdown_version(prd_path)
    if not version:
        _error(f"No version marker found in {prd_path}; add '<!-- version: vX.Y -->' before freezing.")

    snapshot_path = root / f"prd-{version}.md"
    if snapshot_path.exists():
        _error(
            f"Snapshot already exists: {snapshot_path}. "
            "PRD snapshots are protected by an immutability guarantee. "
            "Bump the version marker in prd.md and freeze again."
        )

    atomic_write_text(snapshot_path, prd_path.read_text(encoding="utf-8"))
    print(f"Frozen {snapshot_path}")
    return snapshot_path


def current_version(package_root: Path | None = None, *, args: argparse.Namespace | None = None) -> str:
    """Print the version marker from prd.md."""
    root = package_root or (args and _package_root(args))
    if not root:
        _error("package_root is required")
    prd_path = root / "prd.md"
    if not prd_path.exists():
        _error(f"prd.md not found: {prd_path}")

    version = extract_markdown_version(prd_path)
    if not version:
        _error(f"No version marker found in {prd_path}.")

    print(version)
    return version


def migrate(
    package_root: Path | None = None,
    session_id: str | None = None,
    *,
    args: argparse.Namespace | None = None,
) -> Path:
    """Move a legacy requirements/{session_id}/prd.md to the issue-package root."""
    root = package_root or (args and _package_root(args))
    if not root:
        _error("package_root is required")

    sid = session_id or (args and args.session_id)
    if not sid:
        _error("--session-id is required for migrate")

    legacy_path = root / "requirements" / sid / "prd.md"
    if not legacy_path.exists():
        _error(f"Legacy PRD not found: {legacy_path}")

    target_path = root / "prd.md"
    if target_path.exists():
        _error(f"Root PRD already exists: {target_path}. Manual merge required.")

    content = legacy_path.read_text(encoding="utf-8")
    if not extract_markdown_version(legacy_path):
        # Inject a v1.0 marker at the top if the legacy file lacks one.
        marker = "<!-- version: v1.0 -->\n\n"
        content = marker + content.lstrip("\n")

    atomic_write_text(target_path, content)
    legacy_path.unlink()
    print(f"Migrated {legacy_path} -> {target_path}")
    return target_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Lincoln PRD lifecycle helper")
    parser.add_argument("--package", help="Process package slug (e.g., issue-85)")
    parser.add_argument("--session-id", help="Interview session id (required for migrate)")
    subparsers = parser.add_subparsers(dest="action", required=True)

    subparsers.add_parser("freeze", help="Freeze prd.md into an immutable versioned snapshot")
    subparsers.add_parser("current-version", help="Print the current prd.md version marker")
    migrate_parser = subparsers.add_parser("migrate", help="Move legacy requirements/{session_id}/prd.md to root")
    migrate_parser.add_argument("--session-id", required=True, help="Legacy session directory name")

    args = parser.parse_args()

    try:
        if args.action == "freeze":
            freeze(args=args)
        elif args.action == "current-version":
            current_version(args=args)
        elif args.action == "migrate":
            migrate(args=args)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
