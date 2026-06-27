# Lincoln 产品设计与 TDD 工作流扩展实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有 Lincoln 工作流中补齐 `product-design-docs` → `product-prototype` → `tdd-development-plan` 三个新步骤的 prompt、validator、测试与文档，确保从需求确认到 OpenSpec 提案的链路可运行、可校验。

**Architecture:** 新步骤沿用现有 skill command + workflow step + validator check 三层结构；新增 `tests/` 目录保存 validator smoke tests 和 workflow contract tests；GitHub Actions 中增加静态校验步骤，保证 YAML、Python 和 prompt 路径有效。

**Tech Stack:** Python 3.12+ (validator + tests), Pytest, YAML/Claude Code skill, Markdown prompts, GitHub Actions.

---

## 已落地资产（无需改动，只验证）

- `.claude/skills/interview-workflow/skill.yaml` — 已新增 `draft-product-design`、`build-product-prototype`、`plan-tdd-development` 命令
- `.claude/workflows/interview-to-knowledge.yaml` — 已新增 `product-design-docs`、`product-prototype`、`tdd-development-plan` 步骤
- `.claude/skills/interview-workflow/validators/validate.py` — 已新增对应 entry/exit checks
- `.claude/skills/interview-workflow/prompts/draft-product-design.md`
- `.claude/skills/interview-workflow/prompts/build-product-prototype.md`
- `.claude/skills/interview-workflow/prompts/plan-tdd-development.md`
- `.claude/skills/interview-workflow/prompts/propose-with-openspec.md` — 已改为接收 `<session-id> <design-id> <change-name>`
- `README.md` / `.claude/AGENTS.md` — 已更新步骤说明与确认门

## 待完成资产

### Task 1: 创建测试目录与 conftest

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

**Goal:** 为 validator smoke tests 提供共享 fixtures（临时项目根目录、design_id、session_id）。

- [ ] **Step 1: 创建测试包初始化文件**

```bash
touch tests/__init__.py
```

- [ ] **Step 2: 编写 conftest.py**

```python
import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Return the actual Lincoln project root."""
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def tmp_project(tmp_path):
    """Create a minimal temporary project skeleton for validator tests."""
    root = tmp_path / "lincoln"
    (root / "designs" / "checkout-redesign").mkdir(parents=True)
    (root / "requirements" / "2026-06-27-stakeholder").mkdir(parents=True)
    (root / "openspec" / "changes" / "add-csv-export").mkdir(parents=True)
    return root


@pytest.fixture
def design_id():
    return "checkout-redesign"


@pytest.fixture
def session_id():
    return "2026-06-27-stakeholder"
```

- [ ] **Step 3: Commit**

```bash
git add tests/__init__.py tests/conftest.py
git commit -m "test: add pytest fixtures for validator tests"
```

---

### Task 2: Validator Smoke Tests — 设计文档

**Files:**
- Create: `tests/validators/test_design_docs.py`

**Goal:** 验证 `check_design_docs_complete` 和 `check_design_docs_human_approved` 的通过/失败行为。

- [ ] **Step 1: 编写测试文件**

