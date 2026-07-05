from pathlib import Path
from unittest.mock import MagicMock

import pytest

from record_interview.volume import VolumeAnalyzer, analyze_chunk_loudness


def test_analyze_chunk_loudness_parses_ffmpeg_output(mocker):
    stderr = """
    [Parsed_volumedetect_0 @ 0x...] n_samples: 12345
    [Parsed_volumedetect_0 @ 0x...] mean_volume: -16.50 dB
    [Parsed_volumedetect_0 @ 0x...] max_volume: -1.20 dB
    """
    mocker.patch(
        "record_interview.volume.subprocess.run",
        return_value=MagicMock(returncode=0, stderr=stderr),
    )
    result = analyze_chunk_loudness(Path("/tmp/chunk.m4a"))
    assert result == pytest.approx((-16.50, -1.20))


def test_analyze_chunk_loudness_returns_none_on_missing_values(mocker):
    mocker.patch(
        "record_interview.volume.subprocess.run",
        return_value=MagicMock(returncode=0, stderr=""),
    )
    assert analyze_chunk_loudness(Path("/tmp/chunk.m4a")) is None


def test_analyze_chunk_loudness_returns_none_when_ffmpeg_missing(mocker):
    mocker.patch(
        "record_interview.volume.subprocess.run",
        side_effect=FileNotFoundError("ffmpeg"),
    )
    assert analyze_chunk_loudness(Path("/tmp/chunk.m4a")) is None


def test_volume_analyzer_emits_level_for_new_chunk(mocker, tmp_path):
    (tmp_path / "chunk_000.m4a").write_bytes(b"fake")
    callback = mocker.Mock()
    analyzer = VolumeAnalyzer(tmp_path, on_level=callback, poll_interval=0.05)
    mocker.patch(
        "record_interview.volume.analyze_chunk_loudness",
        return_value=(-20.0, -5.0),
    )
    analyzer.start()
    try:
        # Wait long enough for the analyzer to pick up the new chunk.
        import time

        time.sleep(0.5)
    finally:
        analyzer.stop()
    assert callback.called
    assert callback.call_args.args[0] == pytest.approx(-5.0)
