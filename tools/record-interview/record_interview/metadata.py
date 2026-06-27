from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _metadata_path(workspace_root: Path, session_id: str) -> Path:
    return workspace_root / "interviews" / session_id / "metadata.json"


def build_metadata(
    workspace_root: Path,
    session_id: str,
    design_id: str | None,
    topic: str | None,
    branch: str | None,
) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "design_id": design_id,
        "topic": topic,
        "branch": branch,
        "recording_file": f"recordings/{session_id}.m4a",
        "started_at": now_iso(),
        "ended_at": None,
        "duration_seconds": None,
        "source": "lincoln-record-interview-cli",
        "created_by": "lincoln-record-interview-cli",
    }


def read_metadata(workspace_root: Path, session_id: str) -> dict[str, Any] | None:
    path = _metadata_path(workspace_root, session_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_metadata(workspace_root: Path, session_id: str, metadata: dict[str, Any]) -> None:
    path = _metadata_path(workspace_root, session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


def update_recording_complete(
    workspace_root: Path,
    session_id: str,
    duration_seconds: int,
) -> dict[str, Any]:
    metadata = read_metadata(workspace_root, session_id)
    if metadata is None:
        raise FileNotFoundError(f"metadata not found for {session_id}")
    metadata["ended_at"] = now_iso()
    metadata["duration_seconds"] = duration_seconds
    write_metadata(workspace_root, session_id, metadata)
    return metadata
