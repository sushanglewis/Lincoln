# Lincoln 录音 CLI Wrapper 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在当前 Lincoln workspace 内提供一个命令行录音 wrapper，支持准备、录制、确认、触发 `process-interview` 的完整流程。

**Architecture:** Python CLI 工具，依赖系统 `ffmpeg` 录制 m4a 音频；所有 Lincoln 相关配置和 metadata 生成复用现有规范；录音完成后通过 `claude process-interview <session-id>` 触发下游工作流。

**Tech Stack:** Python 3.11+, `ffmpeg`, `pytest`, `freezegun`, 标准库 `subprocess`/`argparse`/`datetime`。

---

## 文件结构

```
tools/record-interview/
├── pyproject.toml                  # 项目配置与依赖
├── README.md                       # 使用说明
├── record_interview/
│   ├── __init__.py                 # 版本号
│   ├── __main__.py                 # python -m record_interview 入口
│   ├── cli.py                      # argparse + 主流程编排
│   ├── metadata.py                 # metadata.json 生成、读取、校验
│   ├── recorder.py                 # ffmpeg 录音封装
│   ├── validator.py                # session-id 与 workspace 校验
│   └── process.py                  # 调用 claude process-interview
└── tests/
    ├── __init__.py
    ├── test_metadata.py
    ├── test_validator.py
    ├── test_recorder.py
    └── test_cli.py
```

---

## Task 1: 初始化 Python 项目结构

**Files:**
- Create: `tools/record-interview/pyproject.toml`
- Create: `tools/record-interview/README.md`
- Create: `tools/record-interview/record_interview/__init__.py`

- [ ] **Step 1: 创建 pyproject.toml**

```toml
[project]
name = "lincoln-record-interview"
version = "0.1.0"
description = "CLI wrapper to record Lincoln interviews and trigger process-interview"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=8.0", "freezegun>=1.5", "pytest-mock>=3.14"]

[project.scripts]
record-interview = "record_interview.cli:main"
```

- [ ] **Step 2: 创建 README.md**

```markdown
# Lincoln Record Interview CLI

在当前 Lincoln workspace 内录制访谈音频并触发 `process-interview`。

## 使用

```bash
# 进入 Lincoln workspace 后
python -m tools.record-interview SESSION_ID --design-id DESIGN_ID --topic "会议主题"
```

## 依赖

- Python 3.11+
- ffmpeg

## 测试

```bash
pytest tools/record-interview/tests -v
```
```

- [ ] **Step 3: 创建 __init__.py**

```python
__version__ = "0.1.0"
```

- [ ] **Step 4: Commit**

```bash
git add tools/record-interview/
git commit -m "chore: init lincoln record-interview cli project"
```

---

## Task 2: 实现 session ID 与 workspace 校验

**Files:**
- Create: `tools/record-interview/record_interview/validator.py`
- Create: `tools/record-interview/tests/test_validator.py`

- [ ] **Step 1: 写失败测试**

```python
# tools/record-interview/tests/test_validator.py
import pytest
from pathlib import Path
from record_interview.validator import validate_session_id, resolve_workspace_root


def test_validate_session_id_rejects_empty():
    with pytest.raises(ValueError, match="session_id is required"):
        validate_session_id("")


def test_validate_session_id_rejects_invalid_chars():
    with pytest.raises(ValueError, match="invalid characters"):
        validate_session_id("2026-06-27 hello world")


def test_validate_session_id_accepts_valid():
    assert validate_session_id("2026-06-27-stakeholder-checkout") == "2026-06-27-stakeholder-checkout"


def test_resolve_workspace_root_finds_lincoln_root(tmp_path):
    (tmp_path / "recordings").mkdir()
    (tmp_path / "interviews").mkdir()
    (tmp_path / ".claude").mkdir()
    assert resolve_workspace_root(str(tmp_path / "subdir")) == tmp_path


def test_resolve_workspace_root_raises_when_not_found(tmp_path):
    with pytest.raises(FileNotFoundError, match="Lincoln workspace root not found"):
        resolve_workspace_root(str(tmp_path))
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd tools/record-interview
python -m pytest tests/test_validator.py -v
```

Expected: `ModuleNotFoundError` or `ImportError`.

- [ ] **Step 3: 实现最小代码**