```python
import subprocess
import sys
from pathlib import Path

import pytest

VALIDATOR = Path(__file__).resolve().parents[2] / ".claude" / "skills" / "interview-workflow" / "validators" / "validate.py"


def run_validator(check, args):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), "--phase", "exit", "--check", check, "--args", args],
        capture_output=True,
        text=True,
    )


def test_design_docs_complete_missing_files(tmp_project, design_id):
    result = run_validator("design_docs_complete", design_id)
    assert result.returncode == 1
    assert "missing or empty" in result.stdout.lower() or "missing" in result.stderr.lower()


def write_design_package(root, design_id, approved=False):
    base = root / "designs" / design_id
    base.mkdir(parents=True, exist_ok=True)
    review = base / "design-review.md"
    review.write_text(
        f"# Design Review\n\n- [link](scenarios.md)\n- [link](feature-catalog.md)\n"
        f"- [link](data-model.md)\n- [link](flows.md)\n- [link](feasibility.md)\n"
        f"{'<!-- status: approved -->' if approved else ''}\n"
    )
    (base / "scenarios.md").write_text("# 场景\n")
    (base / "feature-catalog.md").write_text("# 功能清单\n## 验收标准\n")
    (base / "data-model.md").write_text("# 数据模型\n## 字段\n")
    (base / "flows.md").write_text("# 流程\n```mermaid\ngraph TD\nA-->B\n```\n")
    (base / "feasibility.md").write_text(
        "# 可行性\n## 业务可行性\n## 技术可行性\n## 开源项目\n## 技术框架\n"
    )


def test_design_docs_complete_all_files(tmp_project, design_id):
    write_design_package(tmp_project, design_id)
    result = run_validator("design_docs_complete", design_id)
    assert result.returncode == 0


def test_design_docs_human_approved_without_marker(tmp_project, design_id):
    write_design_package(tmp_project, design_id, approved=False)
    result = run_validator("design_docs_human_approved", design_id)
    assert result.returncode == 1
    assert "approval marker" in result.stdout.lower() or "approval" in result.stderr.lower()


def test_design_docs_human_approved_with_marker(tmp_project, design_id):
    write_design_package(tmp_project, design_id, approved=True)
    result = run_validator("design_docs_human_approved", design_id)
    assert result.returncode == 0
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/validators/test_design_docs.py -v
```

Expected: 4 tests collected; currently FAIL because file does not exist.

- [ ] **Step 3: 创建文件后运行测试确认通过**

After writing the file, rerun:

```bash
pytest tests/validators/test_design_docs.py -v
```

Expected: 4 PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/validators/test_design_docs.py
git commit -m "test: add validator smoke tests for design docs"
```

---

### Task 3: Validator Smoke Tests — 原型与 TDD Plan

**Files:**
- Create: `tests/validators/test_prototype_and_tdd.py`

**Goal:** 验证 `check_prototype_artifact_complete` 和 `check_tdd_plan_complete`。

- [ ] **Step 1: 编写测试文件**

```python
import subprocess
import sys
from pathlib import Path

import pytest

VALIDATOR = Path(__file__).resolve().parents[2] / ".claude" / "skills" / "interview-workflow" / "validators" / "validate.py"


def run_validator(check, args):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), "--phase", "exit", "--check", check, "--args", args],
        capture_output=True,
        text=True,
    )


def write_prototype_package(root, design_id, prototype_approved=False):
    base = root / "designs" / design_id
    base.mkdir(parents=True, exist_ok=True)
    (base / "prototype.pen").write_text("pen-placeholder")
    (base / "fields.md").write_text("# 字段\n## 校验\n## 错误状态\n")
    ui = base / "ui-spec.md"
    ui.write_text(
        "# UI 规格\n## 界面\n## 交互\n## 状态\n"
        f"{'<!-- prototype-status: approved -->' if prototype_approved else ''}\n"
    )


def test_prototype_artifact_complete_missing_pen(tmp_project, design_id):
    result = run_validator("prototype_artifact_complete", design_id)
    assert result.returncode == 1
    assert "prototype" in result.stdout.lower()


def test_prototype_artifact_complete_all_files(tmp_project, design_id):
    write_prototype_package(tmp_project, design_id)
    result = run_validator("prototype_artifact_complete", design_id)
    assert result.returncode == 0


def write_tdd_plan(root, design_id, ready=False):
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


def test_tdd_plan_complete_missing_sections(tmp_project, design_id):
    base = tmp_project / "designs" / design_id
    base.mkdir(parents=True, exist_ok=True)
    (base / "tdd-plan.md").write_text("# TDD Plan\n")
    result = run_validator("tdd_plan_complete", design_id)
    assert result.returncode == 1
    assert "missing sections" in result.stdout.lower()


def test_tdd_plan_complete_with_all_sections(tmp_project, design_id):
    write_tdd_plan(tmp_project, design_id)
    result = run_validator("tdd_plan_complete", design_id)
    assert result.returncode == 0
