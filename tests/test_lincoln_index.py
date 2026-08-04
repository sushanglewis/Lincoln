"""Tests for scripts/lincoln_index.py."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.lincoln_index import build_package_data, extract_html_meta


def write_html(root: Path, rel: str, content: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_extract_html_meta_nav_label_priority(tmp_path: Path):
    page = write_html(
        tmp_path,
        "pages/docs/a.html",
        '<meta name="nav-label" content="短标签">'
        '<meta name="doc-title" content="完整标题">'
        "<title>HTML Title</title>",
    )
    meta = extract_html_meta(page)
    assert meta["nav_label"] == "短标签"
    assert meta["title"] == "完整标题"


def test_extract_html_meta_falls_back_to_title(tmp_path: Path):
    page = write_html(
        tmp_path,
        "pages/docs/b.html",
        '<meta name="doc-title" content="Doc Title">'
        "<title>HTML Title</title>",
    )
    meta = extract_html_meta(page)
    assert meta["nav_label"] == ""
    assert meta["title"] == "Doc Title"


def test_extract_html_meta_annotation_tags(tmp_path: Path):
    page = write_html(
        tmp_path,
        "pages/docs/c.html",
        '<meta name="doc-purpose" content="说明">'
        '<meta name="doc-layout" content="顶部 | 左侧 | 主内容">'
        '<meta name="doc-fields" content="A — 文本 | B — 数字">'
        '<meta name="doc-stories" content="用户故事一 | 用户故事二">'
        '<meta name="doc-rules" content="规则一 | 规则二">'
        '<meta name="doc-boundaries" content="空态 | 最大长度">'
        '<meta name="doc-exceptions" content="网络失败 | 无权限">'
        '<meta name="doc-refs" content="PRD #1 | flows.html">',
    )
    meta = extract_html_meta(page)
    assert meta["purpose"] == "说明"
    assert meta["layout"] == "顶部 | 左侧 | 主内容"
    assert meta["fields"] == ["A — 文本", "B — 数字"]
    assert meta["stories"] == ["用户故事一", "用户故事二"]
    assert meta["rules"] == ["规则一", "规则二"]
    assert meta["boundaries"] == ["空态", "最大长度"]
    assert meta["exceptions"] == ["网络失败", "无权限"]
    assert meta["refs"] == ["PRD #1", "flows.html"]


def test_extract_html_meta_missing_lists_are_empty(tmp_path: Path):
    page = write_html(tmp_path, "pages/docs/d.html", "")
    meta = extract_html_meta(page)
    assert meta["fields"] == []
    assert meta["stories"] == []
    assert meta["rules"] == []
    assert meta["boundaries"] == []
    assert meta["exceptions"] == []
    assert meta["refs"] == []


def test_build_package_data_uses_nav_label_for_label(tmp_path: Path):
    write_html(
        tmp_path,
        "issue-99/pages/docs/prefixed.html",
        '<meta name="nav-label" content="短名">'
        '<meta name="doc-title" content="EAIC 原型 · 文档预览 · 完整名">',
    )
    write_html(
        tmp_path,
        "issue-99/pages/docs/fallback.html",
        '<meta name="doc-title" content="Fallback Title">',
    )
    state = {
        "schema_version": "2.0.0",
        "current_run": {"issue_number": "99", "current_stage": "product-prototype"},
        "nodes": [],
    }
    data = build_package_data(state, "issue-99", project_root=tmp_path)
    items = {item["path"]: item for group in data["nav"] for item in group["items"]}
    assert items["pages/docs/prefixed.html"]["label"] == "短名"
    assert items["pages/docs/prefixed.html"]["title"] == "EAIC 原型 · 文档预览 · 完整名"
    assert items["pages/docs/fallback.html"]["label"] == "Fallback Title"


def test_build_package_data_passes_through_annotations(tmp_path: Path):
    write_html(
        tmp_path,
        "issue-99/pages/prototype/app/main.html",
        '<meta name="doc-purpose" content="主界面">'
        '<meta name="doc-layout" content="顶部 | 左侧 | 主内容">'
        '<meta name="doc-fields" content="A | B">'
        '<meta name="doc-boundaries" content="空态">'
        '<meta name="doc-exceptions" content="网络失败">',
    )
    state = {
        "schema_version": "2.0.0",
        "current_run": {"issue_number": "99", "current_stage": "product-prototype"},
        "nodes": [],
    }
    data = build_package_data(state, "issue-99", project_root=tmp_path)
    items = {item["path"]: item for group in data["nav"] for item in group["items"]}
    item = items["pages/prototype/app/main.html"]
    assert item["purpose"] == "主界面"
    assert item["layout"] == "顶部 | 左侧 | 主内容"
    assert item["fields"] == ["A", "B"]
    assert item["boundaries"] == ["空态"]
    assert item["exceptions"] == ["网络失败"]


def test_build_package_data_label_falls_back_to_stem(tmp_path: Path):
    write_html(tmp_path, "issue-99/pages/docs/untitled.html", "")
    state = {
        "schema_version": "2.0.0",
        "current_run": {"issue_number": "99", "current_stage": "clarify"},
        "nodes": [],
    }
    data = build_package_data(state, "issue-99", project_root=tmp_path)
    items = {item["path"]: item for group in data["nav"] for item in group["items"]}
    assert items["pages/docs/untitled.html"]["label"] == "untitled"
    assert items["pages/docs/untitled.html"]["title"] == "untitled"
