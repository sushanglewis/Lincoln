from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FORMAT)


def _metadata_path(workspace_root: Path, session_id: str) -> Path:
    return workspace_root / "interviews" / session_id / "metadata.json"


def build_metadata(
    session_id: str,
    design_id: str | None,
    topic: str | None,
    branch: str | None,
    started_at: str | None = None,
    transcription_model: str | None = None,
    diarization_model: str | None = None,
    summarization_model: str | None = None,
) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "design_id": design_id,
        "topic": topic,
        "branch": branch,
        "recording_file": f"recordings/{session_id}.m4a",
        "started_at": started_at or now_iso(),
        "ended_at": None,
        "duration_seconds": None,
        "source": "lincoln-record-interview-cli",
        "created_by": "lincoln-record-interview-cli",
        "phased_summaries": [],
        "transcription_model": transcription_model,
        "diarization_model": diarization_model,
        "summarization_model": summarization_model,
    }


def add_phase_summary(
    metadata: dict[str, Any],
    index: int,
    file: str,
    start_time: str,
    end_time: str,
) -> dict[str, Any]:
    summaries = list(metadata.get("phased_summaries", []))
    summaries.append({
        "index": index,
        "file": file,
        "start_time": start_time,
        "end_time": end_time,
    })
    return {**metadata, "phased_summaries": summaries}


def read_metadata(workspace_root: Path, session_id: str) -> dict[str, Any] | None:
    path = _metadata_path(workspace_root, session_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"corrupted metadata for {session_id}: {e}") from e


def write_metadata(workspace_root: Path, session_id: str, data: dict[str, Any]) -> None:
    path = _metadata_path(workspace_root, session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def mark_recording_complete(
    metadata: dict[str, Any],
    duration_seconds: int,
    ended_at: str | None = None,
) -> dict[str, Any]:
    return {**metadata, "ended_at": ended_at or now_iso(), "duration_seconds": duration_seconds}


def update_recording_complete(
    workspace_root: Path,
    session_id: str,
    duration_seconds: int,
) -> dict[str, Any]:
    metadata = read_metadata(workspace_root, session_id)
    if metadata is None:
        raise FileNotFoundError(f"metadata not found for {session_id}")
    updated = mark_recording_complete(metadata, duration_seconds)
    write_metadata(workspace_root, session_id, updated)
    return updated
