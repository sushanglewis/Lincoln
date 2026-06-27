import sys
from pathlib import Path

import pytest

VALIDATOR_DIR = Path(__file__).resolve().parents[2] / ".claude" / "skills" / "interview-workflow" / "validators"
sys.path.insert(0, str(VALIDATOR_DIR))

import validate


def run_validator(check_name, *args):
    check_fn = validate.EXIT_CHECKS[check_name]
    with pytest.raises(SystemExit) as exc_info:
        check_fn(*args)
    return exc_info.value.code


def write_design_package(root, design_id, approved=False):
    base = root / "designs" / design_id
    base.mkdir(parents=True, exist_ok=True)
    review = base / "design-review.md"
    review.write_text(
        "# Design Review\n\n"
        "- [link](scenarios.md)\n"
        "- [link](feature-catalog.md)\n"
        "- [link](data-model.md)\n"
        "- [link](flows.md)\n"
        "- [link](feasibility.md)\n"
        f"{'<!-- status: approved -->' if approved else ''}\n"
    )
    (base / "scenarios.md").write_text("# 场景\n")
    (base / "feature-catalog.md").write_text("# 功能清单\n## 验收标准\n")
    (base / "data-model.md").write_text("# 数据模型\n## 字段\n")
    (base / "flows.md").write_text("# 流程\n```mermaid\ngraph TD\nA --> B\n```\n")
    (base / "feasibility.md").write_text(
        "# 可行性\n## 业务可行性\n## 技术可行性\n## 开源项目\n## 技术框架\n"
    )


class TestDesignDocsComplete:
    def test_fails_when_files_missing(self, tmp_project, design_id):
        validate.PROJECT_ROOT = tmp_project
        assert run_validator("design_docs_complete", design_id) == 1

    def test_passes_when_all_files_present(self, tmp_project, design_id):
        validate.PROJECT_ROOT = tmp_project
        write_design_package(tmp_project, design_id)
        assert run_validator("design_docs_complete", design_id) == 0


class TestDesignDocsHumanApproved:
    def test_fails_without_approval_marker(self, tmp_project, design_id):
        validate.PROJECT_ROOT = tmp_project
        write_design_package(tmp_project, design_id, approved=False)
        assert run_validator("design_docs_human_approved", design_id) == 1

    def test_passes_with_approval_marker(self, tmp_project, design_id):
        validate.PROJECT_ROOT = tmp_project
        write_design_package(tmp_project, design_id, approved=True)
        assert run_validator("design_docs_human_approved", design_id) == 0
