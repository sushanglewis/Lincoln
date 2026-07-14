# 可行性分析: recording-replacement

## 业务可行性

目标是让 Lincoln 拥有一条**成熟、本地、离线、可 CLI 调用**的录音/转写链路，替代当前脆弱的 `record-interview` + `lincoln` TUI。通过参考最成熟的可收录产品 Meetily（MIT, ~22.2k stars）的 Rust 后端设计，重写一个 headless CLI，可以在保留 Lincoln 工作流入口的同时，获得：

- 系统音频 + 麦克风双轨录制；
- 本地 Whisper/Parakeet 实时转写；
- 说话人 diarization；
- 标准 Markdown/JSON 输出，直接喂给 `process-interview`。

业务价值：访谈/会议知识沉淀从“半手动、易出错”变为“一条命令自动化”。

## 技术可行性

### 参考对象：Meetily 当前架构

Meetily 的当前版本是自包含 Tauri 桌面应用：

- **UI**：Next.js 前端。
- **后端**：`frontend/src-tauri/src/` 下的 Rust 代码。
- **音频**：`cpal` 捕获麦克风；macOS 通过 `cidre` 做 Core Audio global tap 捕获系统音频；`AudioPipeline` 混音、VAD、降噪、响度归一化；`ffmpeg-sidecar` 合并分段。
- **转写**：`whisper-rs`（whisper.cpp）或 `ort` + Parakeet ONNX。
- **摘要**：`reqwest` 调用 Ollama/OpenAI/Anthropic/Groq/OpenRouter。
- **存储**：`sqlx` SQLite + 每个会议目录下的 `audio.mp4` / `transcripts.json` / `metadata.json`。

详见 [Meetily GitHub](https://github.com/Zackriya-Solutions/meetily)。

### CLI 化思路

Meetily 的核心音频/转写/存储模块**已经与 UI 解耦**，可行路径：

1. **剥离 Tauri**：移除 `lib.rs` 中的 `#[tauri::command]`、`AppHandle`、前端资源、`tray/`、`notifications/`、`analytics/`。
2. **替换事件层**：把 Tauri Emitter 事件换成 stdout 结构化日志或直接写库/文件。
3. **CLI 入口**：它本身已在 `Cargo.toml` 里依赖 `clap`，可直接写一个 `main.rs` 暴露子命令。
4. **数据目录**：把 `app_data_dir()` 改成 CLI 参数 `--data-dir` / `--session-dir`。
5. **增加 diarization**：Meetily 社区版**没有 speaker diarization**（仅 PRO 规划中）。需要额外实现。

### 推荐实现路线

**路线 A：Rust CLI（Meetily 风格，推荐）**

- 用 Rust 重写 CLI harness，复用/借鉴 Meetily 的 `audio/`、`whisper_engine/`、`parakeet_engine/`、`summary/` 设计。
- 音频捕获：macOS 参考 `cidre` Core Audio tap；Windows/Linux 需要补充实现（Meetily 当前未实现）。
- 转写：`whisper-rs` + Parakeet `ort`。
- Diarization：采用**后处理方案**——录音结束后用 Python 侧载（`WhisperX` + `pyannote.audio`）做 diarization；或未来引入 `sherpa-onnx` speaker embedding。
- 摘要：复用 Meetily 的 `summary/llm_client.rs` 设计，支持 Ollama/Claude/OpenAI 等。
- 输出：直接写到 `issue-XX/interviews/<session>/` 下的 `transcript.md`、`metadata.json`。

**路线 B：Python CLI（ownscribe 风格，快速实现）**

- 不参考 Meetily 的 Rust 代码，而是用 Python + `cpal`/CoreAudio + `WhisperX` + `pyannote` 重新实现。
- 开发速度更快，diarization 生态成熟，但与“参考最成熟产品重写”的诉求不完全一致。

## 开源项目 / 框架参考

| 项目 | 作用 | 可借鉴内容 |
|---|---|---|
| [Meetily](https://github.com/Zackriya-Solutions/meetily) | 最成熟本地会议助手 | Rust 音频 pipeline、VAD、降噪、whisper-rs/Parakeet 集成、LLM 摘要抽象 |
| [OpenWhispr](https://github.com/OpenWhispr/OpenWhispr) | 本地 diarization 已可用 | `sherpa-onnx` 说话人识别、voice fingerprinting 设计 |
| [ownscribe](https://github.com/paberr/ownscribe) | CLI-first 本地录制 | CLI 交互设计、WhisperX + pyannote diarization 后处理 |
| [WhisperX](https://github.com/m-bain/whisperX) | ASR + diarization | 本地 diarization 后处理黄金组合 |
| [pyannote.audio](https://github.com/pyannote/pyannote-audio) | 说话人 diarization | _segmentation_ 模型 |

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|---|---|---|
| Meetily 社区版无 diarization | 硬需求无法满足 | 后处理引入 WhisperX/pyannote；或购买/等待 Meetily PRO |
| Windows/Linux 系统音频捕获未实现 | 跨平台能力受限 | 先聚焦 macOS；Windows 用 WASAPI loopback、Linux 用 PulseAudio/PipeWire 逐步补充 |
| Rust 团队经验不足 | 开发/维护成本高 | 先用 Python 侧载 diarization；核心音频链路若人力不足可退回到 Python 方案 |
| 模型下载与 GPU 加速复杂 | 首次使用体验差 | 提供 `warmup` 子命令预下载模型；默认 CPU fallback |
| 直接复制 Meetily 代码带来协议/版权风险 | 合规问题 | 仅借鉴架构与 crate 选型；重新实现 CLI harness 和 diarization；保留 MIT 版权声明 |
| 与 Lincoln 现有 `process-interview` 格式兼容 | 集成失败 | 输出阶段严格对齐 `transcript.md` 结构 |

## 建议方案

**采用路线 A（Rust CLI）作为目标架构，diarization 第一阶段用 Python 后处理兜底。**

理由：

1. Meetily 是同类中最成熟、协议最友好的产品，其 Rust 后端已经解决了 80% 的音频/转写/摘要难题。
2. 剥离 UI 后的 headless CLI 与 Lincoln 的 CLI 工作流天然契合。
3. Diarization 虽然 Meetily 未提供，但 WhisperX/pyannote 是成熟后处理方案，可作为 v1 实现；后续再替换为 Rust 内嵌 diarization。
4. 相比直接集成 Electron/Tauri 桌面应用，CLI 化后 Lincoln 可以完全控制数据流和输出格式。

下一步：产出 `design-review.md` 与 TDD 计划，定义 CLI 子命令、数据流、diarization 后处理接口、与 `process-interview` 的对接方式。
