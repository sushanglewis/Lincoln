#!/usr/bin/env python3
"""Shared path helpers for Lincoln process packages."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEGACY_STATE_PATH = PROJECT_ROOT / ".claude" / "workflow-state.yaml"
ROOT_STATE_PATH = PROJECT_ROOT / ".claude" / "workflow-stage.yaml"
STATE_FILENAME = "workflow-stage.yaml"
SOLO_STATE_DIR = ".context/workflow"
SOLO_PROCESS_SLUG = ".context"

RESERVED_PROCESS_DIRS = {
    ".claude",
    ".conductor",
    ".context",
    ".git",
    ".github",
    ".pytest_cache",
    ".venv",
    "docs",
    "knowledge",
    "node_modules",
    "oss",
    "products",
    "scripts",
    "tests",
    "tools",
    "venv",
}


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip()).strip("-").lower()
    return slug or "lc-process"


def validate_slug(value: str) -> str:
    slug = slugify(value)
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise ValueError(f"Invalid process slug: {value}")
    return slug


def branch_slug(project_root: Path = PROJECT_ROOT) -> str:
    try:
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"],
            cwd=project_root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        branch = ""
    if branch.startswith("lincoln/"):
        branch = branch.split("/", 1)[1]
    return slugify(branch or project_root.name)


def default_process_slug(project_root: Path = PROJECT_ROOT) -> str:
    """Return a sensible default process package slug for a Conductor workspace."""
    env_slug = os.environ.get("LINCOLN_PROCESS_SLUG") or os.environ.get("CONDUCTOR_WORKSPACE_NAME")
    if env_slug:
        return validate_slug(env_slug)

    # Conductor paths commonly look like .../workspaces/<workspace-slug>/<repo-name>.
    if project_root.parent.name and project_root.parent.parent.name == "workspaces":
        return validate_slug(project_root.parent.name)

    return validate_slug(branch_slug(project_root))


def discover_process_state_paths(project_root: Path = PROJECT_ROOT) -> list[Path]:
    """Find branch process package state files at <process_slug>/workflow-stage.yaml."""
    paths: list[Path] = []
    for candidate in project_root.iterdir():
        if not candidate.is_dir() or candidate.name in RESERVED_PROCESS_DIRS:
            continue
        state_path = candidate / STATE_FILENAME
        if state_path.is_file():
            paths.append(state_path)
    return sorted(paths, key=lambda p: p.stat().st_mtime, reverse=True)


def discover_solo_state_paths(project_root: Path = PROJECT_ROOT) -> list[Path]:
    """Find session-scoped solo workflow instances under .context/workflow/."""
    solo_dir = project_root / SOLO_STATE_DIR
    if not solo_dir.is_dir():
        return []
    paths = [p for p in solo_dir.glob("*.yaml") if p.is_file()]
    return sorted(paths, key=lambda p: p.stat().st_mtime, reverse=True)


def resolve_state_path(path: Path | None = None, project_root: Path = PROJECT_ROOT) -> Path:
    """Resolve canonical process state, falling back to legacy root state files."""
    env_path = os.environ.get("LINCOLN_STATE_FILE")
    if path is None and env_path:
        path = Path(env_path)

    if path is not None:
        path = path if path.is_absolute() else project_root / path
        if path.exists():
            return path
        if path not in (ROOT_STATE_PATH, LEGACY_STATE_PATH):
            return path

    discovered = discover_process_state_paths(project_root)
    if discovered:
        return discovered[0]
    solo = discover_solo_state_paths(project_root)
    if solo:
        return solo[0]
    if ROOT_STATE_PATH.exists():
        return ROOT_STATE_PATH
    if LEGACY_STATE_PATH.exists():
        return LEGACY_STATE_PATH
    return ROOT_STATE_PATH


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def get_process_slug(state: dict[str, Any] | None = None, state_path: Path | None = None) -> str:
    if state:
        variables = state.get("current_run", {}).get("variables", {})
        if variables.get("process_slug"):
            raw = str(variables["process_slug"])
            if raw == SOLO_PROCESS_SLUG:
                return raw
            return validate_slug(raw)
    if state_path and state_path.name == STATE_FILENAME and state_path.parent != PROJECT_ROOT / ".claude":
        return validate_slug(state_path.parent.name)
    return default_process_slug(PROJECT_ROOT)


def interpolate_process_path(path: str, state: dict[str, Any] | None = None, state_path: Path | None = None) -> str:
    return path.replace("{process_slug}", get_process_slug(state, state_path))


def process_package_root(
    process_slug: str | None = None,
    state: dict[str, Any] | None = None,
    state_path: Path | None = None,
    project_root: Path = PROJECT_ROOT,
) -> Path:
    slug = process_slug or get_process_slug(state, state_path)
    if slug == SOLO_PROCESS_SLUG:
        return project_root / SOLO_PROCESS_SLUG
    return project_root / validate_slug(slug)


def is_process_state_path(path: Path, project_root: Path = PROJECT_ROOT) -> bool:
    try:
        rel = path.resolve().relative_to(project_root.resolve())
    except ValueError:
        return False
    return len(rel.parts) == 2 and rel.parts[1] == STATE_FILENAME and rel.parts[0] not in RESERVED_PROCESS_DIRS
