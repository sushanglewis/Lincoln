from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static

from record_interview.process import ProcessInterviewError, trigger_process_interview


class SummaryScreen(Screen):
    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Static("Recording Complete", id="summary-title")
        yield Vertical(id="summary-body")
        with Horizontal(id="summary-actions"):
            yield Button("Trigger process-interview", id="process", variant="primary")
            yield Button("Exit", id="exit")

    def on_mount(self) -> None:
        app = self.app
        body = self.query_one("#summary-body", Vertical)
        body.remove_children()
        minutes, seconds = divmod(app.duration_seconds, 60)
        body.mount(Static(f"Duration: {minutes:02d}:{seconds:02d}"))
        body.mount(Static(f"Workspace: {app.workspace_root}"))
        if app.summary_path:
            body.mount(Static(f"Summary: {app.summary_path}"))
        if app.phase_summaries:
            body.mount(Static("Phase summaries:"))
            for path in app.phase_summaries:
                body.mount(Static(f"  - {path.name}"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "process":
            try:
                trigger_process_interview(self.app.workspace_root, self.app.session_id)
                self.notify("process-interview completed")
            except ProcessInterviewError as e:
                self.notify(f"process-interview failed: {e}", severity="error")
        elif event.button.id == "exit":
            self.app.exit(0)
