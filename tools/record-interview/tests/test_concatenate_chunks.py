from unittest.mock import MagicMock

import pytest

from record_interview.recorder import (
    RecordingError,
    concatenate_chunks,
    get_chunk_paths,
)


def test_get_chunk_paths_sorts_naturally(tmp_path):
    (tmp_path / "chunk_001.m4a").write_bytes(b"1")
    (tmp_path / "chunk_010.m4a").write_bytes(b"10")
    (tmp_path / "chunk_002.m4a").write_bytes(b"2")
    paths = get_chunk_paths(tmp_path)
    assert [p.name for p in paths] == [
        "chunk_001.m4a",
        "chunk_002.m4a",
        "chunk_010.m4a",
    ]


def test_concatenate_chunks_skips_when_no_chunks(tmp_path):
    chunks_dir = tmp_path / "chunks"
    chunks_dir.mkdir()
    result = concatenate_chunks(chunks_dir, tmp_path / "out.m4a")
    assert result is None


def test_concatenate_chunks_builds_ffmpeg_concat_command(mocker, tmp_path):
    chunks_dir = tmp_path / "chunks"
    chunks_dir.mkdir()
    (chunks_dir / "chunk_000.m4a").write_bytes(b"fake0")
    (chunks_dir / "chunk_001.m4a").write_bytes(b"fake1")

    output_path = tmp_path / "recordings" / "test.m4a"
    run_mock = mocker.patch(
        "record_interview.recorder.subprocess.run",
        return_value=MagicMock(returncode=0, stderr=""),
    )

    result = concatenate_chunks(chunks_dir, output_path)

    assert result == output_path
    assert run_mock.called
    cmd = run_mock.call_args.args[0]
    assert cmd[0] == "ffmpeg"
    assert "concat" in cmd
    assert "-safe" in cmd
    assert str(output_path) in cmd

    list_path = chunks_dir / "concat_list.txt"
    assert list_path.exists()
    content = list_path.read_text(encoding="utf-8")
    assert "file 'chunk_000.m4a'" in content
    assert "file 'chunk_001.m4a'" in content


def test_concatenate_chunks_raises_on_ffmpeg_failure(mocker, tmp_path):
    chunks_dir = tmp_path / "chunks"
    chunks_dir.mkdir()
    (chunks_dir / "chunk_000.m4a").write_bytes(b"fake")

    mocker.patch(
        "record_interview.recorder.subprocess.run",
        return_value=MagicMock(returncode=1, stderr="concat failed"),
    )

    with pytest.raises(RecordingError, match="concatenation failed"):
        concatenate_chunks(chunks_dir, tmp_path / "out.m4a")
