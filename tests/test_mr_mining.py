"""Tests for scripts/lincoln_mr_mine.py."""

from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.lincoln_mr_mine import _extract_decision_snippets, _sanitize_filename, mine_pr_decisions


def _comment(body, author="reviewer", created="2026-08-29T12:00:00Z", cid="c1"):
    return {
        "author": {"login": author},
        "body": body,
        "createdAt": created,
        "id": cid,
    }


def test_extract_decision_snippets_finds_keywords():
    text = "This is a decision.\n\nWe agreed to use X.\n\nRandom note."
    snippets = _extract_decision_snippets(text)
    assert len(snippets) == 2
    assert "decision" in snippets[0].lower()
    assert "agreed" in snippets[1].lower()


def test_extract_decision_snippets_ignores_irrelevant():
    assert _extract_decision_snippets("Just a regular comment.") == []


def test_sanitize_filename_creates_safe_slug():
    assert _sanitize_filename("Use JSON Schema!") == "use-json-schema"


def test_mine_pr_decisions_writes_decision_files(tmp_path):
    output_dir = tmp_path / "decisions"
    comments = [
        _comment("We decided to extend the trace file.\n\nNo other changes.", cid="c1"),
        _comment("Looks good.", cid="c2"),
    ]

    with patch("scripts.lincoln_mr_mine._run_gh", side_effect=[comments, []]):
        written = mine_pr_decisions(
            owner="owner", repo="repo", pr_number=22, output_dir=output_dir
        )

    assert len(written) == 1
    assert written[0].name.startswith("pr-22-")
    content = written[0].read_text(encoding="utf-8")
    assert "PR 22 Decision Note" in content
    assert "extend the trace file" in content


def test_mine_pr_decisions_is_idempotent(tmp_path):
    output_dir = tmp_path / "decisions"
    comments = [_comment("Agreed to defer caching.", cid="c1")]

    with patch("scripts.lincoln_mr_mine._run_gh", side_effect=[comments, []]):
        first = mine_pr_decisions(
            owner="owner", repo="repo", pr_number=23, output_dir=output_dir
        )
    with patch("scripts.lincoln_mr_mine._run_gh", side_effect=[comments, []]):
        second = mine_pr_decisions(
            owner="owner", repo="repo", pr_number=23, output_dir=output_dir
        )

    assert len(first) == 1
    assert len(second) == 0


def test_mine_pr_decisions_skips_code_and_secrets(tmp_path):
    output_dir = tmp_path / "decisions"
    comments = [
        _comment("```python\nAPI_KEY=secret123\n```", cid="c1"),
        _comment("Note: keep secrets out of code.", cid="c2"),
    ]

    with patch("scripts.lincoln_mr_mine._run_gh", side_effect=[comments, []]):
        written = mine_pr_decisions(
            owner="owner", repo="repo", pr_number=24, output_dir=output_dir
        )

    assert len(written) == 1
    assert "secret123" not in written[0].read_text(encoding="utf-8")


def test_mine_pr_decisions_requires_output_or_issue():
    with pytest.raises(ValueError):
        mine_pr_decisions(owner="owner", repo="repo", pr_number=25)


def test_mine_pr_decisions_uses_issue_number_default(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    comments = [_comment("Decision: adopt schema.", cid="c1")]

    with patch("scripts.lincoln_mr_mine._run_gh", side_effect=[comments, []]):
        written = mine_pr_decisions(
            owner="owner", repo="repo", pr_number=26, issue_number=70
        )

    assert written[0].parent == Path("issue-70/docs/decisions")
    assert written[0].exists()