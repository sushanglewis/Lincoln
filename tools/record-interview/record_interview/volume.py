from __future__ import annotations

import logging
import re
import subprocess
import threading
import time
from pathlib import Path
from typing import Callable

_LOGGER = logging.getLogger(__name__)


def analyze_chunk_loudness(chunk_path: Path) -> tuple[float, float] | None:
    """Return (mean_volume_db, max_volume_db) for a chunk using ffmpeg volumedetect.

    Returns None if ffmpeg is unavailable or parsing fails.
    """
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(chunk_path),
        "-af",
        "volumedetect",
        "-f",
        "null",
        "-",
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (subprocess.SubprocessError, FileNotFoundError, OSError) as exc:
        _LOGGER.debug("Volume analysis failed for %s: %s", chunk_path, exc)
        return None

    stderr = result.stderr or ""
    mean_match = re.search(r"mean_volume:\s*([-\d.]+)\s*dB", stderr)
    max_match = re.search(r"max_volume:\s*([-\d.]+)\s*dB", stderr)
    if not mean_match or not max_match:
        return None
    try:
        return float(mean_match.group(1)), float(max_match.group(1))
    except ValueError:
        return None


class VolumeAnalyzer:
    """Poll a chunk directory and emit the latest max dB level for each new chunk."""

    def __init__(
        self,
        chunks_dir: Path,
        on_level: Callable[[float], None] | None = None,
        poll_interval: float = 0.2,
    ) -> None:
        self.chunks_dir = chunks_dir
        self.on_level = on_level
        self.poll_interval = poll_interval
        self._running = False
        self._thread: threading.Thread | None = None
        self._seen: set[Path] = set()

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._seen = set()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2)

    def _run(self) -> None:
        while self._running:
            try:
                current = set(self.chunks_dir.glob("chunk_*.m4a"))
                new = sorted(current - self._seen)
                for path in new:
                    # Wait briefly for the chunk to finish writing.
                    time.sleep(0.2)
                    levels = analyze_chunk_loudness(path)
                    if levels is not None:
                        _mean, max_db = levels
                        self._emit(max_db)
                    self._seen.add(path)
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Volume analyzer loop failed")
            time.sleep(self.poll_interval)

    def _emit(self, db: float) -> None:
        if self.on_level is not None:
            try:
                self.on_level(db)
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Volume level callback failed")
