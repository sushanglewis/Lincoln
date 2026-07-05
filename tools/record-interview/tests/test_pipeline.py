from pathlib import Path
from unittest.mock import MagicMock

import pytest

from record_interview.config import (
    Config,
    DiarizationConfig,
    SummarizationConfig,
    TranscriptionConfig,
)
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
    mocker.patch(
        "record_interview.pipeline.build_transcriber", return_value=_fake_transcriber()
    )
    mocker.patch(
        "record_interview.pipeline.build_diarizer", return_value=_fake_diarizer()
    )
    mocker.patch(
        "record_interview.pipeline.build_summarizer", return_value=_fake_summarizer()
    )

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
    pipeline._summary_generator.generate_phase_summary.return_value = Path(
        "phase-summary-01.md"
    )
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


def test_pipeline_stop_concatenates_chunks(mocker, tmp_path):
    config = Config(
        transcription=TranscriptionConfig(),
        diarization=DiarizationConfig(provider="heuristic"),
        summarization=SummarizationConfig(provider="openai", openai_api_key="sk-key"),
    )
    mocker.patch("record_interview.pipeline.build_transcriber")
    mocker.patch("record_interview.pipeline.build_diarizer")
    mocker.patch("record_interview.pipeline.build_summarizer")
    concat_mock = mocker.patch(
        "record_interview.pipeline.concatenate_chunks",
        return_value=tmp_path / "recordings" / "2026-06-27-test.m4a",
    )

    pipeline = TranscriptionPipeline(
        workspace_root=tmp_path,
        session_id="2026-06-27-test",
        config=config,
    )
    chunks_dir = tmp_path / "interviews" / "2026-06-27-test" / "chunks"
    chunks_dir.mkdir(parents=True)
    (chunks_dir / "chunk_000.m4a").write_bytes(b"fake")

    fake_recorder = MagicMock()
    fake_recorder.output_dir = chunks_dir
    fake_recorder.queue = MagicMock()
    fake_recorder.queue.get_nowait.side_effect = [
        chunks_dir / "chunk_000.m4a",
        None,
    ]
    fake_recorder.stop.return_value = 12

    pipeline._summary_generator = MagicMock()
    pipeline._summary_generator.session_dir = chunks_dir.parent
    pipeline._recorder = fake_recorder
    pipeline._recording_path = tmp_path / "recordings" / "2026-06-27-test.m4a"
    pipeline._transcriber = MagicMock()
    pipeline._transcriber.transcribe.return_value = []
    pipeline._diarizer = MagicMock()
    pipeline._thread = MagicMock()
    pipeline._volume_analyzer = MagicMock()
    pipeline._running = True

    duration = pipeline.stop()

    assert duration == 12
    concat_mock.assert_called_once_with(
        chunks_dir,
        tmp_path / "recordings" / "2026-06-27-test.m4a",
    )


def test_pipeline_status_callback_is_invoked(mocker, tmp_path):
    config = Config(
        transcription=TranscriptionConfig(),
        diarization=DiarizationConfig(provider="heuristic"),
        summarization=SummarizationConfig(provider="openai", openai_api_key="sk-key"),
    )
    mocker.patch("record_interview.pipeline.build_transcriber")
    mocker.patch("record_interview.pipeline.build_diarizer")
    mocker.patch("record_interview.pipeline.build_summarizer")

    statuses = []
    pipeline = TranscriptionPipeline(
        workspace_root=tmp_path,
        session_id="2026-06-27-test",
        config=config,
        on_status=statuses.append,
    )
    chunks_dir = tmp_path / "interviews" / "2026-06-27-test" / "chunks"
    chunks_dir.mkdir(parents=True)
    pipeline._summary_generator = MagicMock()
    pipeline._summary_generator.session_dir = chunks_dir.parent
    pipeline._recorder = MagicMock()
    pipeline._recorder.output_dir = chunks_dir
    pipeline._recorder.queue = MagicMock()
    pipeline._volume_analyzer = MagicMock()

    pipeline.start()
    assert any("等待音频" in s for s in statuses)
    pipeline.stop()
    assert any("正在保存最终录音" in s for s in statuses)
