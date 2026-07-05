from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from record_interview.checks import run_setup_checks
from record_interview.metadata import build_metadata, write_metadata


class SetupScreen(Screen):
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh_checks", "Refresh"),
        ("s", "start_recording", "Start"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._checks: dict[str, tuple[bool, str]] = {}

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Environment checks", id="setup-title")
        with ScrollableContainer(id="checks"):
            yield Vertical(id="checks-list")
        yield Static("", id="setup-status")
        yield Footer()

    def on_mount(self) -> None:
        self._run_checks()

    def _run_checks(self) -> None:
        self._checks = run_setup_checks(self.app.config)
        self._render_checks()

    def _render_checks(self) -> None:
        container = self.query_one("#checks-list", Vertical)
        container.remove_children()
        all_ready = True
        for name, (ready, message) in self._checks.items():
            icon = "✓" if ready else "✗"
            css_class = "check-ok" if ready else "check-fail"
            container.mount(
                Static(f"{icon} {name.capitalize()}: {message}", classes=css_class)
            )
            if not ready:
                all_ready = False

        status = self.query_one("#setup-status", Static)
        if all_ready:
            status.update("按 [b]s[/b] 开始录制，按 [b]q[/b] 退出")
        else:
            status.update("检查未通过，按 [b]r[/b] 刷新，按 [b]q[/b] 退出")

        self._can_start = all_ready

    def _prepare_metadata(self) -> None:
        app = self.app
        metadata = build_metadata(
            session_id=app.session_id,
            design_id=app.design_id,
            topic=app.topic,
            branch=app.branch,
            transcription_model=app.config.transcription.model
            if app.config.transcription
            else None,
            diarization_model=app.config.diarization.model
            if app.config.diarization
            else None,
            summarization_model=app.config.summarization.model
            if app.config.summarization
            else None,
        )
        write_metadata(app.workspace_root, app.session_id, metadata)

    def action_refresh_checks(self) -> None:
        self._run_checks()

    def action_start_recording(self) -> None:
        if not getattr(self, "_can_start", False):
            self.notify(
                "Environment checks must pass before starting", severity="warning"
            )
            return
        self._prepare_metadata()
        self.app.push_screen("recording")