```python
# tools/record-interview/record_interview/validator.py
from __future__ import annotations

import re
from pathlib import Path

SESSION_ID_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9-]+$")


def validate_session_id(session_id: str) -> str:
    if not session_id:
        raise ValueError("session_id is required")
    if not SESSION_ID_PATTERN.match(session_id):
        raise ValueError(
            f"session_id '{session_id}' has invalid characters. "
            "Expected format: YYYY-MM-DD-descriptive-name"
        )
    return session_id


def resolve_workspace_root(start_path: str | None = None) -> Path:
    path = Path(start_path or ".").resolve()
    for current in [path, *path.parents]:
        if all((current / d).is_dir() for d in ("recordings", "interviews", ".claude")):
            return current
    raise FileNotFoundError("Lincoln workspace root not found: missing recordings/, interviews/, or .claude/")
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd tools/record-interview
python -m pytest tests/test_validator.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add tools/record-interview/
git commit -m "feat: add session id and workspace validation"
```

---

## Task 3: 实现 metadata.json 生成与读取

**Files:**
- Create: `tools/record-interview/record_interview/metadata.py`
- Create: `tools/record-interview/tests/test_metadata.py`

- [ ] **Step 1: 写失败测试**

```python
# tools/record-interview/tests/test_metadata.py
import json
from pathlib import Path

import pytest
from freezegun import freeze_time

from record_interview.metadata import build_metadata, read_metadata, update_recording_complete


@freeze_time("2026-06-27T10:00:00Z")
def test_build_metadata(tmp_path):
    meta = build_metadata(
        workspace_root=tmp_path,
        session_id="2026-06-27-stakeholder-checkout",
        design_id="checkout-redesign",
        topic="结算流程 redesign 需求访谈",
        branch="lincoln/2026-06-27-stakeholder-checkout-checkout-redesign",
    )
    assert meta["session_id"] == "2026-06-27-stakeholder-checkout"
    assert meta["design_id"] == "checkout-redesign"
    assert meta["topic"] == "结算流程 redesign 需求访谈"
    assert meta["branch"] == "lincoln/2026-06-27-stakeholder-checkout-checkout-redesign"
    assert meta["recording_file"] == "recordings/2026-06-27-stakeholder-checkout.m4a"
    assert meta["started_at"] == "2026-06-27T10:00:00Z"
    assert meta["source"] == "lincoln-record-interview-cli"


def test_read_metadata_returns_none_when_missing(tmp_path):
    assert read_metadata(tmp_path, "2026-06-27-stakeholder-checkout") is None


def test_read_metadata_reads_existing(tmp_path):
    meta_path = tmp_path / "interviews" / "2026-06-27-stakeholder-checkout" / "metadata.json"
    meta_path.parent.mkdir(parents=True)
    meta_path.write_text(json.dumps({"session_id": "x"}), encoding="utf-8")
    assert read_metadata(tmp_path, "2026-06-27-stakeholder-checkout") == {"session_id": "x"}


@freeze_time("2026-06-27T10:45:00Z")
def test_update_recording_complete(tmp_path):
    meta_path = tmp_path / "interviews" / "2026-06-27-stakeholder-checkout" / "metadata.json"
    meta_path.parent.mkdir(parents=True)
    meta = build_metadata(
        workspace_root=tmp_path,
        session_id="2026-06-27-stakeholder-checkout",
        design_id="checkout-redesign",
        topic="t",
        branch="b",
    )
    meta_path.write_text(json.dumps(meta), encoding="utf-8")

    updated = update_recording_complete(tmp_path, "2026-06-27-stakeholder-checkout", duration_seconds=2700)
    assert updated["ended_at"] == "2026-06-27T10:45:00Z"
    assert updated["duration_seconds"] == 2700
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd tools/record-interview
python -m pytest tests/test_metadata.py -v
```

Expected: ImportError.

- [ ] **Step 3: 实现最小代码**

