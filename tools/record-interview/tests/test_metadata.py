import json
from pathlib import Path
from typing import Any

import pytest
from freezegun import freeze_time

from record_interview.metadata import (
    build_metadata,
    mark_recording_complete,
    read_metadata,
    update_recording_complete,
    write_metadata,
)


def make_sample_metadata() -> dict[str, Any]:
    return {
        "session_id": "2026-06-27-stakeholder-checkout",
        "design_id": "checkout-redesign",
        "topic": "结算流程 redesign 需求访谈",
        "branch": "lincoln/2026-06-27-stakeholder-checkout-checkout-redesign",
        "recording_file": "recordings/2026-06-27-stakeholder-checkout.m4a",
        "started_at": "2026-06-27T10:00:00Z",
        "ended_at": None,
        "duration_seconds": None,
        "source": "lincoln-record-interview-cli",
        "created_by": "lincoln-record-interview-cli",
    }


@freeze_time("2026-06-27T10:00:00Z")
def test_build_metadata():
    meta = build_metadata(
        session_id="2026-06-27-stakeholder-checkout",
        design_id="checkout-redesign",
        topic="结算流程 redesign 需求访谈",
        branch="lincoln/2026-06-27-stakeholder-checkout-checkout-redesign",
        started_at="2026-06-27T10:00:00Z",
    )
    assert meta["session_id"] == "2026-06-27-stakeholder-checkout"
    assert meta["design_id"] == "checkout-redesign"
    assert meta["topic"] == "结算流程 redesign 需求访谈"
    assert meta["branch"] == "lincoln/2026-06-27-stakeholder-checkout-checkout-redesign"
    assert meta["recording_file"] == "recordings/2026-06-27-stakeholder-checkout.m4a"
    assert meta["started_at"] == "2026-06-27T10:00:00Z"
    assert meta["ended_at"] is None
    assert meta["duration_seconds"] is None
    assert meta["created_by"] == "lincoln-record-interview-cli"
    assert meta["source"] == "lincoln-record-interview-cli"


def test_read_metadata_returns_none_when_missing(tmp_path):
    assert read_metadata(tmp_path, "2026-06-27-stakeholder-checkout") is None


def test_read_metadata_reads_existing(tmp_path):
    meta_path = tmp_path / "interviews" / "2026-06-27-stakeholder-checkout" / "metadata.json"
    meta_path.parent.mkdir(parents=True)
    meta_path.write_text(json.dumps(make_sample_metadata()), encoding="utf-8")
    assert read_metadata(tmp_path, "2026-06-27-stakeholder-checkout") == make_sample_metadata()


def test_read_metadata_corrupted_raises_value_error(tmp_path):
    meta_path = tmp_path / "interviews" / "2026-06-27-stakeholder-checkout" / "metadata.json"
    meta_path.parent.mkdir(parents=True)
    meta_path.write_text("not json", encoding="utf-8")
    with pytest.raises(ValueError, match="corrupted metadata for 2026-06-27-stakeholder-checkout"):
        read_metadata(tmp_path, "2026-06-27-stakeholder-checkout")


@freeze_time("2026-06-27T10:45:00Z")
def test_mark_recording_complete():
    meta = make_sample_metadata()
    updated = mark_recording_complete(meta, duration_seconds=2700)
    assert updated["ended_at"] == "2026-06-27T10:45:00Z"
    assert updated["duration_seconds"] == 2700
    assert updated["started_at"] == meta["started_at"]


@freeze_time("2026-06-27T10:45:00Z")
def test_update_recording_complete(tmp_path):
    meta_path = tmp_path / "interviews" / "2026-06-27-stakeholder-checkout" / "metadata.json"
    meta_path.parent.mkdir(parents=True)
    meta = build_metadata(
        session_id="2026-06-27-stakeholder-checkout",
        design_id="checkout-redesign",
        topic="t",
        branch="b",
    )
    meta_path.write_text(json.dumps(meta), encoding="utf-8")

    updated = update_recording_complete(tmp_path, "2026-06-27-stakeholder-checkout", duration_seconds=2700)
    assert updated["ended_at"] == "2026-06-27T10:45:00Z"
    assert updated["duration_seconds"] == 2700
    assert read_metadata(tmp_path, "2026-06-27-stakeholder-checkout") == updated


def test_write_metadata_roundtrip(tmp_path):
    meta = build_metadata(
        session_id="2026-06-27-stakeholder-checkout",
        design_id="checkout-redesign",
        topic="结算流程 redesign 需求访谈",
        branch="lincoln/2026-06-27-stakeholder-checkout-checkout-redesign",
    )
    write_metadata(tmp_path, "2026-06-27-stakeholder-checkout", meta)
    read_back = read_metadata(tmp_path, "2026-06-27-stakeholder-checkout")
    assert read_back == meta
