from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class WorktreeError(Exception):
    pass


def find_worktree_root(start_path: str | Path | None = None) -> Path:
    """Return the git worktree root for start_path, or raise WorktreeError."""
    if shutil.which("git") is None:
        raise WorktreeError("git not found in PATH")

    cwd = Path(start_path).resolve() if start_path else Path(".").resolve()
    try:
        result = subprocess.run(
            ["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
        raise WorktreeError(f"not inside a git worktree: {e}") from e

    path = Path(result.stdout.strip())
    if not path.exists():
        raise WorktreeError(f"git reported worktree root does not exist: {path}")
    return path


def is_inside_worktree(path: str | Path | None = None) -> bool:
    try:
        find_worktree_root(path)
        return True
    except WorktreeError:
        return False