```python
# tools/record-interview/record_interview/metadata.py
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _metadata_path(workspace_root: Path, session_id: str) -> Path:
    return workspace_root / "interviews" / session_id / "metadata.json"


def build_metadata(
    workspace_root: Path,
    session_id: str,
    design_id: str | None,
    topic: str | None,
    branch: str | None,
) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "design_id": design_id,
        "topic": topic,
        "branch": branch,
        "recording_file": f"recordings/{session_id}.m4a",
        "started_at": now_iso(),
        "ended_at": None,
        "duration_seconds": None,
        "source": "lincoln-record-interview-cli",
        "created_by": "lincoln-record-interview-cli",
    }


def read_metadata(workspace_root: Path, session_id: str) -> dict[str, Any] | None:
    path = _metadata_path(workspace_root, session_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_metadata(workspace_root: Path, session_id: str, metadata: dict[str, Any]) -> None:
    path = _metadata_path(workspace_root, session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


def update_recording_complete(
    workspace_root: Path,
    session_id: str,
    duration_seconds: int,
) -> dict[str, Any]:
    metadata = read_metadata(workspace_root, session_id)
    if metadata is None:
        raise FileNotFoundError(f"metadata not found for {session_id}")
    metadata["ended_at"] = now_iso()
    metadata["duration_seconds"] = duration_seconds
    write_metadata(workspace_root, session_id, metadata)
    return metadata
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd tools/record-interview
python -m pytest tests/test_metadata.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add tools/record-interview/
git commit -m "feat: add metadata.json generation and update"
```

---

## Task 4: 实现 ffmpeg 录音封装

**Files:**
- Create: `tools/record-interview/record_interview/recorder.py`
- Create: `tools/record-interview/tests/test_recorder.py`

- [ ] **Step 1: 写失败测试**

```python
# tools/record-interview/tests/test_recorder.py
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from record_interview.recorder import FfmpegRecorder, RecordingError


def test_recorder_builds_correct_command():
    recorder = FfmpegRecorder(sample_rate=44100)
    output = Path("/tmp/test.m4a")
    cmd = recorder._build_command(output)
    assert cmd[0] == "ffmpeg"
    assert "-i" in cmd
    assert "-f" in cmd
    assert str(output) in cmd


@patch("record_interview.recorder.subprocess.Popen")
def test_recorder_start_stop(mock_popen):
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None
    mock_proc.wait.return_value = 0
    mock_popen.return_value = mock_proc

    recorder = FfmpegRecorder(sample_rate=44100)
    recorder.start(Path("/tmp/test.m4a"))
    assert recorder.is_recording()

    recorder.stop()
    mock_proc.terminate.assert_called_once()
    mock_proc.wait.assert_called_once()


@patch("record_interview.recorder.subprocess.Popen")
def test_recorder_raises_on_failure(mock_popen):
    mock_proc = MagicMock()
    mock_proc.wait.return_value = 1
    mock_proc.stderr.read.return_value = "Device not found"
    mock_popen.return_value = mock_proc

    recorder = FfmpegRecorder(sample_rate=44100)
    with pytest.raises(RecordingError, match="ffmpeg exited with code 1"):
        recorder.start(Path("/tmp/test.m4a"))
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd tools/record-interview
python -m pytest tests/test_recorder.py -v
```

Expected: ImportError.

- [ ] **Step 3: 实现最小代码**

```python
# tools/record-interview/record_interview/recorder.py
from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path


class RecordingError(Exception):
    pass


class FfmpegRecorder:
    def __init__(self, sample_rate: int = 44100) -> None:
        self.sample_rate = sample_rate
        self._process: subprocess.Popen | None = None
        self._output_path: Path | None = None
        self._started_at: float | None = None

    def _build_command(self, output_path: Path) -> list[str]:
        return [
            "ffmpeg",
            "-y",
            "-f", "avfoundation",
            "-i", ":default",
            "-ar", str(self.sample_rate),
            "-c:a", "aac",
            "-b:a", "128k",
            str(output_path),
        ]

    def start(self, output_path: Path) -> None:
        if not shutil.which("ffmpeg"):
            raise RecordingError("ffmpeg not found in PATH")
        if self._process is not None:
            raise RecordingError("already recording")

        self._output_path = output_path
        self._started_at = time.monotonic()
        cmd = self._build_command(output_path)
        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def stop(self) -> int:
        if self._process is None:
            raise RecordingError("not recording")
        self._process.terminate()
        try:
            self._process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait(timeout=5)

        returncode = self._process.returncode
        stderr = self._process.stderr.read() if self._process.stderr else ""
        duration = int(time.monotonic() - self._started_at) if self._started_at else 0
        self._process = None
        self._started_at = None

        if returncode != 0:
            raise RecordingError(f"ffmpeg exited with code {returncode}: {stderr}")
        return duration

    def is_recording(self) -> bool:
        return self._process is not None and self._process.poll() is None
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd tools/record-interview
python -m pytest tests/test_recorder.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add tools/record-interview/
git commit -m "feat: add ffmpeg-based audio recorder"
```

