"""Contract tests for Axure-style prototype review annotations (#155)."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.lincoln_prototype_annotations import REQUIRED_STATE_KINDS, validate_annotations

ROOT = Path(__file__).resolve().parents[1]
PAGE_PATH = "pages/prototype/web/search/page.html"


def golden_annotations() -> dict:
    states = {
        "default": ("可搜索", "页面加载完成且用户有搜索权限", "显示最近搜索关键词", "输入框和搜索按钮可用"),
        "loading": ("搜索中", "提交有效关键词", "保留当前关键词，结果区显示搜索中", "搜索按钮显示处理中且不可重复提交"),
        "empty": ("无匹配结果", "没有符合权限和关键词的文档", "结果数为 0", "显示空结果说明和修改关键词入口"),
        "success": ("搜索成功", "返回可读取的有效文档", "显示文档摘要与引用", "用户可打开原文引用"),
        "error": ("搜索失败", "权限校验或搜索服务暂时不可用", "不展示未鉴权内容", "显示失败原因和重试入口"),
    }
    return {
        "overview": {
            "role": "一线客服",
            "scenario": "在工单中查找内部知识",
            "goal": "不切换系统即可找到可信答案",
            "entry": "打开工单详情并进入知识搜索",
            "completion": "打开一条有效原文引用",
            "current_state": "default",
            "flow": "FLOW-001 搜索并打开引用",
        },
        "sections": [{
            "target": "search-panel",
            "title": "搜索区",
            "purpose": "集中完成关键词输入和搜索",
            "content": "关键词输入框、搜索按钮和最近搜索",
        }],
        "interactions": [{
            "target": "search-input",
            "name": "输入关键词",
            "trigger": "点击输入框并输入关键词",
            "response": "显示输入内容；有效关键词使搜索按钮可用",
            "rule": "关键词去除首尾空格，长度为 1–100 个字符",
            "next": "点击搜索后进入搜索中状态",
        }],
        "states": [
            {
                "kind": kind,
                "name": values[0],
                "when": values[1],
                "data": values[2],
                "feedback": values[3],
                "recovery": "点击重试或修改关键词" if kind == "error" else "无需额外恢复",
                "page": PAGE_PATH,
            }
            for kind, values in states.items()
        ],
        "exceptions": [{
            "name": "暂时无法验证权限",
            "trigger": "点击搜索时权限服务暂时不可用",
            "feedback": "显示“暂时无法验证权限，请稍后重试”",
            "recovery": "点击重试；连续失败时联系知识管理员",
            "target": "search-retry",
        }],
        "data": [{
            "name": "关键词",
            "meaning": "用户希望查找的内容",
            "values": "1–100 个字符",
            "empty": "为空时搜索按钮不可用",
            "validation": "自动去除首尾空格",
            "source": "用户输入",
        }],
    }


def write_page(root: Path, annotations: dict | None, *, legacy_hotspot: bool = False) -> Path:
    page = root / PAGE_PATH
    page.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "layout": {"type": "web", "shell": "dashboard", "title": "知识搜索"},
        "components": [{
            "type": "html",
            "uid": "search-panel",
            "props": {"html": '<div data-uid="search-panel"><input data-uid="search-input"><button data-uid="search-retry">重试</button></div>'},
        }],
    }
    if annotations is not None:
        data["annotations"] = annotations
    if legacy_hotspot:
        data["hotspots"] = [{"target": "search-input", "title": "搜索框", "text": "输入关键词"}]
    page.write_text(
        '<!doctype html><html><head><meta name="prototype-base" content="../../../../"></head>'
        '<body><script type="application/json" id="pageData">'
        + json.dumps(data, ensure_ascii=False)
        + "</script></body></html>",
        encoding="utf-8",
    )
    return page


def test_golden_annotation_contract_passes(tmp_path: Path):
    write_page(tmp_path, golden_annotations())
    assert validate_annotations(tmp_path) == []


def test_legacy_single_hotspot_does_not_satisfy_new_contract(tmp_path: Path):
    write_page(tmp_path, None, legacy_hotspot=True)
    errors = validate_annotations(tmp_path)
    assert "ANNOTATIONS_MISSING" in "\n".join(errors)


@pytest.mark.parametrize("kind", sorted(REQUIRED_STATE_KINDS))
def test_every_required_state_must_be_enumerated(tmp_path: Path, kind: str):
    annotations = golden_annotations()
    annotations["states"] = [state for state in annotations["states"] if state["kind"] != kind]
    write_page(tmp_path, annotations)
    errors = validate_annotations(tmp_path)
    assert any(error.startswith(f"STATE_MISSING: {kind}") for error in errors)


def test_not_applicable_state_requires_business_reason(tmp_path: Path):
    annotations = golden_annotations()
    annotations["states"] = [state for state in annotations["states"] if state["kind"] != "empty"]
    annotations["states"].append({"kind": "empty", "not_applicable": True})
    write_page(tmp_path, annotations)
    assert any(error.startswith("STATE_NA_REASON: empty") for error in validate_annotations(tmp_path))


def test_annotation_target_must_exist(tmp_path: Path):
    annotations = golden_annotations()
    annotations["sections"][0]["target"] = "missing-element"
    write_page(tmp_path, annotations)
    assert any("ANNOTATION_TARGET_MISSING: missing-element" in error for error in validate_annotations(tmp_path))


def test_exception_requires_recovery_path(tmp_path: Path):
    annotations = golden_annotations()
    annotations["exceptions"][0]["recovery"] = ""
    write_page(tmp_path, annotations)
    assert any("EXCEPTION_FIELD: recovery" in error for error in validate_annotations(tmp_path))


def test_technical_narrative_is_rejected(tmp_path: Path):
    annotations = golden_annotations()
    annotations["exceptions"][0]["feedback"] = "API 返回 HTTP 500，检查 JSON"
    write_page(tmp_path, annotations)
    assert any("TECHNICAL_NARRATIVE" in error for error in validate_annotations(tmp_path))


def test_current_state_must_be_catalogued(tmp_path: Path):
    annotations = golden_annotations()
    annotations["overview"]["current_state"] = "disabled"
    write_page(tmp_path, annotations)
    assert any(error.startswith("CURRENT_STATE_UNKNOWN: disabled") for error in validate_annotations(tmp_path))


def test_structured_template_exposes_annotation_drawer_and_presentation_mode():
    template = (ROOT / ".claude" / "templates" / "issue-package" / "page-prototype-structured.html.tpl").read_text(encoding="utf-8")
    runtime = (ROOT / ".claude" / "templates" / "issue-package" / "assets" / "prototype.js").read_text(encoding="utf-8")
    assert "initAnnotations" in template
    assert "data.annotations" in template
    assert "lc-annotation-panel" in runtime
    assert "annotationShow" in runtime
    assert "annotationNext" in runtime
    assert "function annotationEscape" in runtime
    assert "hotspotBadgeContainer" in runtime
    assert "container.appendChild(badge)" in runtime


def test_data_free_page_must_explain_why_data_is_not_applicable(tmp_path: Path):
    annotations = golden_annotations()
    annotations["data"] = []
    write_page(tmp_path, annotations)
    assert any("DATA_EMPTY" in error for error in validate_annotations(tmp_path))

    annotations["data_not_applicable"] = "纯导航页不承载业务数据"
    write_page(tmp_path, annotations)
    assert validate_annotations(tmp_path) == []
