from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


from record_interview.summarizer import CLAUDE_CLI_TIMEOUT_SECONDS


class ProcessInterviewError(Exception):
    pass


def trigger_process_interview(workspace_root: Path, session_id: str) -> None:
    if not shutil.which("claude"):
        raise ProcessInterviewError("claude CLI not found in PATH")

    cmd = ["claude", "process-interview", session_id]
    try:
        result = subprocess.run(
            cmd,
            cwd=workspace_root,
            capture_output=True,
            text=True,
            timeout=CLAUDE_CLI_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as e:
        raise ProcessInterviewError(
            f"claude process-interview timed out after {CLAUDE_CLI_TIMEOUT_SECONDS} seconds"
        ) from e
    except OSError as e:
        raise ProcessInterviewError(f"failed to run claude process-interview: {e}") from e
    if result.returncode != 0:
        raise ProcessInterviewError(
            f"claude process-interview failed with code {result.returncode}"
        )
