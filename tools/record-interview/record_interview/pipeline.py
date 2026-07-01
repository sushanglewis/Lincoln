from __future__ import annotations

import logging
import queue
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from record_interview.config import Config
from record_interview.diarizer import Diarizer, build_diarizer
from record_interview.metadata import now_iso
from record_interview.phased_summary import PhasedSummaryGenerator
from record_interview.recorder import ChunkedRecorder
from record_interview.summarizer import Summarizer, build_summarizer
from record_interview.transcriber import Transcriber, TranscriptionSegment, build_transcriber


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PipelineSegment:
    start: float
    end: float
    speaker: str
    text: str


@dataclass
class TranscriptionPipeline:
    workspace_root: Path
    session_id: str
    config: Config
    on_segment: Callable[[PipelineSegment], None] | None = None
    on_phase_summary: Callable[[Path], None] | None = None
    on_error: Callable[[Exception], None] | None = None

    _segments: list[PipelineSegment] = field(default_factory=list, init=False)
    _segments_lock: threading.Lock = field(default_factory=threading.Lock, init=False)
    _running: bool = field(default=False, init=False)
    _thread: threading.Thread | None = field(default=None, init=False)
    _transcriber: Transcriber | None = field(default=None, init=False)
    _diarizer: Diarizer | None = field(default=None, init=False)
    _summarizer: Summarizer | None = field(default=None, init=False)
    _summary_generator: PhasedSummaryGenerator | None = field(default=None, init=False)
    _recorder: ChunkedRecorder | None = field(default=None, init=False)
    _start_time_offset: float = field(default=0.0, init=False)
    _phase_start_time: float = field(default=0.0, init=False)
    _phase_start_iso: str = field(default="", init=False)

    @property
    def segments(self) -> list[PipelineSegment]:
        with self._segments_lock:
            return list(self._segments)

    def _safe_call(self, callback: Callable | None, *args, **kwargs) -> None:
        if callback is None:
            return
        try:
            callback(*args, **kwargs)
        except Exception as e:
            logger.exception("Pipeline callback failed: %s", e)

    def _align(
        self,
        chunk_path: Path,
        transcript: list[TranscriptionSegment],
    ) -> list[PipelineSegment]:
        if not transcript:
            return []
        assigned = self._diarizer.assign_speakers(chunk_path, transcript)
        return [
            PipelineSegment(start=seg.start, end=seg.end, speaker=speaker, text=seg.text)
            for seg, speaker in assigned
        ]

    def _maybe_generate_phase_summary(self) -> None:
        elapsed = time.monotonic() - self._phase_start_time
        if elapsed < self.config.phase_interval_seconds:
            return
        if self._summary_generator is None:
            return
        with self._segments_lock:
            segments = [
                (s.start, s.end, s.speaker, s.text)
                for s in self._segments
                if s.start >= self._phase_start_time - self._start_time_offset
            ]
        end_time = now_iso()
        path = self._summary_generator.generate_phase_summary(
            segments,
            start_time=self._phase_start_iso,
            end_time=end_time,
        )
        self._phase_start_time = time.monotonic()
        self._phase_start_iso = end_time
        self._safe_call(self.on_phase_summary, path)

    def _process_chunk(self, chunk_path: Path) -> None:
        transcript = self._transcriber.transcribe(chunk_path)
        aligned = self._align(chunk_path, transcript)
        with self._segments_lock:
            for segment in aligned:
                self._segments.append(segment)
        for segment in aligned:
            self._safe_call(self.on_segment, segment)
        self._maybe_generate_phase_summary()

    def _run(self) -> None:
        while self._running:
            try:
                chunk_path = self._recorder.queue.get(timeout=0.5)
            except queue.Empty:
                continue
            if chunk_path is None:
                break
            try:
                self._process_chunk(chunk_path)
            except Exception as e:
                logger.exception("Failed to process chunk %s: %s", chunk_path, e)
                self._safe_call(self.on_error, e)

    def start(self) -> None:
        if self._running:
            return
        self._transcriber = build_transcriber(self.config)
        self._diarizer = build_diarizer(self.config)
        self._summarizer = build_summarizer(self.config)
        self._summary_generator = PhasedSummaryGenerator(
            workspace_root=self.workspace_root,
            session_id=self.session_id,
            summarizer=self._summarizer,
            phase_interval_seconds=self.config.phase_interval_seconds,
        )
        self._recorder = ChunkedRecorder(
            output_dir=self._summary_generator.session_dir / "chunks",
            chunk_seconds=self.config.chunk_seconds,
        )
        self._start_time_offset = time.monotonic()
        self._phase_start_time = self._start_time_offset
        self._phase_start_iso = now_iso()
        self._running = True
        self._recorder.start()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> int:
        if not self._running:
            return 0
        self._running = False
        duration = self._recorder.stop()
        self._recorder.queue.put(None)
        if self._thread is not None:
            self._thread.join(timeout=10)
        return duration

    def generate_final_summary(self) -> Path:
        if self._summary_generator is None:
            raise RuntimeError("pipeline has not been started")
        return self._summary_generator.generate_final_summary()