```

- [ ] **Step 2: 运行测试**

```bash
pytest tests/validators/test_prototype_and_tdd.py -v
```

Expected: 5 PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/validators/test_prototype_and_tdd.py
git commit -m "test: add validator smoke tests for prototype and tdd plan"
```

---

### Task 4: Workflow Contract Tests

**Files:**
- Create: `tests/test_workflow_contracts.py`

**Goal:** 验证 workflow YAML 的 entry/exit checks 与 validator registry 一一对应。

- [ ] **Step 1: 编写测试文件**

```python
import re
from pathlib import Path

import pytest
import yaml


def test_workflow_checks_exist_in_validator_registry():
    root = Path(__file__).resolve().parent
    workflow_path = root / ".claude" / "workflows" / "interview-to-knowledge.yaml"
    validator_path = root / ".claude" / "skills" / "interview-workflow" / "validators" / "validate.py"

    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    validator_source = validator_path.read_text(encoding="utf-8")

    entry_match = re.search(r"ENTRY_CHECKS\s*=\s*\{([^}]+)\}", validator_source, re.DOTALL)
    exit_match = re.search(r"EXIT_CHECKS\s*=\s*\{([^}]+)\}", validator_source, re.DOTALL)

    entry_names = set(re.findall(r'"(\w+)"', entry_match.group(1))) if entry_match else set()
    exit_names = set(re.findall(r'"(\w+)"', exit_match.group(1))) if exit_match else set()

    used_entry = set()
    used_exit = set()
    for step in workflow["workflow"]["steps"]:
        for check in step.get("entry_checks", []):
            used_entry.add(check["check"])
        for check in step.get("exit_checks", []):
            used_exit.add(check["check"])

    assert used_entry <= entry_names, f"Missing entry checks: {used_entry - entry_names}"
    assert used_exit <= exit_names, f"Missing exit checks: {used_exit - exit_names}"


def test_propose_step_requires_tdd_plan_ready():
    root = Path(__file__).resolve().parent
    workflow_path = root / ".claude" / "workflows" / "interview-to-knowledge.yaml"
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

    propose = next(s for s in workflow["workflow"]["steps"] if s["id"] == "propose")
    entry_checks = [c["check"] for c in propose.get("entry_checks", [])]
    assert "tdd_plan_ready" in entry_checks
```

- [ ] **Step 2: 运行测试**

```bash
pytest tests/test_workflow_contracts.py -v
```

Expected: 2 PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/test_workflow_contracts.py
git commit -m "test: add workflow contract tests"
```

---

### Task 5: Static Validation Script

**Files:**
- Create: `scripts/static-check.sh`

**Goal:** 在 CI/本地一次性校验 YAML 可解析、Python 可编译、prompt 路径存在。

- [ ] **Step 1: 编写脚本**

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> Validate YAML files"
python3 -c "import yaml; yaml.safe_load(open('.claude/workflows/interview-to-knowledge.yaml')); yaml.safe_load(open('.claude/skills/interview-workflow/skill.yaml'))"

echo "==> Validate Python syntax"
python3 -m py_compile .claude/skills/interview-workflow/validators/validate.py

echo "==> Validate prompt paths in skill.yaml"
python3 <<'PY'
import yaml
from pathlib import Path

root = Path(__file__).resolve().parents[1]
skill = yaml.safe_load((root / ".claude/skills/interview-workflow/skill.yaml").read_text(encoding="utf-8"))
base = root / ".claude/skills/interview-workflow"
for name, cmd in skill.get("commands", {}).items():
    prompt = cmd.get("prompt")
    if prompt:
        path = base / prompt
        if not path.exists():
            raise FileNotFoundError(f"Missing prompt for command '{name}': {path}")
print("All prompt paths resolved.")
PY

echo "==> Run pytest"
python3 -m pytest tests/ -v

echo "==> All static checks passed"
```

