from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Static

from record_interview.process import ProcessInterviewError, trigger_process_interview


class SummaryScreen(Screen):
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("p", "process", "Process"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(id="summary-body")
        table = DataTable(id="phase-summaries")
        table.add_columns("Phase", "File")
        yield table
        yield Footer()

    def on_mount(self) -> None:
        app = self.app
        body = self.query_one("#summary-body", Vertical)
        body.remove_children()
        body.mount(Static(f"Session: {app.session_id}"))
        body.mount(Static(f"Duration: {self._format_duration(app.duration_seconds)}"))
        body.mount(Static(f"Workspace: {app.workspace_root}"))
        if app.summary_path:
            body.mount(Static(f"Summary: {app.summary_path}"))

        table = self.query_one("#phase-summaries", DataTable)
        for index, path in enumerate(app.phase_summaries, start=1):
            table.add_row(str(index), path.name)

    @staticmethod
    def _format_duration(seconds: int) -> str:
        minutes, secs = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def action_process(self) -> None:
        try:
            trigger_process_interview(self.app.workspace_root, self.app.session_id)
            self.notify("process-interview completed")
        except ProcessInterviewError as e:
            self.notify(f"process-interview failed: {e}", severity="error")
