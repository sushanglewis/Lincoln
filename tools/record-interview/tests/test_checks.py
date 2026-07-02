import subprocess

from record_interview.checks import (
    _probe_microphone,
    check_diarization,
    check_ffmpeg,
    check_microphone,
    check_summarization,
    check_transcription,
    request_microphone_permission,
    run_setup_checks,
)
from record_interview.config import Config, DiarizationConfig, SummarizationConfig, TranscriptionConfig


def test_check_ffmpeg_true_when_available(mocker):
    mocker.patch("shutil.which", return_value="/usr/bin/ffmpeg")
    ready, message = check_ffmpeg()
    assert ready is True
    assert "ffmpeg" in message


def test_check_ffmpeg_false_when_missing(mocker):
    mocker.patch("shutil.which", return_value=None)
    ready, message = check_ffmpeg()
    assert ready is False
    assert "brew install ffmpeg" in message


def test_check_microphone_detected(mocker):
    mocker.patch(
        "record_interview.checks._probe_microphone",
        return_value=(True, "microphone accessible"),
    )
    ready, message = check_microphone()
    assert ready is True
    assert "accessible" in message


def test_check_microphone_missing(mocker):
    mocker.patch(
        "record_interview.checks._probe_microphone",
        return_value=(False, "failed: no device"),
    )
    ready, message = check_microphone()
    assert ready is False
    assert "no device" in message


def test_check_microphone_cannot_check_without_ffmpeg(mocker):
    mocker.patch(
        "record_interview.checks._probe_microphone",
        return_value=(False, "ffmpeg missing"),
    )
    ready, message = check_microphone()
    assert ready is False
    assert "ffmpeg is missing" in message


def test_check_transcription_local_ok(mocker):
    mocker.patch.dict("sys.modules", {"faster_whisper": mocker.MagicMock()})
    cfg = Config(transcription=TranscriptionConfig(model="tiny"))
    ready, message = check_transcription(cfg)
    assert ready is True
    assert "tiny" in message


def test_check_transcription_fallback_openai(mocker):
    mocker.patch.dict("sys.modules", {"faster_whisper": None})
    cfg = Config(
        transcription=TranscriptionConfig(),
        summarization=SummarizationConfig(openai_api_key="sk-key"),
    )
    ready, message = check_transcription(cfg)
    assert ready is True
    assert "OpenAI Whisper API" in message


def test_check_transcription_not_ready(mocker):
    mocker.patch.dict("sys.modules", {"faster_whisper": None})
    cfg = Config(transcription=TranscriptionConfig())
    ready, message = check_transcription(cfg)
    assert ready is False
    assert "pip install" in message


def test_check_diarization_heuristic():
    cfg = Config(diarization=DiarizationConfig(provider="heuristic"))
    ready, message = check_diarization(cfg)
    assert ready is True


def test_check_diarization_pyannote_missing_token(mocker):
    mocker.patch.dict(
        "sys.modules",
        {
            "pyannote": mocker.MagicMock(),
            "pyannote.audio": mocker.MagicMock(),
        },
    )
    cfg = Config(diarization=DiarizationConfig(provider="pyannote"))
    ready, message = check_diarization(cfg)
    assert ready is False
    assert "HUGGINGFACE_TOKEN" in message


def test_check_diarization_pyannote_with_token(mocker):
    mocker.patch.dict(
        "sys.modules",
        {
            "pyannote": mocker.MagicMock(),
            "pyannote.audio": mocker.MagicMock(),
        },
    )
    cfg = Config(diarization=DiarizationConfig(provider="pyannote", huggingface_token="hf"))
    ready, message = check_diarization(cfg)
    assert ready is True


def test_check_diarization_diarize_installed(mocker):
    mocker.patch.dict("sys.modules", {"diarize": mocker.MagicMock()})
    cfg = Config(diarization=DiarizationConfig(provider="diarize"))
    ready, message = check_diarization(cfg)
    assert ready is True


def test_check_diarization_diarize_missing(mocker):
    mocker.patch.dict("sys.modules", {"diarize": None})
    cfg = Config(diarization=DiarizationConfig(provider="diarize"))
    ready, message = check_diarization(cfg)
    assert ready is False
    assert "diarize not installed" in message


def test_check_summarization_claude_missing(mocker):
    mocker.patch("shutil.which", return_value=None)
    cfg = Config(summarization=SummarizationConfig(provider="claude"))
    ready, message = check_summarization(cfg)
    assert ready is False
    assert "claude CLI" in message


