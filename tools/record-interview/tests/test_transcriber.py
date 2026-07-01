import pytest

from record_interview.config import Config, SummarizationConfig, TranscriptionConfig
from record_interview.transcriber import OpenAIWhisperTranscriber, build_transcriber


def test_build_transcriber_prefers_faster_whisper(mocker):
    mocker.patch.dict("sys.modules", {"faster_whisper": mocker.MagicMock()})
    cfg = Config(transcription=TranscriptionConfig(model="tiny"))
    transcriber = build_transcriber(cfg)
    assert transcriber._model is not None


def test_build_transcriber_falls_back_to_openai(mocker):
    mocker.patch.dict("sys.modules", {"faster_whisper": None})
    mocker.patch.dict("sys.modules", {"openai": mocker.MagicMock()})
    cfg = Config(
        transcription=TranscriptionConfig(),
        summarization=SummarizationConfig(openai_api_key="sk-key"),
    )
    transcriber = build_transcriber(cfg)
    assert isinstance(transcriber, OpenAIWhisperTranscriber)


def test_build_transcriber_raises_when_no_backend():
    cfg = Config(transcription=TranscriptionConfig())
    with pytest.raises(ImportError):
        build_transcriber(cfg)
