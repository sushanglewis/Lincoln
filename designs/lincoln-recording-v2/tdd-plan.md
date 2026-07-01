# Lincoln #14 录音功能优化 — TDD 计划

## 目标

为 `tools/record-interview` 的 TUI + 实时转写 + 阶段总结 + 最终总结功能提供测试驱动的开发计划，确保每个模块在实现前都有失败的测试，并在重构后达到 80% 以上覆盖率。

## 1. 模块与测试矩阵

| 模块 | 单元测试 | 集成测试 | E2E | 备注 |
|---|---|---|---|---|
| `errors.py` | ✅ | — | — | 异常类与 remediation 文本 |
| `config.py` | ✅ | — | — | 配置加载、验证、默认值 |
| `worktree.py` | ✅ | — | — | git worktree 检测、回退 |
| `validator.py` | ✅ | — | — | session_id 校验、worktree 解析 |
| `metadata.py` | ✅ | — | — | 元数据构建、更新、phased_summaries 字段 |
| `recorder.py` | ✅ | ✅ | — | chunk 录制、停止、清理 |
| `transcriber.py` | ✅ | ✅ | — | faster-whisper / OpenAI Whisper API |
| `diarizer.py` | ✅ | ✅ | — | pyannote / diarize / heuristic |
| `pipeline.py` | ✅ | ✅ | — | chunk 消费、diarize 对齐、阶段总结触发 |
| `summarizer.py` | ✅ | ✅ | — | claude CLI / OpenAI / Anthropic |
| `phased_summary.py` | ✅ | ✅ | — | 阶段总结生成、汇总为 summary.md |
| `knowledge_loader.py` | ✅ | — | — | 关键词匹配、路径返回 |
| `tui/screens/setup.py` | ✅ | — | — | Textual pilot 测试 |
| `tui/screens/recording.py` | ✅ | — | — | Textual pilot 测试 |
| `tui/screens/summary.py` | ✅ | — | — | Textual pilot 测试 |
| `tui/widgets/*.py` | ✅ | — | — | 各 widget 行为 |
| `cli.py` | ✅ | ✅ | — | TTY 检测、TUI 启动、非 TTY 回退 |
| `process.py` | ✅ | ✅ | — | trigger_process_interview |
| 完整 TUI 流程 | — | ✅ | ✅ | Setup → Record → Summary |

## 2. 测试开发顺序

### 2.1 Phase 0 — 基础重构

#### `errors.py`

```python
# RED
def test_guidance_error_carries_remediation():
    err = FfmpegMissingError()
    assert "brew install ffmpeg" in err.remediation.lower()

# GREEN — 实现 GuidanceError 基类与 FfmpegMissingError
# IMPROVE — 提取公共模板
```

#### `config.py`

```python
# RED
def test_config_defaults():
    cfg = load_config([])
    assert cfg.phase_interval_seconds == 600
    assert cfg.chunk_seconds == 5

# GREEN — 实现 Config dataclass 与默认值
# IMPROVE — 支持 ~/.lincolnrc 覆盖
```

#### `worktree.py`

```python
# RED
def test_find_worktree_root_uses_git(mocker, tmp_path):
    mocker.patch("subprocess.run", return_value=Mock(stdout=str(tmp_path) + "\n"))
    assert find_worktree_root() == tmp_path

# GREEN — 实现 find_worktree_root
# IMPROVE — 非 git 环境回退
```

#### `validator.py`

```python
# RED
def test_resolve_workspace_root_prefers_git_worktree(mocker):
    mocker.patch("record_interview.worktree.find_worktree_root", return_value=Path("/repo"))
    assert resolve_workspace_root() == Path("/repo")

# GREEN — 修改 resolve_workspace_root
```

#### `metadata.py`

```python
# RED
def test_metadata_includes_phase_summaries():
    meta = build_metadata("2026-07-01-test", None, None, None)
    assert meta["phased_summaries"] == []

# GREEN — 扩展 metadata
```

### 2.2 Phase 1 — TUI 核心

