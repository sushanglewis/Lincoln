from __future__ import annotations


class GuidanceError(Exception):
    """Base class for user-facing errors that include remediation steps."""

    def __init__(self, message: str, remediation: str) -> None:
        super().__init__(message)
        self.message = message
        self.remediation = remediation


class FfmpegMissingError(GuidanceError):
    def __init__(self) -> None:
        super().__init__(
            message="ffmpeg not found in PATH",
            remediation="Install ffmpeg, e.g. 'brew install ffmpeg' on macOS, then restart the terminal.",
        )


class NoMicrophoneError(GuidanceError):
    def __init__(self) -> None:
        super().__init__(
            message="no microphone available or permission denied",
            remediation="Grant microphone access to the terminal in System Settings > Privacy & Security > Microphone.",
        )


class WhisperNotInstalledError(GuidanceError):
    def __init__(self) -> None:
        super().__init__(
            message="faster-whisper is not installed",
            remediation="Install faster-whisper: 'pip install faster-whisper'. Alternatively set OPENAI_API_KEY to use the Whisper API.",
        )


class ApiKeyMissingError(GuidanceError):
    def __init__(self, provider: str) -> None:
        super().__init__(
            message=f"API key missing for {provider}",
            remediation=f"Set {provider.upper()}_API_KEY in your environment or ~/.lincolnrc, or switch to the claude CLI summary provider.",
        )


class GitWorktreeError(GuidanceError):
    def __init__(self) -> None:
        super().__init__(
            message="failed to detect git worktree root",
            remediation="Run this command inside a git worktree, or ensure 'git' is installed and available in PATH.",
        )


class ClaudeCliMissingError(GuidanceError):
    def __init__(self) -> None:
        super().__init__(
            message="claude CLI not found in PATH",
            remediation="Install the Claude Code CLI: 'brew install anthropic/tap/claude-code', or configure summary_provider to 'openai'/'anthropic' in ~/.lincolnrc.",
        )


class PyannoteMissingError(GuidanceError):
    def __init__(self) -> None:
        super().__init__(
            message="pyannote.audio is not installed",
            remediation="Install pyannote.audio: 'pip install pyannote.audio', or switch diarizer to 'diarize'/'heuristic' in ~/.lincolnrc.",
        )
