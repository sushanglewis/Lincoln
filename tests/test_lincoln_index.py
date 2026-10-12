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


def test_extract_html_meta_machine_tags(tmp_path: Path):
    page = write_html(
        tmp_path,
        "pages/docs/c.html",
        '<meta name="doc-title" content="说明">'
        '<meta name="nav-label" content="短名">'
        '<meta name="nav-group" content="Docs">'
        '<meta name="doc-uid" content="c">'
        '<meta name="doc-version" content="v2.0">',
    )
    meta = extract_html_meta(page)
    assert meta["title"] == "说明"
    assert meta["nav_label"] == "短名"
    assert meta["nav_group"] == "Docs"
    assert meta["uid"] == "c"
    assert meta["version"] == "v2.0"
    assert meta["markdown"] == ""


def test_extract_html_meta_embeds_markdown_for_doc_pages(tmp_path: Path):
    page = write_html(
        tmp_path,
        "pages/docs/prd.html",
        '<meta name="doc-title" content="PRD">'
        '<script type="text/markdown" id="docSource">\n# PRD\n\n## 背景\n\n内容\n</script>',
    )
    meta = extract_html_meta(page)
    assert "## 背景" in meta["markdown"]
    assert "内容" in meta["markdown"]


def test_extract_html_meta_skips_markdown_for_prototype_pages(tmp_path: Path):
    page = write_html(
        tmp_path,
        "pages/prototype/web/main/page.html",
        '<meta name="doc-title" content="主界面"><div class="window"></div>',
    )
    meta = extract_html_meta(page)
    assert meta["markdown"] == ""


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


def test_build_package_data_embeds_markdown_in_nav_payload(tmp_path: Path):
    write_html(
        tmp_path,
        "issue-99/pages/docs/prd.html",
        '<meta name="nav-label" content="PRD">'
        '<script type="text/markdown" id="docSource">\n<!-- version: v1.0 -->\n\n# PRD\n\n## 目标\n\n做一件事\n</script>',
    )
    write_html(
        tmp_path,
        "issue-99/pages/prototype/web/dashboard/page.html",
        '<meta name="nav-label" content="仪表盘">',
    )
    state = {
        "schema_version": "2.0.0",
        "current_run": {"issue_number": "99", "current_stage": "product-prototype"},
        "nodes": [],
    }
    data = build_package_data(state, "issue-99", project_root=tmp_path)
    items = {item["path"]: item for group in data["nav"] for item in group["items"]}
    doc_item = items["pages/docs/prd.html"]
    assert "## 目标" in doc_item["markdown"]
    proto_item = items["pages/prototype/web/dashboard/page.html"]
    assert proto_item["markdown"] == ""


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


def test_build_package_data_archive_group_is_flagged_and_last(tmp_path: Path):
    write_html(
        tmp_path,
        "issue-99/pages/docs/prd.html",
        '<meta name="nav-group" content="Docs">'
        '<meta name="nav-label" content="PRD">',
    )
    write_html(
        tmp_path,
        "issue-99/pages/docs/decisions.html",
        '<meta name="nav-group" content="归档">'
        '<meta name="nav-label" content="决策归档">',
    )
    write_html(
        tmp_path,
        "issue-99/pages/docs/feasibility.html",
        '<meta name="nav-group" content="归档">'
        '<meta name="nav-label" content="可行性">',
    )
    state = {
        "schema_version": "2.0.0",
        "current_run": {"issue_number": "99", "current_stage": "product-design-docs"},
        "nodes": [],
    }
    data = build_package_data(state, "issue-99", project_root=tmp_path)

    items = {item["path"]: item for group in data["nav"] for item in group["items"]}
    assert items["pages/docs/decisions.html"]["archived"] is True
    assert items["pages/docs/feasibility.html"]["archived"] is True
    assert items["pages/docs/prd.html"]["archived"] is False

    group_names = [group["group"] for group in data["nav"]]
    assert group_names[-1] == "归档"
    assert group_names.count("归档") == 1
