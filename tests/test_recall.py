"""Tests for scripts/lincoln_recall.py."""

from pathlib import Path

import pytest

from scripts.lincoln_recall import recall


@pytest.fixture
def knowledge_dir(tmp_path):
    root = tmp_path / "knowledge"
    root.mkdir()
    (root / "01-intro.md").write_text("Lincoln is a framework for AI-Native R&D.", encoding="utf-8")
    (root / "02-friction.md").write_text(
        "Friction-based learning captures tool failures and retries.", encoding="utf-8"
    )
    (root / "03-security.md").write_text(
        "Security analyzer blocks rm -rf and file writes outside the process package.",
        encoding="utf-8",
    )
    return root


def test_recall_returns_top_k_by_keywords(knowledge_dir):
    result = recall("friction learning failures", knowledge_dir=knowledge_dir, top_k=2)
    assert result["method"] == "keywords"
    assert len(result["docs"]) <= 2
    assert any("friction" in doc["path"] for doc in result["docs"])


def test_recall_returns_empty_when_no_match(knowledge_dir):
    result = recall("quantum computing", knowledge_dir=knowledge_dir, top_k=3)
    assert result["docs"] == []


def test_recall_falls_back_to_keywords_when_embedding_unavailable(knowledge_dir):
    result = recall("security analyzer blocks rm", knowledge_dir=knowledge_dir, top_k=3)
    assert result["method"] == "keywords"
    assert any("security" in doc["path"] for doc in result["docs"])


def test_recall_no_embedding_flag(knowledge_dir):
    result = recall("Lincoln framework", knowledge_dir=knowledge_dir, top_k=1, use_embedding=False)
    assert result["method"] == "keywords"
    assert len(result["docs"]) == 1


def test_recall_handles_missing_knowledge_dir(tmp_path):
    result = recall("Lincoln", knowledge_dir=tmp_path / "missing", top_k=3)
    assert result["docs"] == []


def test_recall_ignores_low_scores(knowledge_dir):
    result = recall("totally unrelated topic xyz", knowledge_dir=knowledge_dir, top_k=3)
    assert result["docs"] == []


def test_recall_main_cli_json(knowledge_dir, capsys):
    from scripts.lincoln_recall import main

    assert main(["--query", "friction learning", "--knowledge-dir", str(knowledge_dir), "--top-k", "1"]) == 0
    captured = capsys.readouterr()
    assert "friction" in captured.out


def test_recall_main_cli_markdown(knowledge_dir, capsys):
    from scripts.lincoln_recall import main

    assert (
        main(
            [
                "--query",
                "security",
                "--knowledge-dir",
                str(knowledge_dir),
                "--format",
                "markdown",
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    assert "# 相关知识" in captured.out
    assert "security" in captured.out