#!/usr/bin/env python3
"""Maintain the per-package HTML portal index.

Generates {process_slug}/assets/js/package-data.js from workflow-stage.yaml and a
scan of {process_slug}/pages/**/*.html. The portal's index.html loads this file
and renders navigation, status, and annotations.

Replaces the older documents.yaml index; machine state stays in
workflow-stage.yaml, while package-data.js is a generated projection for humans.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.lincoln_paths import STATE_FILENAME, is_process_state_path

PACKAGE_DATA_FILENAME = "assets/js/package-data.js"
VERSION_COMMENT_RE = re.compile(r"<!--\s*version:\s*(v\d+\.\d+)\s*-->", re.IGNORECASE)
STATUS_COMMENT_RE = re.compile(r"<!--\s*status:\s*(\w+)\s*-->", re.IGNORECASE)
LIST_META_KEYS = ("doc-fields", "doc-stories", "doc-rules", "doc-boundaries", "doc-exceptions", "doc-refs")
LIST_SEPARATOR = "|"


class MetaParser(HTMLParser):
    """Collect <meta name="..." content="..."> tags and the <title>."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.meta: dict[str, str] = {}
        self.title: str = ""
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "meta":
            attr_dict = {k: v or "" for k, v in attrs}
            name = attr_dict.get("name", "").strip()
            content = attr_dict.get("content", "").strip()
            if name:
                self.meta[name] = content
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def package_relative(path: str, process_slug: str) -> str:
    """Strip the '<process_slug>/' prefix from a repo-relative artifact path."""
    prefix = f"{process_slug}/"
    return path[len(prefix) :] if path.startswith(prefix) else path


def split_list_meta(value: str) -> list[str]:
    """Split a pipe-separated meta value into a list of trimmed non-empty items."""
    if not value:
        return []
    return [item.strip() for item in value.split(LIST_SEPARATOR) if item.strip()]


def extract_html_meta(full_path: Path) -> dict[str, Any]:
    """Parse meta tags and version/status comments from an HTML page."""
    if not full_path.exists():
        return {}
    text = full_path.read_text(encoding="utf-8")
    parser = MetaParser()
    try:
        parser.feed(text)
    except Exception:
        pass

    version_match = VERSION_COMMENT_RE.search(text)
    status_match = STATUS_COMMENT_RE.search(text)
    meta = {
        "title": parser.meta.get("doc-title") or parser.title or full_path.stem,
        "nav_label": parser.meta.get("nav-label", ""),
        "nav_group": parser.meta.get("nav-group", "Docs"),
        "version": parser.meta.get("doc-version") or (version_match.group(1) if version_match else None),
        "status": status_match.group(1) if status_match else "",
        "uid": parser.meta.get("doc-uid") or parser.meta.get("page-uid", ""),
        "purpose": parser.meta.get("doc-purpose", ""),
        "layout": parser.meta.get("doc-layout", ""),
    }
    for key in LIST_META_KEYS:
        field = key.replace("doc-", "")
        meta[field] = split_list_meta(parser.meta.get(key, ""))
    return meta


