from __future__ import annotations

import argparse
import sys
from pathlib import Path

from record_interview.metadata import build_metadata, update_recording_complete, write_metadata
from record_interview.process import trigger_process_interview
from record_interview.recorder import FfmpegRecorder
from record_interview.validator import resolve_workspace_root, validate_session_id


def _confirm(duration_seconds: int) -> bool:
    minutes, seconds = divmod(duration_seconds, 60)
    prompt = f"Recording duration: {minutes:02d}:{seconds:02d}. Trigger process-interview? [y/N]: "
    try:
        answer = input(prompt).strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False
    return answer in ("y", "yes")


def run_recording_flow(
    workspace_root: Path,
    session_id: str,
    design_id: str | None,
    topic: str | None,
    branch: str | None,
    no_confirm: bool = False,
) -> int:
    recording_path = workspace_root / "recordings" / f"{session_id}.m4a"
    recording_path.parent.mkdir(parents=True, exist_ok=True)

    metadata = build_metadata(session_id, design_id, topic, branch)
    write_metadata(workspace_root, session_id, metadata)
    print(f"Metadata prepared: interviews/{session_id}/metadata.json")

    recorder = FfmpegRecorder()
    print("Recording... Press Enter to stop.")
    recorder.start(recording_path)
    cancelled = False
    duration = 0
    try:
        input()
    except KeyboardInterrupt:
        print("\nRecording cancelled.")
        cancelled = True
    finally:
        duration = recorder.stop()
        print(f"Recording saved: {recording_path}")
        update_recording_complete(workspace_root, session_id, duration)

    if cancelled:
        return 130

    if no_confirm:
        return 0

    if not _confirm(duration):
        print("Cancelled. Recording saved but process-interview was not triggered.")
        return 0

    print("Triggering claude process-interview...")
    trigger_process_interview(workspace_root, session_id)
    print("Done.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Record a Lincoln interview")
    parser.add_argument("session_id", help="Session ID in YYYY-MM-DD-descriptive-name format")
    parser.add_argument("--design-id", help="Design ID")
    parser.add_argument("--topic", help="Interview topic")
    parser.add_argument("--branch", help="Current branch name")
    parser.add_argument("--no-confirm", action="store_true", help="Save recording and exit without confirming process-interview")
    args = parser.parse_args(argv)

    try:
        session_id = validate_session_id(args.session_id)
        workspace_root = resolve_workspace_root()
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    try:
        return run_recording_flow(
            workspace_root=workspace_root,
            session_id=session_id,
            design_id=args.design_id,
            topic=args.topic,
            branch=args.branch,
            no_confirm=args.no_confirm,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
