from pathlib import Path

from .conftest import run_validator


def write_prototype_package(root: Path, design_id: str, prototype_approved: bool = False):
    base = root / "designs" / design_id
    base.mkdir(parents=True, exist_ok=True)
    (base / "prototype.pen").write_text("pen-placeholder")
    (base / "fields.md").write_text("# 字段\n## 校验\n## 错误状态\n")
    ui = base / "ui-spec.md"
    ui.write_text(
        "# UI 规格\n## 界面\n## 交互\n## 状态\n"
        f"{'<!-- prototype-status: approved -->' if prototype_approved else ''}\n"
    )


def write_tdd_plan(root: Path, design_id: str, ready: bool = False):
    base = root / "designs" / design_id
    base.mkdir(parents=True, exist_ok=True)
    tdd = base / "tdd-plan.md"
    tdd.write_text(
        "# TDD Plan\n\n"
        "- Source: requirements/2026-06-27-stakeholder/requirements.md\n"
        f"- Source: designs/{design_id}/design-review.md\n"
        f"- Source: designs/{design_id}/fields.md\n"
        f"- Source: designs/{design_id}/ui-spec.md\n"
        f"- Source: designs/{design_id}/prototype.pen\n\n"
        "## 验收映射\n## 测试场景\n## 红/绿/重构\n## 任务切片\n## 回归范围\n"
        f"{'<!-- status: ready-for-openspec -->' if ready else ''}\n"
    )


class TestPrototypeArtifactComplete:
    def test_fails_when_prototype_pen_missing(self, tmp_project, design_id):
        assert run_validator(tmp_project, "prototype_artifact_complete", design_id) == 1

    def test_passes_when_all_artifacts_present(self, tmp_project, design_id):
        write_prototype_package(tmp_project, design_id)
        assert run_validator(tmp_project, "prototype_artifact_complete", design_id) == 0


class TestTddPlanComplete:
    def test_fails_when_sections_missing(self, tmp_project, design_id):
        base = tmp_project / "designs" / design_id
        base.mkdir(parents=True, exist_ok=True)
        (base / "tdd-plan.md").write_text("# TDD Plan\n")
        assert run_validator(tmp_project, "tdd_plan_complete", design_id) == 1

    def test_passes_when_all_sections_present(self, tmp_project, design_id):
        write_tdd_plan(tmp_project, design_id)
        assert run_validator(tmp_project, "tdd_plan_complete", design_id) == 0