#### `tui/widgets/recording_timer.py`

```python
# RED
async def test_timer_increments_every_second(pilot):
    await pilot.press("space")  # 假设开始
    assert "00:01" in app.screen.query_one("#timer").render()

# GREEN — 实现 RecordingTimer
```

#### `tui/widgets/transcript_pane.py`

```python
# RED
async def test_transcript_pane_appends_segments(pilot):
    app.screen.add_segment("Speaker A", "Hello")
    assert "Hello" in app.screen.query_one("#transcript").render()

# GREEN — 实现 TranscriptPane
```

#### `tui/screens/setup.py`

```python
# RED
async def test_setup_disables_start_when_checks_fail(pilot):
    await pilot.pause()
    button = app.screen.query_one("#start-button")
    assert button.disabled

# GREEN — 实现 SetupScreen
```

#### `tui/screens/recording.py`

```python
# RED
async def test_recording_screen_shows_live_indicator(pilot):
    await pilot.press("enter")
    assert "REC" in app.screen.query_one("#indicator").render()

# GREEN — 实现 RecordingScreen
```

#### `tui/screens/summary.py`

```python
# RED
async def test_summary_lists_phase_summaries(pilot):
    app.screen.set_phase_summaries(["phase-summary-01.md"])
    assert "phase-summary-01.md" in app.screen.query_one("#phase-list").render()

# GREEN — 实现 SummaryScreen
```

### 2.3 Phase 2 — 实时流水线

#### `recorder.py`

```python
# RED
def test_chunked_recorder_creates_chunk_files(tmp_path):
    recorder = FfmpegRecorder()
    recorder.start_chunked(tmp_path, chunk_seconds=1)
    time.sleep(1.2)
    chunks = recorder.stop()
    assert len(chunks) >= 1

# GREEN — 实现 start_chunked
```

#### `transcriber.py`

```python
# RED
def test_faster_whisper_transcriber_returns_segments(mocker):
    mock_model = mocker.MagicMock()
    mock_model.transcribe.return_value = iter([
        Segment(start=0.0, end=2.0, text="hello", speaker=None),
    ])
    transcriber = FasterWhisperTranscriber(model=mock_model)
    segments = transcriber.transcribe(Path("x.m4a"))
    assert segments[0].text == "hello"

# GREEN — 实现 FasterWhisperTranscriber
```

#### `diarizer.py`

```python
# RED
def test_pyannote_diarizer_returns_speaker_turns(mocker):
    mock_pipeline = mocker.MagicMock()
    mock_pipeline.return_value.itertracks.return_value = [
        (None, None, {"start": 0.0, "end": 2.0, "label": "SPEAKER_00"})
    ]
    diarizer = PyannoteDiarizer(pipeline=mock_pipeline)
    turns = diarizer.diarize(Path("x.m4a"))
    assert turns[0].speaker == "SPEAKER_00"

# GREEN — 实现 PyannoteDiarizer
```

#### `pipeline.py`

```python
# RED
def test_pipeline_emits_segment_after_chunk(mocker):
    pipeline = TranscriptionPipeline(transcriber=mock_transcriber, diarizer=mock_diarizer)
    pipeline.start()
    pipeline.enqueue(Path("chunk-000.m4a"))
    segment = pipeline.output_queue.get(timeout=2)
    assert segment.text == "hello"

# GREEN — 实现 TranscriptionPipeline
```

### 2.4 Phase 3 — 阶段总结与知识关联

#### `knowledge_loader.py`

```python
# RED
def test_knowledge_loader_finds_relevant_docs(tmp_path):
    (tmp_path / "docs/knowledge/03-features/recording.md").write_text("recording")
    docs = load_knowledge_docs("recording", root=tmp_path)
    assert any("recording.md" in str(p) for p in docs)

# GREEN — 实现 load_knowledge_docs
```

#### `summarizer.py`

