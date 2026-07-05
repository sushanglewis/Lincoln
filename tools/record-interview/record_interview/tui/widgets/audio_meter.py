from __future__ import annotations

from textual.reactive import reactive
from textual.widgets import Static


MIN_DB = -60.0
MAX_DB = 0.0
BAR_WIDTH = 24


def _format_meter(db: float | None) -> str:
    if db is None:
        return "level: --"
    clamped = max(MIN_DB, min(MAX_DB, db))
    ratio = (clamped - MIN_DB) / (MAX_DB - MIN_DB)
    filled = int(ratio * BAR_WIDTH)
    empty = BAR_WIDTH - filled
    bar = "▓" * filled + "░" * empty
    return f"level: {bar} {db:+.1f}dB"


class AudioMeter(Static):
    """A simple terminal audio level meter."""

    level_db: reactive[float | None] = reactive(None)

    def watch_level_db(self, db: float | None) -> None:
        self.update(_format_meter(db))