---

## Task 5: 实现 process-interview 调用

**Files:**
- Create: `tools/record-interview/record_interview/process.py`
- Create: `tools/record-interview/tests/test_process.py`

- [ ] **Step 1: 写失败测试**

```python
# tools/record-interview/tests/test_process.py
from pathlib import Path
from unittest.mock import patch

from record_interview.process import trigger_process_interview


@patch("record_interview.process.subprocess.run")
def test_trigger_process_interview(mock_run):
    trigger_process_interview(Path("/workspace"), "2026-06-27-stakeholder")
    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "claude"
    assert cmd[1] == "process-interview"
    assert "2026-06-27-stakeholder" in cmd
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd tools/record-interview
python -m pytest tests/test_process.py -v
```

Expected: ImportError.

- [ ] **Step 3: 实现最小代码**

```python
# tools/record-interview/record_interview/process.py
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class ProcessInterviewError(Exception):
    pass


def trigger_process_interview(workspace_root: Path, session_id: str) -> None:
    if not shutil.which("claude"):
        raise ProcessInterviewError("claude CLI not found in PATH")

    cmd = ["claude", "process-interview", session_id]
    result = subprocess.run(
        cmd,
        cwd=workspace_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise ProcessInterviewError(
            f"claude process-interview failed with code {result.returncode}: {result.stderr}"
        )
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd tools/record-interview
python -m pytest tests/test_process.py -v
```

Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add tools/record-interview/
git commit -m "feat: add process-interview trigger"
```

---

## Task 6: 实现 CLI 主流程与确认交互

**Files:**
- Create: `tools/record-interview/record_interview/cli.py`
- Create: `tools/record-interview/record_interview/__main__.py`
- Create: `tools/record-interview/tests/test_cli.py`

- [ ] **Step 1: 写失败测试**

```python
# tools/record-interview/tests/test_cli.py
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from record_interview.cli import run_recording_flow


def test_run_recording_flow_creates_metadata_and_triggers_process(tmp_path):
    recordings_dir = tmp_path / "recordings"
    interviews_dir = tmp_path / "interviews"
    claude_dir = tmp_path / ".claude"
    recordings_dir.mkdir()
    interviews_dir.mkdir()
    claude_dir.mkdir()

    recorder_mock = MagicMock()
    recorder_mock.start.return_value = None
    recorder_mock.stop.return_value = 120
    recorder_mock.is_recording.return_value = False

    with patch("record_interview.cli.FfmpegRecorder", return_value=recorder_mock), \
         patch("record_interview.cli.trigger_process_interview") as mock_trigger, \
         patch("record_interview.cli._confirm", return_value=True):
        run_recording_flow(
            workspace_root=tmp_path,
            session_id="2026-06-27-test",
            design_id="d1",
            topic="test topic",
            branch="main",
        )

    metadata_path = interviews_dir / "2026-06-27-test" / "metadata.json"
    assert metadata_path.exists()
    meta = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert meta["session_id"] == "2026-06-27-test"
    assert meta["duration_seconds"] == 120
    mock_trigger.assert_called_once_with(tmp_path, "2026-06-27-test")
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd tools/record-interview
python -m pytest tests/test_cli.py -v
```

Expected: ImportError.

- [ ] **Step 3: 实现最小代码**

```python
# tools/record-interview/record_interview/cli.py
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from record_interview.metadata import build_metadata, update_recording_complete, write_metadata
from record_interview.process import trigger_process_interview
from record_interview.recorder import FfmpegRecorder
from record_interview.validator import resolve_workspace_root, validate_session_id


def _confirm(duration_seconds: int) -> bool:
    minutes, seconds = divmod(duration_seconds, 60)
    prompt = f"Recording duration: {minutes:02d}:{seconds:02d}. Trigger process-interview? [y/N]: "
    try:
        answer = input(prompt).strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False
    return answer in ("y", "yes")


