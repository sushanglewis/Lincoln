from __future__ import annotations

import abc
from dataclasses import dataclass
from pathlib import Path

from record_interview.config import Config
from record_interview.transcriber import TranscriptionSegment


@dataclass(frozen=True)
class DiarizationSegment:
    start: float
    end: float
    speaker: str


class Diarizer(abc.ABC):
    @abc.abstractmethod
    def diarize(self, audio_path: Path) -> list[DiarizationSegment]:
        raise NotImplementedError

    @abc.abstractmethod
    def assign_speakers(
        self,
        audio_path: Path,
        segments: list[TranscriptionSegment],
    ) -> list[tuple[TranscriptionSegment, str]]:
        """Assign a speaker label to each transcription segment."""
        raise NotImplementedError


def _pick_speaker(segment: TranscriptionSegment, diarization: list[DiarizationSegment]) -> str:
    mid = (segment.start + segment.end) / 2
    for seg in diarization:
        if seg.start <= mid < seg.end:
            return seg.speaker
    return "UNKNOWN"


class PyannoteDiarizer(Diarizer):
    def __init__(self, model: str = "pyannote/speaker-diarization-3.1", huggingface_token: str | None = None) -> None:
        try:
            from pyannote.audio import Pipeline
        except ImportError as e:
            raise ImportError("pyannote.audio is not installed") from e
        import os
        token = huggingface_token or os.environ.get("HUGGINGFACE_TOKEN")
        self._pipeline = Pipeline.from_pretrained(model, use_auth_token=token)

    def diarize(self, audio_path: Path) -> list[DiarizationSegment]:
        diarization = self._pipeline(str(audio_path))
        return [
            DiarizationSegment(start=turn.start, end=turn.end, speaker=speaker)
            for turn, _, speaker in diarization.itertracks(yield_label=True)
        ]

    def assign_speakers(
        self,
        audio_path: Path,
        segments: list[TranscriptionSegment],
    ) -> list[tuple[TranscriptionSegment, str]]:
        if not segments:
            return []
        diarization = self.diarize(audio_path)
        return [(segment, _pick_speaker(segment, diarization)) for segment in segments]


class DiarizeDiarizer(Diarizer):
    def __init__(self) -> None:
        try:
            from diarize import Diarizer as _Diarizer  # type: ignore
        except ImportError as e:
            raise ImportError("diarize is not installed") from e
        self._diarizer = _Diarizer()

    def diarize(self, audio_path: Path) -> list[DiarizationSegment]:
        result = self._diarizer.diarize(str(audio_path))
        return [
            DiarizationSegment(start=s["start"], end=s["end"], speaker=s["speaker"])
            for s in result
        ]

    def assign_speakers(
        self,
        audio_path: Path,
        segments: list[TranscriptionSegment],
    ) -> list[tuple[TranscriptionSegment, str]]:
        return [(segment, "UNKNOWN") for segment in segments]


class HeuristicDiarizer(Diarizer):
    """Fallback diarizer that labels each transcription segment alternately."""

    def __init__(self, speakers: tuple[str, str] = ("SPEAKER_A", "SPEAKER_B")) -> None:
        self._speakers = speakers

    def diarize(self, audio_path: Path) -> list[DiarizationSegment]:
        return []

    def assign_speakers(
        self,
        audio_path: Path,
        segments: list[TranscriptionSegment],
    ) -> list[tuple[TranscriptionSegment, str]]:
        return [
            (segment, self._speakers[index % len(self._speakers)])
            for index, segment in enumerate(segments)
        ]


def build_diarizer(config: Config) -> Diarizer:
    if config.diarization is None:
        raise ValueError("diarization configuration is missing")
    provider = config.diarization.provider
    if provider == "pyannote":
        return PyannoteDiarizer(
            model=config.diarization.model,
            huggingface_token=config.diarization.huggingface_token,
        )
    if provider == "diarize":
        return DiarizeDiarizer()
    if provider == "heuristic":
        return HeuristicDiarizer()
    raise ValueError(f"unknown diarization provider: {provider}")
