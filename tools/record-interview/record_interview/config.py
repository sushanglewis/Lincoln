from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml


DEFAULT_CHUNK_SECONDS = 5
DEFAULT_PHASE_INTERVAL_SECONDS = 600


@dataclass(frozen=True)
class TranscriptionConfig:
    model: str = "tiny"
    device: str = "auto"
    compute_type: str = "default"


@dataclass(frozen=True)
class DiarizationConfig:
    provider: str = "heuristic"
    model: str = "pyannote/speaker-diarization-3.1"
    huggingface_token: str | None = None


@dataclass(frozen=True)
class SummarizationConfig:
    provider: str = "claude"
    model: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None


@dataclass(frozen=True)
class Config:
    chunk_seconds: int = DEFAULT_CHUNK_SECONDS
    phase_interval_seconds: int = DEFAULT_PHASE_INTERVAL_SECONDS
    transcription: TranscriptionConfig | None = None
    diarization: DiarizationConfig | None = None
    summarization: SummarizationConfig | None = None


def _env_or_none(name: str) -> str | None:
    value = os.environ.get(name)
    return value if value else None


def _load_lincolnrc() -> dict:
    rc_path = Path.home() / ".lincolnrc"
    if not rc_path.exists():
        return {}
    try:
        return yaml.safe_load(rc_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return {}


def load_config(argv: list[str] | None = None) -> Config:
    """Load configuration from ~/.lincolnrc, environment variables and CLI flags."""
    rc = _load_lincolnrc()

    transcription = TranscriptionConfig(
        model=rc.get("transcription", {}).get("model", "tiny"),
        device=rc.get("transcription", {}).get("device", "auto"),
        compute_type=rc.get("transcription", {}).get("compute_type", "default"),
    )

    diarization = DiarizationConfig(
        provider=rc.get("diarization", {}).get("provider", "heuristic"),
        model=rc.get("diarization", {}).get("model", "pyannote/speaker-diarization-3.1"),
        huggingface_token=_env_or_none("HUGGINGFACE_TOKEN")
        or rc.get("diarization", {}).get("huggingface_token"),
    )

    summarization = SummarizationConfig(
        provider=rc.get("summarization", {}).get("provider", "claude"),
        model=rc.get("summarization", {}).get("model"),
        openai_api_key=_env_or_none("OPENAI_API_KEY")
        or rc.get("summarization", {}).get("openai_api_key"),
        anthropic_api_key=_env_or_none("ANTHROPIC_API_KEY")
        or rc.get("summarization", {}).get("anthropic_api_key"),
    )

    return Config(
        chunk_seconds=int(rc.get("chunk_seconds", DEFAULT_CHUNK_SECONDS)),
        phase_interval_seconds=int(rc.get("phase_interval_seconds", DEFAULT_PHASE_INTERVAL_SECONDS)),
        transcription=transcription,
        diarization=diarization,
        summarization=summarization,
    )
