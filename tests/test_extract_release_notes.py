"""scripts/extract_release_notes.py 的确定性单元测试。

tmp_path 中合成多种节标题形态的 RELEASE.md fixture;覆盖三种标题形态、
章节边界(同级/更高级标题截断)、缺失章节与缺失文件的错误路径。
"""

import pytest
from scripts import extract_release_notes as ern

RELEASE = """# Lincoln v1.6.0 Release Notes

**Release date:** 2026-08-06

## Highlights

Notes for 1.6.0.

## Full Changelog

- #100 something

---

# Lincoln v1.5.0 Release Notes

## Highlights

Notes for 1.5.0.
"""

MIXED_HEADINGS = """# v2.0.0

Bare level-one notes.

# v1.9.0

Older notes.

## v1.9.1

Level-two notes.

## v1.9.2

More level-two notes.
"""


def make_repo(tmp_path, content=RELEASE):
    (tmp_path / "RELEASE.md").write_text(content, encoding="utf-8")
    return tmp_path


def test_extracts_lincoln_prefixed_section(tmp_path, capsys):
    root = make_repo(tmp_path)
    assert ern.main(["extract_release_notes.py", "1.6.0"], root) == 0
    out = capsys.readouterr().out
    assert "# Lincoln v1.6.0 Release Notes" in out
    assert "Notes for 1.6.0." in out
    assert "- #100 something" in out


def test_extract_stops_at_next_same_level_heading(tmp_path, capsys):
    root = make_repo(tmp_path)
    assert ern.main(["extract_release_notes.py", "1.5.0"], root) == 0
    out = capsys.readouterr().out
    assert "Notes for 1.5.0." in out
    assert "1.6.0" not in out


def test_extracts_bare_level_one_heading(tmp_path, capsys):
    root = make_repo(tmp_path, MIXED_HEADINGS)
    assert ern.main(["extract_release_notes.py", "2.0.0"], root) == 0
    out = capsys.readouterr().out
    assert "# v2.0.0" in out
    assert "Bare level-one notes." in out
    assert "1.9.0" not in out


def test_extracts_level_two_heading_and_stops_at_peer(tmp_path, capsys):
    root = make_repo(tmp_path, MIXED_HEADINGS)
    assert ern.main(["extract_release_notes.py", "1.9.1"], root) == 0
    out = capsys.readouterr().out
    assert "## v1.9.1" in out
    assert "Level-two notes." in out
    assert "1.9.2" not in out


def test_level_one_section_swallows_deeper_headings(tmp_path, capsys):
    """`# v1.9.0` 章节内的 `##` 子标题同属该章节,不应截断。"""
    root = make_repo(tmp_path, MIXED_HEADINGS)
    assert ern.main(["extract_release_notes.py", "1.9.0"], root) == 0
    out = capsys.readouterr().out
    assert "Older notes." in out
    assert "Level-two notes." in out


def test_v_prefix_accepted(tmp_path, capsys):
    root = make_repo(tmp_path)
    assert ern.main(["extract_release_notes.py", "v1.6.0"], root) == 0
    assert "Notes for 1.6.0." in capsys.readouterr().out


def test_version_does_not_match_longer_prefix(tmp_path, capsys):
    """请求 1.9.1 不得命中 `## v1.9.10` 这类更长版本号标题。"""
    content = "## v1.9.10\n\nNotes for 1.9.10.\n"
    root = make_repo(tmp_path, content)
    assert ern.main(["extract_release_notes.py", "1.9.1"], root) == 1
    assert "not found" in capsys.readouterr().err


def test_missing_section_returns_error(tmp_path, capsys):
    root = make_repo(tmp_path)
    assert ern.main(["extract_release_notes.py", "9.9.9"], root) == 1
    err = capsys.readouterr().err
    assert "9.9.9" in err and "RELEASE.md" in err


def test_missing_release_file_returns_error(tmp_path, capsys):
    assert ern.main(["extract_release_notes.py", "1.6.0"], tmp_path) == 1
    assert "RELEASE.md" in capsys.readouterr().err


def test_invalid_semver_returns_usage_error(tmp_path, capsys):
    root = make_repo(tmp_path)
    assert ern.main(["extract_release_notes.py", "1.6"], root) == 2
    assert "invalid semver" in capsys.readouterr().err


def test_missing_version_arg_returns_usage_error(tmp_path):
    assert ern.main(["extract_release_notes.py"], tmp_path) == 2


def test_root_flag(tmp_path, capsys):
    make_repo(tmp_path)
    args = ["extract_release_notes.py", "1.6.0", "--root", str(tmp_path)]
    assert ern.main(args) == 0
    assert "Notes for 1.6.0." in capsys.readouterr().out


def test_real_repo_v160_section_extracts(capsys):
    """真实仓库守护:RELEASE.md 中的历史章节必须始终可抽取。"""
    assert ern.main(["extract_release_notes.py", "1.6.0"], ern.ROOT) == 0
    out = capsys.readouterr().out
    assert "Lincoln v1.6.0" in out
    assert "Lincoln v1.5.0" not in out
