from __future__ import annotations

import abc
import os
from dataclasses import dataclass
from pathlib import Path

from record_interview.config import Config


@dataclass(frozen=True)
class TranscriptionSegment:
    start: float
    end: float
    text: str


class Transcriber(abc.ABC):
    @abc.abstractmethod
    def transcribe(self, audio_path: Path) -> list[TranscriptionSegment]:
        raise NotImplementedError


class FasterWhisperTranscriber(Transcriber):
    def __init__(self, model: str = "small", device: str = "auto", compute_type: str = "default") -> None:
        try:
            from faster_whisper import WhisperModel
        except ImportError as e:
            raise ImportError("faster-whisper is not installed") from e
        self._model = WhisperModel(model, device=device, compute_type=compute_type)

    def transcribe(self, audio_path: Path) -> list[TranscriptionSegment]:
        segments, _ = self._model.transcribe(str(audio_path))
        return [
            TranscriptionSegment(start=s.start, end=s.end, text=s.text.strip())
            for s in segments
        ]


class OpenAIWhisperTranscriber(Transcriber):
    def __init__(self, api_key: str | None = None, model: str = "whisper-1") -> None:
        try:
            from openai import OpenAI
        except ImportError as e:
            raise ImportError("openai package is not installed") from e
        self._client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        self._model = model

    def transcribe(self, audio_path: Path) -> list[TranscriptionSegment]:
        with open(audio_path, "rb") as f:
            transcript = self._client.audio.transcriptions.create(
                model=self._model,
                file=f,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )
        return [
            TranscriptionSegment(start=s.start, end=s.end, text=s.text.strip())
            for s in transcript.segments
        ]


def build_transcriber(config: Config) -> Transcriber:
    if config.transcription is None:
        raise ValueError("transcription configuration is missing")
    try:
        return FasterWhisperTranscriber(
            model=config.transcription.model,
            device=config.transcription.device,
            compute_type=config.transcription.compute_type,
        )
    except ImportError:
        if config.summarization and config.summarization.openai_api_key:
            return OpenAIWhisperTranscriber(api_key=config.summarization.openai_api_key)
        raise
