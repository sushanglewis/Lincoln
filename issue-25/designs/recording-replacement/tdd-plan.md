# TDD 研发计划: recording-replacement

<!-- status: ready-for-openspec -->

## 目标

基于已确认的设计，实现 `lincoln-record` —— 一个受 Meetily 设计启发的 headless CLI 录音/转写工具，并接入 Lincoln interview-to-knowledge 工作流。

## 范围

- 实现 Rust CLI 核心：设备发现、音频录制、本地转写、文件输出。
- 实现 Python diarization 侧载：基于 WhisperX + pyannote.audio。
- 实现 Lincoln adapter：将 CLI 输出标准化为 `issue-XX/interviews/<session>/` 结构。
- macOS v1 优先；Windows/Linux 在后续迭代支持。
- 不实现 UI、不实现云端模式、不实现会议机器人。

## 技术栈

- **CLI 核心**: Rust + `clap` + `tokio` + `cpal` + `cidre`（macOS system audio）+ `whisper-rs` / `ort`
- **Diarization 后处理**: Python + `whisperx` + `pyannote.audio`
- **测试**: Rust `cargo test` + Python `pytest`
- **构建**: `cargo build` / `cargo install`

## 测试策略

| 类型 | 覆盖率目标 | 重点 |
|---|---|---|
| Unit Tests | >= 80% | 配置解析、音频 chunk 处理、转写结果格式化、diarization 输出映射 |
| Integration Tests | 关键路径覆盖 | CLI 子命令到文件输出的端到端（使用预录制音频 fixture，避免真实麦克风依赖） |
| E2E Tests | 1 条主流程 | 在 CI 允许的 macOS runner 上跑完整 `record` → `transcribe` → `process-interview` 链路 |

### Fixture 设计

- `tests/fixtures/sample_meeting.wav` — 预录制双说话人音频，用于转写/diarization 测试。
- `tests/fixtures/expected_transcript.md` — 期望输出，验证格式与 speaker label。

## 实现阶段与测试节奏

### Phase 1 — CLI 骨架与配置（RED → GREEN → REFACTOR）

1. **测试先行**
   - `test_cli_parses_record_command`：验证 `record --session-id --mic --system-auto --diarize` 参数解析。
   - `test_config_defaults`：验证默认配置加载。
2. **实现**
   - 创建 `tools/lincoln-record/` Rust crate。
   - 定义 `Cli`、`RecordArgs`、`Config`。
   - 实现 `devices` 子命令（依赖 `cpal`）。
3. **验证**
   - `cargo test --bin lincoln-record` 通过。

### Phase 2 — 音频捕获与保存（RED → GREEN → REFACTOR）

1. **测试先行**
   - `test_record_writes_audio_file`：使用 mock audio source，验证录制结束能写出 `audio.mp4`。
   - `test_pipeline_mixes_mic_and_system`：验证双声道/混音输出。
2. **实现**
   - 实现 `audio/` 模块：
     - `capture/microphone.rs` — `cpal` 麦克风捕获；
     - `capture/system_macos.rs` — `cidre` Core Audio tap（macOS）；
     - `pipeline.rs` — chunk 缓冲、混音、VAD 入口；
     - `saver.rs` — 30 秒 checkpoint + ffmpeg 合并。
   - 实现 `record` 子命令：
     - 启动/停止录制；
     - 捕获到临时 checkpoints；
     - 停止后合并为 `audio.mp4`。
3. **验证**
   - 使用 fixture 音频代替真实麦克风跑集成测试。

### Phase 3 — 本地转写（RED → GREEN → REFACTOR）

1. **测试先行**
   - `test_transcribe_produces_segments`：输入 fixture WAV，输出 `TranscriptSegment` 列表。
   - `test_transcription_markdown_format`：验证 `transcript.md` 格式。
2. **实现**
   - 实现 `transcription/` 模块：
     - `whisper_provider.rs` — `whisper-rs` 封装；
     - `parakeet_provider.rs` — `ort` + Parakeet ONNX 封装；
     - `provider.rs` — trait 抽象；
     - `worker.rs` — 分块转写。
   - 实现 `transcribe` 子命令。
