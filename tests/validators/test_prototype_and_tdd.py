from pathlib import Path

from .conftest import run_validator


def _doc_source(markdown: str) -> str:
    return f'<script type="text/markdown" id="docSource">\n{markdown}\n</script>\n'


def write_prototype_package(root: Path, design_id: str, prototype_approved: bool = False):
    docs = root / "lc-test" / "pages" / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    prototype_dir = root / "lc-test" / "pages" / "prototype"
    prototype_dir.mkdir(parents=True, exist_ok=True)
    (prototype_dir / "index.html").write_text("prototype", encoding="utf-8")

    (docs / "fields.html").write_text(
        _doc_source("# 字段\n## 校验\n## 错误状态\n"), encoding="utf-8"
    )
    ui = docs / "ui-spec.html"
    ui.write_text(
        _doc_source(
            "# UI 规格\n## 界面\n## 交互\n## 状态\n"
            f"{'<!-- prototype-status: approved -->' if prototype_approved else ''}"
        ),
        encoding="utf-8",
    )


def write_tdd_plan(root: Path, design_id: str, ready: bool = False):
    docs = root / "lc-test" / "pages" / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    tdd = docs / "tdd-plan.html"
    tdd.write_text(
        _doc_source(
            "# TDD Plan\n\n"
            "- Source: lc-test/pages/docs/requirements.html\n"
            "- Source: lc-test/pages/docs/design-review.html\n"
            "- Source: lc-test/pages/docs/fields.html\n"
            "- Source: lc-test/pages/docs/ui-spec.html\n"
            "- Source: lc-test/pages/prototype/\n\n"
            "## 验收映射\n## 测试场景\n## 红/绿/重构\n## 任务切片\n## 回归范围\n"
            f"{'<!-- status: ready-for-openspec -->' if ready else ''}"
        ),
        encoding="utf-8",
    )


class TestPrototypeArtifactComplete:
    def test_fails_when_prototype_pen_missing(self, tmp_project, design_id):
        assert run_validator(tmp_project, "prototype_artifact_complete", design_id) == 1

    def test_passes_when_all_artifacts_present(self, tmp_project, design_id):
        write_prototype_package(tmp_project, design_id)
        assert run_validator(tmp_project, "prototype_artifact_complete", design_id) == 0


class TestTddPlanComplete:
    def test_fails_when_sections_missing(self, tmp_project, design_id):
        docs = tmp_project / "lc-test" / "pages" / "docs"
        docs.mkdir(parents=True, exist_ok=True)
        (docs / "tdd-plan.html").write_text(_doc_source("# TDD Plan\n"), encoding="utf-8")
        assert run_validator(tmp_project, "tdd_plan_complete", design_id) == 1

    def test_passes_when_all_sections_present(self, tmp_project, design_id):
        write_tdd_plan(tmp_project, design_id)
        assert run_validator(tmp_project, "tdd_plan_complete", design_id) == 0
