# tools/record-interview/record_interview/recorder.py
from __future__ import annotations

import logging
import queue
import re
import shutil
import subprocess
import threading
import time
from pathlib import Path

_LOGGER = logging.getLogger(__name__)


class RecordingError(Exception):
    pass


def _list_avfoundation_devices() -> str:
    try:
        result = subprocess.run(
            ["ffmpeg", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return ""
    return result.stderr or ""


def _find_avfoundation_audio_input() -> str | None:
    """Return the first AVFoundation audio input index (e.g. ':0') or None."""
    devices = _list_avfoundation_devices()
    in_audio_section = False
    for line in devices.splitlines():
        lower = line.lower()
        if "audio devices" in lower:
            in_audio_section = True
            continue
        if "video devices" in lower:
            in_audio_section = False
            continue
        if in_audio_section:
            match = re.search(r"\[(\d+)\]", line)
            if match:
                return f":{match.group(1)}"
    return None


def _resolve_avfoundation_input() -> str:
    """Resolve the AVFoundation audio input to use.

    ':default' is the documented shorthand, but on some macOS/terminal
    combinations it produces AVERROR_INVALIDDATA. Fall back to the first
    enumerated audio input device.
    """
    explicit = _find_avfoundation_audio_input()
    if explicit:
        return explicit
    return ":default"


class FfmpegRecorder:
    def __init__(self, sample_rate: int = 44100) -> None:
        self.sample_rate = sample_rate
        self._process: subprocess.Popen | None = None
        self._output_path: Path | None = None
        self._started_at: float | None = None

    def _build_command(self, output_path: Path) -> list[str]:
        return [
            "ffmpeg",
            "-y",
            "-f",
            "avfoundation",
            "-i",
            _resolve_avfoundation_input(),
            "-ar",
            str(self.sample_rate),
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            str(output_path),
        ]

    def start(self, output_path: Path) -> None:
        if not shutil.which("ffmpeg"):
            raise RecordingError("ffmpeg not found in PATH")
        if self._process is not None:
            raise RecordingError("already recording")

        self._output_path = output_path
        self._started_at = time.monotonic()
        cmd = self._build_command(output_path)
        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        time.sleep(0.05)
        if self._process.poll() is not None:
            stderr = self._process.stderr.read() if self._process.stderr else ""
            self._process = None
            self._started_at = None
            _LOGGER.warning("ffmpeg failed to start: %s", stderr)
            raise RecordingError("ffmpeg failed to start. Check the logs for details.")

    def stop(self) -> int:
        if self._process is None:
            raise RecordingError("not recording")
        self._process.terminate()
        try:
            self._process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait(timeout=5)

        returncode = self._process.returncode
        stderr = self._process.stderr.read() if self._process.stderr else ""
        duration = int(time.monotonic() - self._started_at) if self._started_at else 0
        self._process = None
        self._started_at = None

        if returncode != 0:
            # ffmpeg often exits with 255 after receiving SIGTERM, even though
            # it has already flushed the output. Treat that as a successful stop.
            if "Exiting normally" in stderr:
                return duration
            _LOGGER.warning("ffmpeg exited with code %s: %s", returncode, stderr)
            raise RecordingError(
                f"ffmpeg exited with code {returncode}. Check the logs for details."
            )
        return duration

    def is_recording(self) -> bool:
        return self._process is not None and self._process.poll() is None


class ChunkedRecorder:
    """Record audio into fixed-duration chunks using ffmpeg's segment muxer."""

    def __init__(
        self, output_dir: Path, chunk_seconds: int = 5, sample_rate: int = 44100
    ) -> None:
        self.output_dir = output_dir
        self.chunk_seconds = chunk_seconds
        self.sample_rate = sample_rate
        self.queue: queue.Queue[Path | None] = queue.Queue()
        self._process: subprocess.Popen | None = None
        self._started_at: float | None = None
        self._watcher_thread: threading.Thread | None = None
        self._running = False

    def _build_command(self) -> list[str]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        pattern = str(self.output_dir / "chunk_%03d.m4a")
        return [
            "ffmpeg",
            "-y",
            "-f",
            "avfoundation",
            "-i",
            _resolve_avfoundation_input(),
            "-ar",
            str(self.sample_rate),
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-f",
            "segment",
            "-segment_time",
            str(self.chunk_seconds),
            "-reset_timestamps",
            "1",
            pattern,
        ]

    def _watcher(self) -> None:
        """Enqueue finalized chunks (all but the most recent) for processing."""
        enqueued: set[Path] = set()
        while self._running:
            time.sleep(0.2)
            chunks = get_chunk_paths(self.output_dir)
            if len(chunks) < 2:
                continue
            for path in chunks[:-1]:
                if path in enqueued:
                    continue
                try:
                    if not path.exists() or path.stat().st_size == 0:
                        continue
                except OSError:
                    continue
                self.queue.put(path)
                enqueued.add(path)

        # Flush any remaining chunks when stopping; at this point ffmpeg has
        # closed the final file.
        for path in get_chunk_paths(self.output_dir):
            if path in enqueued:
                continue
            try:
                if path.exists() and path.stat().st_size > 0:
                    self.queue.put(path)
            except OSError:
                continue

    def start(self) -> None:
        if not shutil.which("ffmpeg"):
            raise RecordingError("ffmpeg not found in PATH")
        if self._process is not None:
            raise RecordingError("already recording")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        for path in get_chunk_paths(self.output_dir):
            path.unlink(missing_ok=True)
        (self.output_dir / "concat_list.txt").unlink(missing_ok=True)

        self._started_at = time.monotonic()
        self._running = True
        self._watcher_thread = threading.Thread(target=self._watcher, daemon=True)
        self._watcher_thread.start()

        cmd = self._build_command()
        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        time.sleep(0.05)
        if self._process.poll() is not None:
            stderr = self._process.stderr.read() if self._process.stderr else ""
            self._process = None
            self._running = False
            _LOGGER.warning("ffmpeg failed to start: %s", stderr)
            raise RecordingError("ffmpeg failed to start. Check the logs for details.")

    def stop(self) -> int:
        if self._process is None:
            raise RecordingError("not recording")
        self._running = False
        self._process.terminate()
        try:
            self._process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait(timeout=5)

        returncode = self._process.returncode
        stderr = self._process.stderr.read() if self._process.stderr else ""
        duration = int(time.monotonic() - self._started_at) if self._started_at else 0
        self._process = None

        if self._watcher_thread is not None:
            self._watcher_thread.join(timeout=2)

        if returncode != 0 and "Exiting normally" not in stderr:
            _LOGGER.warning("ffmpeg exited with code %s: %s", returncode, stderr)
            raise RecordingError(
                f"ffmpeg exited with code {returncode}. Check the logs for details."
            )
        return duration

    def is_recording(self) -> bool:
        return self._process is not None and self._process.poll() is None


def get_chunk_paths(chunks_dir: Path) -> list[Path]:
    """Return sorted list of all chunk files in the directory."""
    return sorted(chunks_dir.glob("chunk_*.m4a"))


def concatenate_chunks(chunks_dir: Path, output_path: Path) -> Path | None:
    """Concatenate chunk files into a single audio file using ffmpeg concat demuxer.

    Returns the output path on success, None if no chunks exist.
    Raises RecordingError on ffmpeg failure.
    """
    chunk_files = get_chunk_paths(chunks_dir)
    if not chunk_files:
        return None

    output_path.parent.mkdir(parents=True, exist_ok=True)

    list_path = chunks_dir / "concat_list.txt"
    lines = [f"file '{chunk.name}'" for chunk in chunk_files]
    list_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_path),
        "-c",
        "copy",
        str(output_path),
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(chunks_dir),
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (subprocess.SubprocessError, FileNotFoundError, OSError) as exc:
        raise RecordingError(f"chunk concatenation failed: {exc}") from exc

    if result.returncode != 0:
        raise RecordingError(
            f"chunk concatenation failed (code {result.returncode}): {result.stderr}"
        )

    return output_path