def run_recording_flow(
    workspace_root: Path,
    session_id: str,
    design_id: str | None,
    topic: str | None,
    branch: str | None,
) -> int:
    recording_path = workspace_root / "recordings" / f"{session_id}.m4a"
    recording_path.parent.mkdir(parents=True, exist_ok=True)

    metadata = build_metadata(workspace_root, session_id, design_id, topic, branch)
    write_metadata(workspace_root, session_id, metadata)
    print(f"Metadata prepared: interviews/{session_id}/metadata.json")

    recorder = FfmpegRecorder()
    print("Recording... Press Enter to stop.")
    recorder.start(recording_path)
    try:
        input()
    finally:
        duration = recorder.stop()
        print(f"Recording saved: {recording_path}")

    update_recording_complete(workspace_root, session_id, duration)

    if not _confirm(duration):
        print("Cancelled. Recording saved but process-interview was not triggered.")
        return 0

    print("Triggering claude process-interview...")
    trigger_process_interview(workspace_root, session_id)
    print("Done.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Record a Lincoln interview")
    parser.add_argument("session_id", help="Session ID in YYYY-MM-DD-descriptive-name format")
    parser.add_argument("--design-id", help="Design ID")
    parser.add_argument("--topic", help="Interview topic")
    parser.add_argument("--branch", help="Current branch name")
    args = parser.parse_args(argv)

    try:
        session_id = validate_session_id(args.session_id)
        workspace_root = resolve_workspace_root()
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return run_recording_flow(
        workspace_root=workspace_root,
        session_id=session_id,
        design_id=args.design_id,
        topic=args.topic,
        branch=args.branch or "main",
    )


if __name__ == "__main__":
    raise SystemExit(main())
```

```python
# tools/record-interview/record_interview/__main__.py
from record_interview.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd tools/record-interview
python -m pytest tests/test_cli.py -v
```

Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add tools/record-interview/
git commit -m "feat: add cli recording flow with human confirmation"
```

---

## Task 7: 集成测试与覆盖率校验

**Files:**
- Modify: `tools/record-interview/pyproject.toml`

- [ ] **Step 1: 添加 pytest 配置**

```toml
[project.optional-dependencies]
dev = ["pytest>=8.0", "freezegun>=1.5", "pytest-mock>=3.14", "pytest-cov>=5.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=record_interview --cov-report=term-missing --cov-fail-under=80"
```

- [ ] **Step 2: 运行全部测试并校验覆盖率**

```bash
cd tools/record-interview
python -m pytest tests/ -v
```

Expected: all tests pass and coverage ≥ 80%.

- [ ] **Step 3: Commit**

```bash
git add tools/record-interview/pyproject.toml
git commit -m "chore: add pytest coverage gate"
```

---

## Task 8: 文档与使用示例

**Files:**
- Modify: `tools/record-interview/README.md`

- [ ] **Step 1: 更新 README 为完整使用说明**

```markdown
# Lincoln Record Interview CLI

在当前 Lincoln workspace 内录制访谈音频并触发 `process-interview`。

## 安装依赖

```bash
# 进入 Lincoln workspace 根目录
python -m pip install -e "tools/record-interview[dev]"
```

确保系统已安装 `ffmpeg` 和 `claude` CLI。

## 使用

```bash
python -m tools.record-interview 2026-06-27-stakeholder-checkout \
  --design-id checkout-redesign \
  --topic "结算流程 redesign 需求访谈" \
  --branch "lincoln/2026-06-27-stakeholder-checkout-checkout-redesign"
```

按回车开始录音，再次按回车停止。确认后自动触发 `claude process-interview`。

## 测试

```bash
cd tools/record-interview
python -m pytest tests/ -v
```
```

- [ ] **Step 2: Commit**

```bash
git add tools/record-interview/README.md
git commit -m "docs: add cli usage and test instructions"
```

---

## Self-Review

### Spec coverage
- PRD Story 1（启动录音准备）：Task 6 `main()` 参数解析 + Task 2 session ID 校验
- PRD Story 2（录制音频）：Task 4 `FfmpegRecorder`
- PRD Story 3（确认并触发转写）：Task 6 `_confirm()` + `trigger_process_interview`
- PRD Story 4（生成标准 artifact）：Task 3 `metadata.py`
- PRD Story 5（复用 Lincoln 配置）：Task 5 直接调用 `claude process-interview`

### Placeholder scan
- 无 TBD/TODO
- 每个测试和实现代码完整
- 命令和预期输出明确

### Type consistency
- `session_id` 类型始终为 `str`
- `workspace_root` 类型始终为 `Path`
- metadata 字段名与 PRD 一致

### Gaps
- 未实现 TUI（argparse + input 已满足 MVP）
- 未实现音量可视化（MVP 可选，可后续添加）
