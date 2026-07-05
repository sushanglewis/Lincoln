from __future__ import annotations

import time
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Static
from textual.worker import Worker, WorkerState

from record_interview.metadata import update_recording_complete
from record_interview.pipeline import PipelineSegment, TranscriptionPipeline
from record_interview.tui.widgets.audio_meter import AudioMeter


class RecordingScreen(Screen):
    BINDINGS = [
        ("q", "stop", "Stop"),
        ("space", "mark", "Mark"),
    ]

    elapsed_seconds: reactive[int] = reactive(0)
    audio_level_db: reactive[float | None] = reactive(None)
    status_message: reactive[str] = reactive("准备中...")

    def __init__(self) -> None:
        super().__init__()
        self._pipeline: TranscriptionPipeline | None = None
        self._start_time = 0.0
        self._stopping = False

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="recording-header"):
            yield Static("00:00:00", id="timer")
            yield AudioMeter(id="audio-meter")
        yield Static(self.status_message, id="status-bar")
        table = DataTable(id="transcript")
        table.add_columns("Time", "Speaker", "Text")
        yield table
        yield Footer()

    def on_mount(self) -> None:
        self._start_time = time.monotonic()
        self.set_interval(1, self._tick)
        try:
            self._start_pipeline()
        except Exception as exc:  # noqa: BLE001
            self._on_error(exc)
            self._stop()

    def _start_pipeline(self) -> None:
        app = self.app
        self._pipeline = TranscriptionPipeline(
            workspace_root=app.workspace_root,
            session_id=app.session_id,
            config=app.config,
            on_segment=self._on_segment,
            on_phase_summary=self._on_phase_summary,
            on_error=self._on_error,
            on_status=self._on_status,
            on_volume=self._on_volume,
        )
        self._pipeline.start()

    def _on_segment(self, segment: PipelineSegment) -> None:
        def update():
            table = self.query_one("#transcript", DataTable)
            start_time = self._format_timestamp(segment.start)
            table.add_row(start_time, segment.speaker, segment.text)
            table.scroll_end(animate=False)
            self._trim_transcript_rows()

        self.app.call_from_thread(update)

    def _trim_transcript_rows(self) -> None:
        table = self.query_one("#transcript", DataTable)
        while table.row_count > 500:
            row_keys = list(table.rows.keys())
            if not row_keys:
                break
            table.remove_row(row_keys[0])

    def _on_phase_summary(self, path: Path) -> None:
        def update():
            self.app.phase_summaries.append(path)
            self.notify(f"阶段总结已保存: {path.name}")

        self.app.call_from_thread(update)

    def _on_error(self, error: Exception) -> None:
        def update():
            self.status_message = f"错误: {error}"
            self.query_one("#status-bar", Static).update(self.status_message)

        self.app.call_from_thread(update)

    def _on_status(self, message: str) -> None:
        def update():
            self.status_message = message
            self.query_one("#status-bar", Static).update(self.status_message)

        self.app.call_from_thread(update)

    def _on_volume(self, db: float) -> None:
        def update():
            self.audio_level_db = db

        self.app.call_from_thread(update)

    def watch_elapsed_seconds(self, elapsed: int) -> None:
        self.query_one("#timer", Static).update(self._format_timestamp(elapsed))
        if self._pipeline is not None:
            interval = self.app.config.phase_interval_seconds
            remaining = max(0, interval - (elapsed % interval))
            header = self.query_one(Header)
            header.sub_title = f"Next summary {self._format_timestamp(remaining)}"

    def watch_audio_level_db(self, db: float | None) -> None:
        self.query_one("#audio-meter", AudioMeter).level_db = db

    def _tick(self) -> None:
        self.elapsed_seconds = int(time.monotonic() - self._start_time)

    def action_stop(self) -> None:
        self._stop()

    def action_mark(self) -> None:
        def update():
            table = self.query_one("#transcript", DataTable)
            table.add_row(self._format_timestamp(self.elapsed_seconds), "MARK", "---")
            table.scroll_end(animate=False)

        self.app.call_from_thread(update)

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        minutes, secs = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def _stop(self) -> None:
        if self._stopping:
            return
        if self._pipeline is None:
            self.app.push_screen("summary")
            return
        self._stopping = True
        self.status_message = "正在停止并保存录音..."
        self.query_one("#status-bar", Static).update(self.status_message)
        self.run_worker(self._finalize, thread=True)

    def _finalize(self) -> None:
        duration = 0
        try:
            duration = self._pipeline.stop()
        except Exception as e:  # noqa: BLE001
            self._on_error(e)
            duration = self.elapsed_seconds
        self.app.duration_seconds = duration
        try:
            update_recording_complete(
                self.app.workspace_root, self.app.session_id, duration
            )
        except Exception as e:  # noqa: BLE001
            self._on_error(e)
        try:
            summary_path = self._pipeline.generate_final_summary()
            self.app.summary_path = summary_path
        except Exception as e:  # noqa: BLE001
            self._on_error(e)
        self.app.call_from_thread(self._finish)

    def _finish(self) -> None:
        self.app.push_screen("summary")

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.worker.name == "_finalize" and event.state == WorkerState.ERROR:
            self.notify("停止过程出错，请查看日志", severity="error")
            self._finish()
