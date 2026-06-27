import json
from pathlib import Path

import pytest
from freezegun import freeze_time

from record_interview.metadata import build_metadata, read_metadata, update_recording_complete


@freeze_time("2026-06-27T10:00:00Z")
def test_build_metadata(tmp_path):
    meta = build_metadata(
        workspace_root=tmp_path,
        session_id="2026-06-27-stakeholder-checkout",
        design_id="checkout-redesign",
        topic="结算流程 redesign 需求访谈",
        branch="lincoln/2026-06-27-stakeholder-checkout-checkout-redesign",
    )
    assert meta["session_id"] == "2026-06-27-stakeholder-checkout"
    assert meta["design_id"] == "checkout-redesign"
    assert meta["topic"] == "结算流程 redesign 需求访谈"
    assert meta["branch"] == "lincoln/2026-06-27-stakeholder-checkout-checkout-redesign"
    assert meta["recording_file"] == "recordings/2026-06-27-stakeholder-checkout.m4a"
    assert meta["started_at"] == "2026-06-27T10:00:00Z"
    assert meta["source"] == "lincoln-record-interview-cli"


def test_read_metadata_returns_none_when_missing(tmp_path):
    assert read_metadata(tmp_path, "2026-06-27-stakeholder-checkout") is None


def test_read_metadata_reads_existing(tmp_path):
    meta_path = tmp_path / "interviews" / "2026-06-27-stakeholder-checkout" / "metadata.json"
    meta_path.parent.mkdir(parents=True)
    meta_path.write_text(json.dumps({"session_id": "x"}), encoding="utf-8")
    assert read_metadata(tmp_path, "2026-06-27-stakeholder-checkout") == {"session_id": "x"}


@freeze_time("2026-06-27T10:45:00Z")
def test_update_recording_complete(tmp_path):
    meta_path = tmp_path / "interviews" / "2026-06-27-stakeholder-checkout" / "metadata.json"
    meta_path.parent.mkdir(parents=True)
    meta = build_metadata(
        workspace_root=tmp_path,
        session_id="2026-06-27-stakeholder-checkout",
        design_id="checkout-redesign",
        topic="t",
        branch="b",
    )
    meta_path.write_text(json.dumps(meta), encoding="utf-8")

    updated = update_recording_complete(tmp_path, "2026-06-27-stakeholder-checkout", duration_seconds=2700)
    assert updated["ended_at"] == "2026-06-27T10:45:00Z"
    assert updated["duration_seconds"] == 2700
