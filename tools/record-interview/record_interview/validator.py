from __future__ import annotations

import re
from pathlib import Path

from record_interview.worktree import WorktreeError, find_worktree_root

SESSION_ID_PATTERN = re.compile(r"^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])-[a-z0-9]+(-[a-z0-9]+)*$")
REQUIRED_DIRS = ("recordings", "interviews", ".claude")


def validate_session_id(session_id: str) -> str:
    if not session_id:
        raise ValueError("session_id is required")
    if not SESSION_ID_PATTERN.match(session_id):
        raise ValueError(
            f"session_id '{session_id}' has invalid format. "
            "Expected: YYYY-MM-DD-descriptive-name (lowercase, hyphens only)"
        )
    return session_id


def _resolve_by_directory_markers(start_path: str | None = None) -> Path:
    path = Path(start_path or ".").resolve()
    for current in [path, *path.parents]:
        if all((current / d).is_dir() for d in REQUIRED_DIRS):
            return current
    raise FileNotFoundError("Lincoln workspace root not found: missing required directories (recordings/, interviews/, .claude/)")


def resolve_workspace_root(start_path: str | None = None) -> Path:
    """Resolve the Lincoln workspace root.

    Prefer the current git worktree root; fall back to looking for the
    recordings/interviews/.claude directory markers.
    """
    try:
        return find_worktree_root(start_path)
    except (WorktreeError, OSError):
        return _resolve_by_directory_markers(start_path)
