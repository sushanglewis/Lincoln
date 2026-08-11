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

from scripts.lincoln_index import VERSION_COMMENT_RE
from scripts.lincoln_paths import (
    atomic_write_text,
    get_process_slug,
    load_yaml,
    process_package_root,
    resolve_state_path,
)


def extract_prd_version(prd_path: Path) -> str | None:
    """Return the version marker from an HTML PRD or a legacy Markdown PRD."""
    if not prd_path.exists():
        return None
    text = prd_path.read_text(encoding="utf-8")
    match = VERSION_COMMENT_RE.search(text)
    return match.group(1) if match else None


# Backwards-compatible alias used by early tests.
extract_version = extract_prd_version

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


def _prd_path(root: Path) -> Path:
    """Return the primary HTML PRD path, falling back to legacy root prd.md."""
    html_path = root / "pages" / "docs" / "prd.html"
    if html_path.exists():
        return html_path
    legacy_path = root / "prd.md"
    if legacy_path.exists():
        return legacy_path
    return html_path


def _snapshot_path(prd_path: Path, version: str) -> Path:
    """Return the immutable snapshot path next to the PRD source."""
    if prd_path.name == "prd.html":
        return prd_path.parent / "snapshots" / f"prd-{version}.html"
    return prd_path.with_name(f"prd-{version}.md")


def freeze(package_root: Path | None = None, *, args: argparse.Namespace | None = None) -> Path:
    """Copy the PRD to an immutable versioned snapshot based on its version marker."""
    root = package_root or (args and _package_root(args))
    if not root:
        _error("package_root is required")
    prd_path = _prd_path(root)
    if not prd_path.exists():
        _error(f"PRD not found: {prd_path}")

    version = extract_prd_version(prd_path)
    if not version:
        _error(f"No version marker found in {prd_path}; add '<!-- version: vX.Y -->' before freezing.")

    snapshot_path = _snapshot_path(prd_path, version)
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    if snapshot_path.exists():
        _error(
            f"Snapshot already exists: {snapshot_path}. "
            "PRD snapshots are protected by an immutability guarantee. "
            "Bump the version marker in the PRD and freeze again."
        )

    atomic_write_text(snapshot_path, prd_path.read_text(encoding="utf-8"))
    print(f"Frozen {snapshot_path}")
    return snapshot_path


def current_version(package_root: Path | None = None, *, args: argparse.Namespace | None = None) -> str:
    """Print the version marker from the PRD."""
    root = package_root or (args and _package_root(args))
    if not root:
        _error("package_root is required")
    prd_path = _prd_path(root)
    if not prd_path.exists():
        _error(f"PRD not found: {prd_path}")

    version = extract_prd_version(prd_path)
    if not version:
        _error(f"No version marker found in {prd_path}.")

    print(version)
    return version


def _render_prd_html(title: str, version: str, markdown: str, package_root: Path) -> str:
    """Wrap legacy Markdown PRD content in the page-doc HTML template."""
    from scripts import lincoln_render

    return lincoln_render.render_page(
        stage_id="clarify",
        target="{process_slug}/pages/docs/prd.html",
        title=title,
        nav_label=title,
        nav_group="Docs",
        version=version,
        uid="prd",
        stage_mark="clarify",
        markdown_source=markdown,
        extra_variables={"process_slug": package_root.name},
    )


def migrate(
    package_root: Path | None = None,
    session_id: str | None = None,
    *,
    args: argparse.Namespace | None = None,
) -> Path:
    """Move a legacy requirements/{session_id}/prd.md into the HTML portal."""
    root = package_root or (args and _package_root(args))
    if not root:
        _error("package_root is required")

    sid = session_id or (args and args.session_id)
    if not sid:
        _error("--session-id is required for migrate")

    legacy_path = root / "requirements" / sid / "prd.md"
    if not legacy_path.exists():
        _error(f"Legacy PRD not found: {legacy_path}")

    target_path = root / "pages" / "docs" / "prd.html"
    if target_path.exists():
        _error(f"Root PRD already exists: {target_path}. Manual merge required.")

    content = legacy_path.read_text(encoding="utf-8")
    version = extract_prd_version(legacy_path)
    if not version:
        version = "v1.0"
        content = f"<!-- version: {version} -->\n\n" + content.lstrip("\n")
    else:
        # Avoid duplicating the version marker once the template injects it.
        content = VERSION_COMMENT_RE.sub("", content, count=1).strip("\n")

    html = _render_prd_html("PRD", version, content, root)

    target_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(target_path, html)
    legacy_path.unlink()
    print(f"Migrated {legacy_path} -> {target_path}")
    return target_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Lincoln PRD lifecycle helper")
    parser.add_argument("--package", help="Process package slug (e.g., issue-85)")
    parser.add_argument("--session-id", help="Interview session id (required for migrate)")
    subparsers = parser.add_subparsers(dest="action", required=True)

    subparsers.add_parser("freeze", help="Freeze pages/docs/prd.html into an immutable versioned snapshot")
    subparsers.add_parser("current-version", help="Print the current PRD version marker")
    migrate_parser = subparsers.add_parser("migrate", help="Move legacy requirements/{session_id}/prd.md into pages/docs/prd.html")
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