def extract_html_markdown(full_path: Path) -> str:
    """Return the embedded Markdown source from a Lincoln doc HTML page.

    If the page does not contain a `<script id="docSource" type="text/markdown">`
    block, fall back to the raw file text so that legacy or migrated pages still
    pass content-based validators.
    """
    if not full_path.exists():
        return ""
    text = full_path.read_text(encoding="utf-8")
    match = re.search(
        r'<script(?=\s)([^>]*?\s(?:id="docSource"|type="text/markdown")[^>]*?)>(.*?)</script>',
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if match:
        source = match.group(2)
        return source.strip()
    return text.strip()


def scan_pages(project_root: Path, process_slug: str) -> dict[str, dict[str, Any]]:
    """Return a dict keyed by page path with metadata from each HTML page."""
    pages_dir = project_root / process_slug / "pages"
    found: dict[str, dict[str, Any]] = {}
    if not pages_dir.is_dir():
        return found
    for path in sorted(pages_dir.rglob("*.html")):
        rel = path.relative_to(project_root / process_slug).as_posix()
        found[rel] = extract_html_meta(path)
    return found


def build_package_data(
    state: dict[str, Any],
    process_slug: str,
    generated_at: str | None = None,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Build the portal data object from state and scanned HTML pages."""
    root = project_root or Path(__file__).resolve().parents[1]
    current_run = state.get("current_run", {})

    # Start with scanned pages; merge state node metadata over them.
    page_data = scan_pages(root, process_slug)

    for node in state.get("nodes") or []:
        stage_id = str(node.get("stage_id") or "")
        status = str(node.get("status") or "")
        gate_passed = bool(node.get("gate_passed"))
        approver = node.get("approved_by")
        human_confirmed = bool(approver and str(approver).startswith("human"))

        for artifact in node.get("artifacts") or []:
            rel = package_relative(str(artifact), process_slug)
            if not rel.endswith(".html"):
                continue
            entry = page_data.setdefault(rel, {})
            entry.setdefault("path", rel)
            entry.setdefault("title", entry.get("title", Path(rel).stem))
            entry.setdefault("label", entry.get("title", Path(rel).stem))
            entry.setdefault("group", entry.get("nav_group", "Docs"))
            entry["stage"] = stage_id or entry.get("stage", "")
            entry["status"] = status or entry.get("status", "")
            entry["gate_passed"] = gate_passed or entry.get("gate_passed", False)
            entry["human_confirmed"] = human_confirmed or entry.get("human_confirmed", False)

    # Build nav groups preserving scan order.
    groups: dict[str, list[dict[str, Any]]] = {}
    for rel in sorted(page_data):
        entry = page_data[rel]
        group_name = entry.get("group") or entry.get("nav_group") or "Docs"
        groups.setdefault(group_name, []).append(
            {
                "path": rel,
                "label": entry.get("nav_label") or entry.get("label") or entry.get("title") or Path(rel).stem,
                "title": entry.get("title") or Path(rel).stem,
                "version": entry.get("version"),
                "status": entry.get("status", ""),
                "stage": entry.get("stage", ""),
                "gate_passed": entry.get("gate_passed", False),
                "human_confirmed": entry.get("human_confirmed", False),
                "purpose": entry.get("purpose", ""),
                "layout": entry.get("layout", ""),
                "stories": entry.get("stories", []),
                "fields": entry.get("fields", []),
                "rules": entry.get("rules", []),
                "boundaries": entry.get("boundaries", []),
                "exceptions": entry.get("exceptions", []),
                "refs": entry.get("refs", []),
                "uid": entry.get("uid", ""),
            }
        )

    nav = [{"group": g, "items": items} for g, items in groups.items()]

    return {
        "process_slug": process_slug,
        "issue_number": str(current_run.get("issue_number") or ""),
        "current_stage": str(current_run.get("current_stage") or ""),
        "status": str(current_run.get("status") or ""),
        "generated_at": generated_at or now_iso(),
        "nav": nav,
    }


def write_package_index(
    state: dict[str, Any],
    state_path: Path,
    generated_at: str | None = None,
) -> Path | None:
    """Regenerate package-data.js next to a team package state file."""
    if not is_process_state_path(state_path):
        return None
    project_root = state_path.parents[1]
    process_slug = state_path.parent.name
    data = build_package_data(state, process_slug, generated_at, project_root)

    package_data_dir = state_path.parent / "assets" / "js"
    package_data_dir.mkdir(parents=True, exist_ok=True)
    index_path = package_data_dir / "package-data.js"

    js = "window.LINC_PACKAGE = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n"
    index_path.write_text(js, encoding="utf-8")
    return index_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate the issue-package HTML portal index")
    parser.add_argument("--state-file", required=True, help="Path to the package workflow-stage.yaml")
    args = parser.parse_args()

    state_path = Path(args.state_file).resolve()
    if not state_path.is_file():
        print(f"ERROR: state file not found: {state_path}", file=sys.stderr)
        return 1
    state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    index_path = write_package_index(state, state_path)
    if index_path is None:
        print(f"SKIP: {state_path} is not a team issue-package state file")
        return 0
    print(f"Updated {index_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