def test_check_summarization_openai_ok():
    cfg = Config(summarization=SummarizationConfig(provider="openai", openai_api_key="sk-key"))
    ready, message = check_summarization(cfg)
    assert ready is True


def test_check_summarization_anthropic_ok():
    cfg = Config(summarization=SummarizationConfig(provider="anthropic", anthropic_api_key="sk-key"))
    ready, message = check_summarization(cfg)
    assert ready is True


def test_check_summarization_unknown_provider():
    cfg = Config(summarization=SummarizationConfig(provider="unknown"))
    ready, message = check_summarization(cfg)
    assert ready is False
    assert "unknown summarization provider" in message


def test_run_setup_checks_returns_all_keys(mocker):
    mocker.patch("record_interview.checks.check_ffmpeg", return_value=(True, "ok"))
    mocker.patch("record_interview.checks.check_microphone", return_value=(True, "ok"))
    mocker.patch("record_interview.checks.check_transcription", return_value=(True, "ok"))
    mocker.patch("record_interview.checks.check_diarization", return_value=(True, "ok"))
    mocker.patch("record_interview.checks.check_summarization", return_value=(True, "ok"))
    result = run_setup_checks(Config())
    assert set(result.keys()) == {"ffmpeg", "microphone", "transcription", "diarization", "summarization"}


def test_probe_microphone_missing_ffmpeg(mocker):
    mocker.patch("shutil.which", return_value=None)
    ok, reason = _probe_microphone()
    assert ok is False
    assert reason == "ffmpeg missing"


def test_probe_microphone_granted(mocker):
    result = mocker.MagicMock()
    result.returncode = 0
    result.stderr = b""
    mocker.patch("record_interview.checks.subprocess.run", return_value=result)
    ok, reason = _probe_microphone()
    assert ok is True
    assert reason == "microphone accessible"


def test_probe_microphone_denied(mocker):
    result = mocker.MagicMock()
    result.returncode = 1
    result.stderr = b"Permission denied by user"
    mocker.patch("record_interview.checks.subprocess.run", return_value=result)
    ok, reason = _probe_microphone()
    assert ok is False
    assert reason == "permission denied"


def test_probe_microphone_times_out(mocker):
    mocker.patch(
        "record_interview.checks.subprocess.run",
        side_effect=subprocess.TimeoutExpired("ffmpeg", 30),
    )
    ok, reason = _probe_microphone(timeout_seconds=0.01)
    assert ok is False
    assert reason == "timed out"


def test_probe_microphone_handles_subprocess_error(mocker):
    mocker.patch(
        "record_interview.checks.subprocess.run",
        side_effect=FileNotFoundError("ffmpeg"),
    )
    ok, reason = _probe_microphone()
    assert ok is False
    assert reason.startswith("error:")


def test_probe_microphone_failed(mocker):
    result = mocker.MagicMock()
    result.returncode = 1
    result.stderr = b"first line\nlast line\n"
    mocker.patch("record_interview.checks.subprocess.run", return_value=result)
    ok, reason = _probe_microphone()
    assert ok is False
    assert "last line" in reason


def test_check_microphone_ok(mocker):
    mocker.patch("record_interview.checks._probe_microphone", return_value=(True, "microphone accessible"))
    ready, message = check_microphone()
    assert ready is True
    assert "accessible" in message


def test_check_microphone_missing_ffmpeg(mocker):
    mocker.patch("record_interview.checks._probe_microphone", return_value=(False, "ffmpeg missing"))
    ready, message = check_microphone()
    assert ready is False
    assert "ffmpeg is missing" in message


def test_check_microphone_permission_denied(mocker):
    mocker.patch("record_interview.checks._probe_microphone", return_value=(False, "permission denied"))
    ready, message = check_microphone()
    assert ready is False
    assert "permission denied" in message
    assert "tccutil reset Microphone" in message


def test_check_microphone_other_failure(mocker):
    mocker.patch("record_interview.checks._probe_microphone", return_value=(False, "failed: no device"))
    ready, message = check_microphone()
    assert ready is False
    assert "no device" in message


def test_request_microphone_permission_returns_probe_result(mocker):
    mocker.patch("record_interview.checks._probe_microphone", return_value=(True, "microphone accessible"))
    assert request_microphone_permission() is True