3. **验证**
   - 集成测试：fixture → transcript.md（无 diarization）。

### Phase 4 — Speaker Diarization（RED → GREEN → REFACTOR）

1. **测试先行**
   - `test_diarize_labels_speakers`：输入 fixture WAV，输出带 speaker label 的 segment。
   - `test_diarization_fallback`：diarization 失败时仍保留无 label 转写。
2. **实现**
   - 在 `tools/lincoln-record/diarize/` 创建 Python 侧载：
     - `whisperx_diarize.py` — 调用 `whisperx` 做 alignment + diarization；
     - `merge.py` — 把 diarization 结果合并回 Rust 输出的 `transcripts.json`。
   - Rust 侧调用 Python 脚本并解析输出。
3. **验证**
   - 使用 fixture 验证 speaker label 正确性；允许 mild speaker name 不一致，但要求 speaker 数量与标签一致。

### Phase 5 — Lincoln 标准输出与 Adapter（RED → GREEN → REFACTOR）

1. **测试先行**
   - `test_output_matches_linterview_structure`：验证输出目录与 `transcript.md` / `metadata.json` 格式。
   - `test_process_interview_can_consume_output`：验证 `claude process-interview <session>` 能基于输出生成 summary。
2. **实现**
   - `output/` 模块：
     - 写入 `metadata.json`；
     - 写入 `transcript.md`（含 Speakers 列表）。
   - 更新 `tools/lincoln/src/recording/spawnRecorder.ts`：
     - 启动 `lincoln-record` 替代旧 `record-interview`；
     - 若新工具不可用，提示安装/降级到旧工具。
3. **验证**
   - 端到端测试：fixture → `transcript.md` → `summary.md`。

### Phase 6 — 废弃旧链路 + 文档（REFACTOR）

1. 在 `tools/record-interview/README.md` 中标记 deprecated。
2. 更新 `.claude/skills/process-interview/SKILL.md`，说明新 transcript 来源。
3. 更新 `README.md` 安装指引。
4. 清理旧 mock 音量条等 dead code。

## 关键文件清单

```
tools/lincoln-record/
├── Cargo.toml
├── src/
│   ├── main.rs                 # clap CLI 入口
│   ├── cli.rs                  # 子命令定义
│   ├── config.rs               # 配置加载
│   ├── audio/
│   │   ├── mod.rs
│   │   ├── capture/
│   │   │   ├── microphone.rs
│   │   │   ├── system_macos.rs
│   │   │   └── mod.rs
│   │   ├── pipeline.rs         # 混音/VAD/分块
│   │   └── saver.rs            # checkpoint + 合并
│   ├── transcription/
│   │   ├── mod.rs
│   │   ├── provider.rs         # trait
│   │   ├── whisper_provider.rs
│   │   ├── parakeet_provider.rs
│   │   └── worker.rs
│   ├── output/
│   │   ├── mod.rs
│   │   ├── metadata.rs
│   │   └── transcript.rs
│   └── summary/
│       └── llm_client.rs       # Ollama/OpenAI/Anthropic 等
├── diarize/
│   ├── whisperx_diarize.py
│   └── merge.py
└── tests/
    ├── fixtures/
    │   └── sample_meeting.wav
    └── integration_tests.rs

tools/lincoln/src/recording/spawnRecorder.ts   # 适配新 CLI
.claude/skills/process-interview/SKILL.md      # 更新 transcript 来源说明
```

## Definition of Done

- [ ] `cargo test` 全部通过，覆盖率 ≥ 80%。
- [ ] `lincoln-record record --session-id ... --diarize` 在 macOS 上能产出带 speaker label 的 `transcript.md`。
- [ ] `lincoln-record transcribe fixture.wav --diarize` 在 CI 中稳定通过。
- [ ] `claude process-interview <session>` 能消费输出并生成 `summary.md`。
- [ ] 旧 `record-interview` 标记 deprecated 但不删除。
- [ ] 文档（README、skill、design docs）已更新。
- [ ] OpenSpec 任务已拆分并关联到 GitHub issue。

## 下一步

进入 `propose-with-openspec` 阶段，把本 TDD 计划拆分为具体 GitHub Issues / OpenSpec tasks。
