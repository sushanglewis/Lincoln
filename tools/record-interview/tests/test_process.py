import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from record_interview.process import ProcessInterviewError, trigger_process_interview


@patch("record_interview.process.subprocess.run")
@patch("record_interview.process.shutil.which", return_value="/usr/local/bin/claude")
def test_trigger_process_interview(mock_which, mock_run):
    mock_run.return_value = MagicMock(returncode=0, stderr="")
    trigger_process_interview(Path("/workspace"), "2026-06-27-stakeholder")
    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "claude"
    assert cmd[1] == "process-interview"
    assert cmd[2] == "2026-06-27-stakeholder"
    assert mock_run.call_args.kwargs["cwd"] == Path("/workspace")


@patch("record_interview.process.shutil.which", return_value=None)
def test_trigger_process_interview_claude_not_found(mock_which):
    with pytest.raises(ProcessInterviewError, match="claude CLI not found in PATH"):
        trigger_process_interview(Path("/workspace"), "2026-06-27-stakeholder")


@patch("record_interview.process.subprocess.run")
@patch("record_interview.process.shutil.which", return_value="/usr/local/bin/claude")
def test_trigger_process_interview_raises_on_failure(mock_which, mock_run):
    mock_run.return_value = MagicMock(returncode=1, stderr="claude failed")
    with pytest.raises(ProcessInterviewError, match="failed with code 1"):
        trigger_process_interview(Path("/workspace"), "2026-06-27-stakeholder")


@patch(
    "record_interview.process.subprocess.run",
    side_effect=subprocess.TimeoutExpired(cmd=["claude"], timeout=300),
)
@patch("record_interview.process.shutil.which", return_value="/usr/local/bin/claude")
def test_trigger_process_interview_raises_on_timeout(mock_which, mock_run):
    with pytest.raises(ProcessInterviewError, match="timed out"):
        trigger_process_interview(Path("/workspace"), "2026-06-27-stakeholder")


@patch(
    "record_interview.process.subprocess.run",
    side_effect=OSError("permission denied"),
)
@patch("record_interview.process.shutil.which", return_value="/usr/local/bin/claude")
def test_trigger_process_interview_raises_on_oserror(mock_which, mock_run):
    with pytest.raises(ProcessInterviewError, match="failed to run"):
        trigger_process_interview(Path("/workspace"), "2026-06-27-stakeholder")
