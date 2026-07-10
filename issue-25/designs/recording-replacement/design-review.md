# Design Review: recording-replacement

<!-- status: draft -->

## 背景

- Issue: #25
- 关联需求: `issue-25/requirements/2026-07-09-recording-replacement/requirements.md`
- 关联调研: `issue-25/docs/research/recording-replacement-oss-options.md`

## 设计目标

1. 替换 Lincoln 当前自研的 `record-interview` + `lincoln` TUI 录音链路。
2. 实现本地桌面录音、离线转写、speaker diarization。
3. 新方案可被 Lincoln CLI/Agent 直接调用，输出标准 interview 产物。
4. 优先参考最成熟的开源产品（Meetily）的设计，避免从零造轮子。

## 范围

### 范围内

- 一个受 Meetily 设计启发的 **headless CLI 录音/转写工具**。
- 音频捕获（麦克风 + 系统音频）、本地转写（Whisper/Parakeet）、说话人 diarization、摘要生成。
- Lincoln adapter：把 CLI 输出标准化为 `issue-XX/interviews/<session>/` 结构。
- macOS 优先支持；Windows/Linux 作为后续迭代。

### 范围外

- 会议机器人（bot）加入云端会议。
- 实时字幕/UI 界面。
- 跨设备同步、云端存储。

## 关键决策

| 决策 | 选项 | 理由 |
|---|---|---|
| 参考产品 | Meetily (Rust/Tauri) | ~22.2k stars，最成熟；MIT 协议可收录；Rust 后端与 UI 解耦，适合 CLI 化 |
| CLI 实现语言 | Rust | 与 Meetily 代码库对齐，可复用音频/转写架构；性能好 |
| Diarization 方案 | v1: Python 后处理 (WhisperX + pyannote) | Meetily 社区版无 diarization；WhisperX/pyannote 最成熟 |
| 系统音频捕获 | macOS: Core Audio Tap (Meetily 方案) | 无需虚拟声卡；Windows/Linux 后续补充 |
| 转写引擎 | whisper.cpp (whisper-rs) / Parakeet (ONNX) | 与 Meetily 一致；支持本地离线、GPU 加速 |
| 输出格式 | Markdown transcript + JSON metadata | 兼容现有 `process-interview` skill |
| 摘要生成 | 复用 Meetily LLM 抽象 | 支持 Ollama/Claude/OpenAI/Groq/OpenRouter |

## 架构概述

```
+------------------------------------------------+
|  Lincoln CLI / TUI                             |
|  (calls `lincoln-record record --session-id`)  |
+----------------+------------+------------------+
                 |            |
                 v            v
+-----------------------------------------------+
|  lincoln-record (Rust CLI)                    |
|  - clap 子命令                                |
|  - 配置管理                                   |
+-----------------------------------------------+
                 |
      +----------+----------+
      v                     v
+-------------+     +------------------+
| Audio       |     | Transcription    |
| Pipeline    |---->| Worker           |
| (cpal +     |     | (whisper-rs/ort) |
|  Core Audio |
|  tap + VAD) |
+-------------+     +------------------+
      |                     |
      v                     v
+-----------------------------------------------+
|  Post-processing                              |
|  - Merge checkpoints (ffmpeg)                 |
|  - Diarization (WhisperX/pyannote sidecar)    |
|  - Speaker-labeled transcript                 |
+-----------------------------------------------+
                 |
                 v
+-----------------------------------------------+
|  Output to issue-XX/interviews/<session>/    |
|  - transcript.md                              |
|  - metadata.json                              |
|  - audio.mp4 (optional)                       |
+-----------------------------------------------+
                 |
                 v
+-----------------------------------------------+
|  claude process-interview <session>           |
|  - summary.md                                 |
|  - raw-insights.md                            |
+-----------------------------------------------+
```

## CLI 命令设计

```bash
# 列出可用设备
lincoln-record devices

# 录制会议/访谈（默认同时捕获麦克风和系统音频）
lincoln-record record --session-id 2026-07-10-stakeholder \
                      --mic "MacBook Pro Microphone" \
                      --system-auto \
                      --engine whisper --model large-v3-turbo \
                      --diarize \
                      --output issue-25/interviews/2026-07-10-stakeholder

# 停止录制（或 Ctrl+C）
lincoln-record stop

# 处理已有音频文件
lincoln-record transcribe meeting.wav \
                      --engine whisper --model large-v3-turbo \
                      --diarize \
                      --output issue-25/interviews/2026-07-10-stakeholder

# 预下载模型
lincoln-record warmup --engine whisper --model large-v3-turbo --with-diarization
```

## 数据模型

### `metadata.json`

```json
{
  "session_id": "2026-07-10-stakeholder",
  "started_at": "2026-07-10T09:00:00Z",
  "ended_at": "2026-07-10T09:30:00Z",
  "engine": "whisper",
  "model": "large-v3-turbo",
  "diarization": true,
  "devices": {
    "microphone": "MacBook Pro Microphone",
    "system": "Core Audio Tap"
  },
  "files": {
    "transcript": "transcript.md",
    "audio": "audio.mp4"
  }
}
```

### `transcript.md`

```markdown
# 2026-07-10-stakeholder

## Speakers

- Speaker A
- Speaker B

## Transcript

**[00:00:12] Speaker A**: 我们今天讨论 Lincoln 的录音工具替换方案。

**[00:00:18] Speaker B**: 我认为应该参考 Meetily 的设计重写一个 CLI。
```

## 验收标准

- [ ] `lincoln-record record` 能同时捕获麦克风 + 系统音频并保存。
- [ ] 本地 Whisper/Parakeet 转写结果写入 `transcript.md`。
- [ ] `--diarize` 启用后，转写结果带 speaker label。
- [ ] 输出目录结构符合 Lincoln interview 标准。
- [ ] `claude process-interview <session>` 能基于 `transcript.md` 生成 summary/insights。
- [ ] 不违反 Meetily MIT 协议（不直接复制大量代码，保留引用）。

## 关联文档

- [场景分析](./scenarios.md)
- [功能目录](./feature-catalog.md)
- [数据模型](./data-model.md)
- [流程图](./flows.md)
- [可行性分析](./feasibility.md)

---
*PM 确认时请添加 `<!-- status: approved -->` 或 `[x] PM 已确认设计文档`。*