- [ ] **Step 2: 赋予执行权限并运行**

```bash
chmod +x scripts/static-check.sh
./scripts/static-check.sh
```

Expected: all checks pass.

- [ ] **Step 3: Commit**

```bash
git add scripts/static-check.sh
git commit -m "chore: add static validation script"
```

---

### Task 6: GitHub Actions 接入静态校验

**Files:**
- Modify: `.github/workflows/openspec-check.yml`

**Goal:** 每次 push/PR 都运行静态校验与测试。

- [ ] **Step 1: 在 openspec-check.yml 开头新增 job**

Replace the file with:

```yaml
name: Lincoln Checks

on:
  push:
  pull_request:

jobs:
  static-checks:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pyyaml pytest

      - name: Run static checks
        run: ./scripts/static-check.sh

  check-openspec:
    needs: static-checks
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Validate OpenSpec artifact structure
        run: |
          shopt -s nullglob
          change_dirs=(openspec/changes/*/)
          if [ ${#change_dirs[@]} -eq 0 ]; then
            echo "No OpenSpec changes found; skipping artifact structure check."
            exit 0
          fi

          EXIT=0
          for change_dir in "${change_dirs[@]}"; do
            change_name=$(basename "$change_dir")
            echo "Checking $change_name..."
            for file in proposal.md design.md tasks.md; do
              if [ ! -s "$change_dir/$file" ]; then
                echo "ERROR: $change_dir/$file is missing or empty"
                EXIT=1
              fi
            done
            if [ ! -d "$change_dir/specs" ] || [ -z "$(ls -A "$change_dir/specs")" ]; then
              echo "ERROR: $change_dir/specs is missing or empty"
              EXIT=1
            fi
          done
          exit $EXIT

      - name: Check tasks link to issues
        run: |
          echo "Task-to-issue linkage check is performed by the local Lincoln Agent."
```

- [ ] **Step 2: 运行本地校验**

```bash
./scripts/static-check.sh
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/openspec-check.yml
git commit -m "ci: run static checks and pytest on every push/pr"
```

---

### Task 7: 最终审查与文档更新

**Files:**
- Read: `.claude/AGENTS.md`, `README.md`
- Modify: 如有遗漏

**Goal:** 确保 README/AGENTS 中的命令签名、确认门、Pencil 处理规范与代码一致。

- [ ] **Step 1: 运行完整测试套件**

```bash
./scripts/static-check.sh
```

- [ ] **Step 2: 使用 code-reviewer agent 审查修改**

```bash
# Agent call: code-reviewer on the current diff
```

Address any CRITICAL or HIGH findings.

- [ ] **Step 3: Commit any final fixes**

```bash
git add -A
git commit -m "docs: align README/AGENTS with design-tdd workflow extension"
```

---

## Spec Coverage Check

| Plan Requirement | Implementing Task |
|------------------|-------------------|
| 新增 `product-design-docs` 步骤 | Already in workflow YAML / validator / prompts |
| 新增 `product-prototype` 步骤 | Already in workflow YAML / validator / prompts |
| 新增 `tdd-development-plan` 步骤 | Already in workflow YAML / validator / prompts |
| 调整 `propose` 入口为 `tdd_plan_ready` | Already in workflow YAML / propose prompt |
| 新增 validator entry/exit checks | Already in validate.py |
| 更新 README/AGENTS 确认门 | Already in README.md / AGENTS.md |
| 静态验证：YAML parse、py_compile、prompt 路径 | Task 5 |
| Validator smoke tests | Task 2, Task 3 |
| Workflow contract tests | Task 4 |
| CI 接入静态校验 | Task 6 |

## Placeholder Scan

- No TBD/TODO in task steps.
- Every test contains concrete assertions.
- Static script contains exact commands.

## Type Consistency

- `design_id` = kebab-case string, consistent with validator regex.
- `session_id` = `YYYY-MM-DD-descriptive-name`, consistent with workflow conventions.
- Validator runner CLI args = comma-separated strings, consistent with existing usage.
