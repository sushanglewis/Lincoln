from pathlib import Path
from unittest.mock import MagicMock

import pytest

from record_interview.config import Config, DiarizationConfig, SummarizationConfig, TranscriptionConfig
from record_interview.diarizer import HeuristicDiarizer
from record_interview.pipeline import PipelineSegment, TranscriptionPipeline
from record_interview.transcriber import TranscriptionSegment


def _fake_transcriber():
    transcriber = MagicMock()
    transcriber.transcribe.return_value = [
        TranscriptionSegment(start=0.0, end=1.0, text="hello world"),
    ]
    return transcriber


def _fake_diarizer():
    return HeuristicDiarizer()


def _fake_summarizer():
    summarizer = MagicMock()
    summarizer.summarize.return_value = "phase summary"
    return summarizer


def test_pipeline_processes_chunk_and_emits_segment(mocker, tmp_path):
    mocker.patch("record_interview.pipeline.build_transcriber", return_value=_fake_transcriber())
    mocker.patch("record_interview.pipeline.build_diarizer", return_value=_fake_diarizer())
    mocker.patch("record_interview.pipeline.build_summarizer", return_value=_fake_summarizer())

    received = []

    def on_segment(segment: PipelineSegment) -> None:
        received.append(segment)

    config = Config(
        transcription=TranscriptionConfig(),
        diarization=DiarizationConfig(provider="heuristic"),
        summarization=SummarizationConfig(provider="openai", openai_api_key="sk-key"),
        chunk_seconds=5,
        phase_interval_seconds=600,
    )
    pipeline = TranscriptionPipeline(
        workspace_root=tmp_path,
        session_id="2026-06-27-test",
        config=config,
        on_segment=on_segment,
    )

    fake_recorder = MagicMock()
    fake_recorder.queue = mocker.MagicMock()
    fake_recorder.queue.get.side_effect = [Path("chunk_000.m4a"), None]
    fake_recorder.stop.return_value = 10
    mocker.patch.object(pipeline, "_recorder", fake_recorder)

    pipeline._start_time_offset = 0.0
    pipeline._phase_start_time = 0.0
    pipeline._phase_start_iso = "2026-06-27T10:00:00Z"
    pipeline._transcriber = _fake_transcriber()
    pipeline._diarizer = _fake_diarizer()
    pipeline._summarizer = _fake_summarizer()
    pipeline._summary_generator = MagicMock()
    pipeline._summary_generator.generate_phase_summary.return_value = Path("phase-summary-01.md")
    pipeline._running = True

    pipeline._run()

    assert len(received) == 1
    assert received[0].text == "hello world"


def test_pipeline_raises_when_generating_summary_without_start(tmp_path):
    config = Config(
        transcription=TranscriptionConfig(),
        diarization=DiarizationConfig(provider="heuristic"),
        summarization=SummarizationConfig(provider="openai", openai_api_key="sk-key"),
    )
    pipeline = TranscriptionPipeline(
        workspace_root=tmp_path,
        session_id="2026-06-27-test",
        config=config,
    )
    with pytest.raises(RuntimeError, match="pipeline has not been started"):
        pipeline.generate_final_summary()
