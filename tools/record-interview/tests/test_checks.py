from record_interview.checks import (
    check_diarization,
    check_ffmpeg,
    check_microphone,
    check_summarization,
    check_transcription,
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
        "record_interview.checks._list_avfoundation_devices",
        return_value="[AVFoundation indev] input device 0",
    )
    ready, message = check_microphone()
    assert ready is True


def test_check_microphone_missing(mocker):
    mocker.patch("record_interview.checks._list_avfoundation_devices", return_value="")
    mocker.patch("shutil.which", return_value="/usr/bin/ffmpeg")
    ready, message = check_microphone()
    assert ready is False
    assert "Privacy" in message


def test_check_microphone_cannot_check_without_ffmpeg(mocker):
    mocker.patch("record_interview.checks._list_avfoundation_devices", return_value="")
    mocker.patch("shutil.which", return_value=None)
    ready, message = check_microphone()
    assert ready is False
    assert "cannot check microphone" in message


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
