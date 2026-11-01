"""Deterministic PRD core-v2 quality contract and legacy compatibility tests (issue-143)."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "lincoln_prd_quality.py"
FIXTURES = ROOT / "tests" / "fixtures" / "prd-quality"
PROMPT = ROOT / ".claude" / "skills" / "clarify-requirements" / "prompts" / "main.md"
STANDARD = ROOT / "docs" / "prd-quality-standard.md"

spec = importlib.util.spec_from_file_location("lincoln_prd_quality", SCRIPT)
quality = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = quality
spec.loader.exec_module(quality)


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _codes(result) -> set[str]:
    return {issue.code for issue in result.issues}


def test_core_v2_golden_is_complete_and_passes():
    result = quality.validate_text(_fixture("core-v2-golden.md"))

    assert result.ok, "\n".join(issue.format() for issue in result.issues)
    assert result.mode == "core-v2"


def test_legacy_13_sections_keep_structure_only_compatibility():
    # The dashes deliberately prove that legacy mode does not apply new semantic gates.
    result = quality.validate_text(_fixture("legacy-13-sections.md"))

    assert result.ok, "\n".join(issue.format() for issue in result.issues)
    assert result.mode == "legacy"


def test_legacy_still_rejects_a_missing_required_chapter():
    text = _fixture("legacy-13-sections.md").replace("## 6. 功能拆解\n-\n", "")
    result = quality.validate_text(text)

    assert not result.ok
    assert "MISSING_SECTION" in _codes(result)
    assert any(issue.section == "功能拆解" for issue in result.issues)


@pytest.mark.parametrize(
    ("fixture", "expected_code"),
    (
        ("core-v2-empty-section.md", "EMPTY_SECTION"),
        ("core-v2-placeholder.md", "PLACEHOLDER_SECTION"),
        ("core-v2-missing-metric.md", "METRIC_VALUES"),
        ("core-v2-missing-traceability.md", "ACCEPTANCE_TRACE"),
        ("core-v2-invalid-requirement-id.md", "REQ_ID_FORMAT"),
        ("core-v2-duplicate-acceptance-id.md", "DUPLICATE_AC_ID"),
    ),
)
def test_core_v2_counterexamples_fail_with_actionable_codes(fixture, expected_code):
    result = quality.validate_text(_fixture(fixture))

    assert not result.ok
    assert expected_code in _codes(result)
    assert all(issue.message for issue in result.issues)


def test_core_v2_rejects_an_empty_table_as_empty_content():
    text = _fixture("core-v2-golden.md").replace(
        "为拥有 200 篇以上内部文档的企业客服团队提供带权限继承的答案搜索。首版通过统一搜索入口和答案引用，减少客服跨系统查找资料的时间，并以搜索成功率和平均查找时长衡量业务结果。",
        "| 项目 | 内容 |\n|---|---|",
    )

    assert "EMPTY_SECTION" in _codes(quality.validate_text(text))


def test_core_v2_requires_explicit_non_goals():
    text = _fixture("core-v2-golden.md").replace("### 非目标", "### 排除项")

    assert "NON_GOALS" in _codes(quality.validate_text(text))


def test_core_v2_requires_every_metric_column():
    text = _fixture("core-v2-golden.md").replace(
        "| 指标 | 基线 | 目标值 | 时间窗 | 口径/来源 |",
        "| 指标 | 基线 | 期望 | 时间窗 | 口径/来源 |",
    )

    assert "METRIC_FIELDS" in _codes(quality.validate_text(text))


def test_ids_must_use_uppercase_contract():
    text = _fixture("core-v2-golden.md").replace("REQ-001", "req-001")

    assert "REQ_ID_FORMAT" in _codes(quality.validate_text(text))


def test_explicit_core_mode_requires_marker_and_version():
    text = _fixture("core-v2-golden.md")
    text = text.replace("<!-- prd-contract: core-v2 -->\n", "")
    text = text.replace("<!-- version: v1.0 -->\n", "")
    result = quality.validate_text(text, mode="core-v2")

    assert {"MISSING_CONTRACT_MARKER", "MISSING_VERSION_MARKER"} <= _codes(result)


def test_unmarked_document_does_not_accidentally_enable_semantic_checks():
    assert quality.validate_text(_fixture("legacy-13-sections.md"), mode="auto").mode == "legacy"


def test_rendered_html_uses_embedded_markdown_source():
    html = (
        "<!doctype html><html><body>"
        '<script type="text/markdown" id="docSource">\n'
        + _fixture("core-v2-golden.md")
        + "\n</script></body></html>"
    )

    assert quality.validate_text(html).ok


def test_validation_is_deterministic():
    text = _fixture("core-v2-missing-traceability.md")

    assert quality.validate_text(text).as_dict() == quality.validate_text(text).as_dict()


def test_prompt_generates_all_15_core_v2_chapters_and_shared_paths():
    prompt = PROMPT.read_text(encoding="utf-8")

    assert "<!-- prd-contract: core-v2 -->" in prompt
    for index, section in enumerate(quality.CORE_V2_SECTIONS, start=1):
        assert f"`## {index}. {section}`" in prompt
    assert "REQ-001" in prompt
    assert "AC-001" in prompt
    assert "{process_slug}/pages/docs/prd-traceability.yaml" in prompt
    assert "{process_slug}/pages/docs/prd-review.yaml" in prompt
    assert "scripts/lincoln_prd_quality.py" in prompt


def test_standard_documents_the_same_15_chapters_and_reader_responsibilities():
    standard = STANDARD.read_text(encoding="utf-8")

    for section in quality.CORE_V2_SECTIONS:
        assert section in standard
    for reader in ("PM", "设计", "研发", "QA", "运营"):
        assert reader in standard
    assert "{process_slug}/pages/docs/prd-traceability.yaml" in standard
    assert "{process_slug}/pages/docs/prd-review.yaml" in standard


def test_cli_passes_golden_fixture():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(FIXTURES / "core-v2-golden.md")],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "PASS" in result.stdout
    assert "core-v2" in result.stdout


def test_cli_failure_names_chapter_code_and_fix():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(FIXTURES / "core-v2-missing-metric.md")],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "METRIC_VALUES" in result.stderr
    assert "目标与成功指标" in result.stderr
    assert "fill baseline, target and time window" in result.stderr


def test_cli_missing_file_is_actionable(tmp_path):
    missing = tmp_path / "missing-prd.md"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(missing)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "PRD file not found" in result.stderr
    assert "Pass an existing .md or .html file" in result.stderr


def test_cli_json_is_stable_and_machine_readable():
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(FIXTURES / "core-v2-empty-section.md"),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["mode"] == "core-v2"
    assert payload["issues"][0]["code"] == "EMPTY_SECTION"
