"""Tests for lc-workflow PRD hygiene and cross-validation exit checks (issue-129)."""

from pathlib import Path

from .conftest import run_validator

PRD_13_SECTIONS = (
    "## 1. 版本说明\n-\n"
    "## 2. 修订记录\n-\n"
    "## 3. 功能列表\n-\n"
    "## 4. 需求背景\n-\n"
    "## 5. 用户故事\n-\n"
    "## 6. 功能拆解\n-\n"
    "## 7. 业务流程图\n-\n"
    "## 8. 验收标准\n-\n"
    "## 9. 业务规则\n-\n"
    "## 10. 非功能需求\n-\n"
    "## 11. 关联系统/接口\n-\n"
    "## 12. 相关产物链接\n-\n"
    "## 13. 风险与开放问题\n-\n"
)


def _doc_source(markdown: str) -> str:
    return f'<script type="text/markdown" id="docSource">\n{markdown}\n</script>\n'


def _write_prd(root: Path, content: str, version: str = "v1.2") -> Path:
    prd = root / "lc-test" / "pages" / "docs" / "prd.html"
    prd.parent.mkdir(parents=True, exist_ok=True)
    prd.write_text(
        _doc_source(f"<!-- version: {version} -->\n\n{content}"), encoding="utf-8"
    )
    return prd


def _write_report(root: Path, content: str, version: str = "v1.2") -> Path:
    report = root / "lc-test" / "pages" / "docs" / "prd-cross-validation.html"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        _doc_source(f"<!-- version: {version} -->\n\n{content}"), encoding="utf-8"
    )
    return report


_PASS_REPORT = (
    "# PRD 交叉验证报告\n\n"
    "| 场景 | PRD 答案 | 闭环方式 |\n|---|---|---|\n"
    "| 正常下单 | 业务规则 9.1 | PM 决策接受 |\n\n"
    "<!-- cross-validation: pass prd-version: v1.2 -->\n"
)


class TestPrdContentHygiene:
    def test_passes_on_clean_prd(self, tmp_project):
        _write_prd(tmp_project, "# PRD\n\n" + PRD_13_SECTIONS)
        assert run_validator(tmp_project, "prd_content_hygiene", "lc-test/pages/docs/prd.html") == 0

    def test_fails_on_process_phrase(self, tmp_project):
        _write_prd(tmp_project, "# PRD\n\n" + PRD_13_SECTIONS + "\n> 本节待确认\n")
        assert run_validator(tmp_project, "prd_content_hygiene", "lc-test/pages/docs/prd.html") == 1

    def test_fails_on_tech_heading(self, tmp_project):
        _write_prd(tmp_project, "# PRD\n\n" + PRD_13_SECTIONS + "\n## 技术方案\n用 Redis。\n")
        assert run_validator(tmp_project, "prd_content_hygiene", "lc-test/pages/docs/prd.html") == 1

    def test_fails_when_prd_missing(self, tmp_project):
        assert run_validator(tmp_project, "prd_content_hygiene", "lc-test/pages/docs/prd.html") == 1


class TestPrdCrossValidated:
    def test_passes_with_matching_pass_marker(self, tmp_project):
        _write_prd(tmp_project, "# PRD\n\n" + PRD_13_SECTIONS)
        _write_report(tmp_project, _PASS_REPORT)
        assert (
            run_validator(tmp_project, "prd_cross_validated", "lc-test/pages/docs/prd-cross-validation.html")
            == 0
        )

    def test_fails_when_report_missing(self, tmp_project):
        _write_prd(tmp_project, "# PRD\n\n" + PRD_13_SECTIONS)
        assert (
            run_validator(tmp_project, "prd_cross_validated", "lc-test/pages/docs/prd-cross-validation.html")
            == 1
        )

    def test_fails_without_pass_marker(self, tmp_project):
        _write_prd(tmp_project, "# PRD\n\n" + PRD_13_SECTIONS)
        _write_report(tmp_project, "# PRD 交叉验证报告\n\n| 场景 | 缺口 |\n|---|---|\n")
        assert (
            run_validator(tmp_project, "prd_cross_validated", "lc-test/pages/docs/prd-cross-validation.html")
            == 1
        )

    def test_fails_on_version_mismatch(self, tmp_project):
        _write_prd(tmp_project, "# PRD\n\n" + PRD_13_SECTIONS, version="v1.3")
        _write_report(tmp_project, _PASS_REPORT, version="v1.3")
        assert (
            run_validator(tmp_project, "prd_cross_validated", "lc-test/pages/docs/prd-cross-validation.html")
            == 1
        )

    def test_fails_when_prd_polluted_after_pass(self, tmp_project):
        _write_prd(tmp_project, "# PRD\n\n" + PRD_13_SECTIONS + "\n> 待补充：字段口径\n")
        _write_report(tmp_project, _PASS_REPORT)
        assert (
            run_validator(tmp_project, "prd_cross_validated", "lc-test/pages/docs/prd-cross-validation.html")
            == 1
        )
