import pytest

from record_interview.tui.widgets.audio_meter import _format_meter


def test_format_meter_shows_db_and_bar():
    text = _format_meter(-30.0)
    assert "-30.0dB" in text
    assert "▓" in text
    assert "░" in text


def test_format_meter_clamps_extremes():
    low = _format_meter(-100.0)
    assert "-100.0dB" in low
    high = _format_meter(10.0)
    assert "10.0dB" in high


def test_format_meter_handles_none():
    assert _format_meter(None) == "level: --"


@pytest.mark.asyncio
async def test_audio_meter_reactive_update():
    from record_interview.tui.widgets.audio_meter import AudioMeter

    meter = AudioMeter()
    meter.level_db = -20.0
    assert "-20.0dB" in str(meter.render())
