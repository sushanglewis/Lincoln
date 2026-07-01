from __future__ import annotations

from pathlib import Path

from textual.app import App

from record_interview.config import Config
from record_interview.tui.screens.recording import RecordingScreen
from record_interview.tui.screens.setup import SetupScreen
from record_interview.tui.screens.summary import SummaryScreen


class LincolnRecordApp(App):
    """Textual TUI for recording Lincoln interviews."""

    CSS_PATH = "styles.css"
    SCREENS = {
        "setup": SetupScreen,
        "recording": RecordingScreen,
        "summary": SummaryScreen,
    }

    def __init__(
        self,
        workspace_root: Path,
        session_id: str,
        config: Config,
        design_id: str | None = None,
        topic: str | None = None,
        branch: str | None = None,
    ) -> None:
        super().__init__()
        self.workspace_root = workspace_root
        self.session_id = session_id
        self.config = config
        self.design_id = design_id
        self.topic = topic
        self.branch = branch
        self.duration_seconds = 0
        self.summary_path: Path | None = None
        self.phase_summaries: list[Path] = []

    def on_mount(self) -> None:
        self.push_screen("setup")