```python
# RED
def test_claude_summarizer_invokes_cli_with_file(mocker):
    mock_run = mocker.patch("subprocess.run")
    summarizer = ClaudeSummarizer()
    summarizer.summarize(Path("transcript.md"), [Path("knowledge.md")])
    assert "claude" in mock_run.call_args[0][0]

# GREEN — 实现 ClaudeSummarizer
```

#### `phased_summary.py`

```python
# RED
def test_phase_summary_generator_creates_numbered_files(tmp_path):
    gen = PhasedSummaryGenerator(summarizer=mock_summarizer)
    gen.add_segment(TranscriptionSegment(start=0, end=600, speaker="A", text="..."))
    gen.flush_phase(tmp_path / "interviews/test")
    assert (tmp_path / "interviews/test/phase-summary-01.md").exists()

# GREEN — 实现 PhasedSummaryGenerator
```

```python
# RED
def test_final_summary_aggregates_phase_files(tmp_path):
    (tmp_path / "phase-summary-01.md").write_text("topic A")
    (tmp_path / "phase-summary-02.md").write_text("topic B")
    result = generate_final_summary(tmp_path, summarizer=mock_summarizer)
    assert "topic A" in result.content

# GREEN — 实现 generate_final_summary
```

### 2.5 Phase 4 — 集成

#### `cli.py`

```python
# RED
def test_cli_launches_tui_in_tty(mocker):
    mocker.patch("sys.stdin.isatty", return_value=True)
    mock_app = mocker.patch("record_interview.tui.app.LincolnRecordApp")
    main(["2026-07-01-test"])
    mock_app.run.assert_called_once()

# GREEN — 修改 cli.main
```

#### `process.py`

```python
# RED
def test_trigger_process_interview_passes_summary_path(mocker):
    mock_run = mocker.patch("subprocess.run")
    trigger_process_interview(Path("/repo"), "2026-07-01-test", summary_path=Path("/repo/interviews/.../summary.md"))
    assert "claude" in mock_run.call_args[0][0]

# GREEN — 修改 trigger_process_interview
```

## 3. 集成测试

### `test_full_tui_flow.py`

```python
async def test_full_flow_mocked(pilot):
    # 进入 Setup
    await pilot.pause()
    # 模拟所有检查通过
    app.screen.mark_all_checks_passed()
    await pilot.click("#start-button")
    # 进入 Recording，模拟收到转写 segment
    app.screen.pipeline.emit(TranscriptionSegment(...))
    await pilot.pause()
    assert "hello" in app.screen.query_one("#transcript").render()
    # 停止录制
    await pilot.press("enter")
    # 进入 Summary
    assert app.screen.query_one("#phase-list")
```

### `test_worktree_artifacts.py`

```python
def test_artifacts_land_in_worktree(tmp_path, mocker):
    mocker.patch("record_interview.worktree.find_worktree_root", return_value=tmp_path)
    run_recording_flow(...)
    assert (tmp_path / "interviews/2026-07-01-test/phase-summary-01.md").exists()
```

## 4. E2E 手动测试

1. 录制 11 分钟真实音频。
2. 验证 `recordings/{sid}.m4a` 存在且可播放。
3. 验证 `interviews/{sid}/transcript.md` 包含带说话人标签的实时转写片段。
4. 验证 `interviews/{sid}/phase-summary-01.md` 与 `phase-summary-02.md` 存在。
5. 验证 `interviews/{sid}/summary.md` 由阶段总结汇总生成。
6. 验证 `metadata.json` 的 `phased_summaries` 字段记录正确。
7. 运行 `scripts/stage_loader.py --stage ingest --action validate-exit` 通过。

## 5. 覆盖率门控

```bash
pytest --cov=record_interview --cov-report=term-missing --cov-fail-under=80
```

## 6. 测试约定

- 所有测试遵循 AAA 结构（Arrange-Act-Assert）。
- 测试名必须描述行为，例如 `test_emits_segment_after_processing_chunk`。
- 使用 `pytest-mock` 和 `tmp_path`，避免真实网络/模型调用。
- TUI 测试使用 `textual.pilot`。
- 涉及文件系统的测试必须清理临时文件。
