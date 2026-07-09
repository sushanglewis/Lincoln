# Lincoln 录音工具 OSS 替换方案调研

<!-- status: draft -->

## 1. 当前 Lincoln 录音链路现状

当前链路由三部分组成：

1. **`tools/record-interview/`** — Python CLI，封装 `ffmpeg -f avfoundation -i :default`，仅录制 macOS 默认麦克风，输出 `recordings/<session>.m4a`；同时写 `interviews/<session>/metadata.json`，并嵌套调用 `claude process-interview`。
2. **`tools/lincoln/`** — Ink/React TUI，仅提供交互界面，实际录制委托给 Python CLI；音量条为 mock 数据。
3. **`.claude/skills/process-interview/`** — 提示词驱动的转写 skill，未实现自动化 Whisper 后端。

主要痛点：

- 只录麦克风，不捕获系统/会议应用音频；
- TUI 音频指示器为假数据；
- 转写依赖人工调用 Whisper；
- 嵌套 `claude` 子进程脆弱；
- macOS-only，无设备选择；
- 两包分离，无统一安装器。

## 2. 需求约束（PM 已确认）

1. 只需要**本地桌面录音**（替代当前麦克风录制）；
2. 转写必须**本地/离线**；
3. 技术栈无偏好，以**方案成熟度**为准；
4. **Speaker diarization 是硬需求**。

## 3. 候选项目深度对比

### 3.1 OpenWhispr（更新后推荐主选）

- **Repo**: https://github.com/OpenWhispr/OpenWhispr
- **License**: MIT — 可商业使用，无 copyleft 顾虑。
- **Stars**: ~4.4k（截至 2026-07-10），持续活跃更新。
- **平台**: macOS（Apple Silicon + Intel）、Windows、Linux。
- **形态**: Electron 桌面应用 + 本地 HTTP bridge（`127.0.0.1:8200–8219`）+ MCP server。
- **录音**: 自动检测 Zoom/Teams/FaceTime，捕获系统音频 + 麦克风；也支持全局热键 dictation。
- **转写**: 本地 `whisper.cpp` 或 NVIDIA Parakeet（via sherpa-onnx），完全离线。
- **Diarization**: README 明确列出 **local speaker diarization** + voice fingerprinting across meetings，无需云端。
- **API**: 提供 Public API（`https://api.openwhispr.com/api/v1`）和 **Local HTTP bridge**。桌面应用运行时 CLI/脚本走 `127.0.0.1` 本地桥，应用关闭时回退到云端。
- **MCP**: 提供 MCP server（`https://mcp.openwhispr.com/mcp`），暴露 `list_transcriptions`、`get_transcription`、`get_note_transcript` 等工具，可被 Claude/Cursor 等调用。
- **优势**: 成熟度明显高于 pasrom；跨平台；MIT；本地 diarization 已可用；有 API/MCP 便于 Lincoln adapter 消费转写结果。
- **劣势**: Electron 应用较重；官方未提供“上传音频文件转写”的公开 REST endpoint，主要面向实时录音/应用内文件转写；本地桥端口和 token 由桌面应用管理，集成时需检测应用是否运行。

### 3.2 Meetly / Meetily-Local

- **Repo**: https://github.com/Zackriya-Solutions/meetily
- **License**: MIT。
- **Stars**: ~22.2k，社区热度最高。
- **形态**: Tauri 桌面应用（Rust + Next.js）。
- **录音**: 本地麦克风 + 系统音频。
- **转写**: Whisper / Parakeet，本地运行。
- **Diarization**: README/PRO 文案显示 **speaker diarization 目前仅规划在 Meetily PRO（mid-June）**，社区版暂未提供。
- **API/CLI**: 当前版本无稳定 CLI 或公开 API；旧版 FastAPI/Docker 后端已归档不再维护。
- **结论**: 协议安全、社区最大，但**当前社区版不满足 diarization 硬需求**，且缺少可编程接口。**不作为直接替换主选**。

### 3.3 anarlog（fastrepl）

- **Repo**: https://github.com/fastrepl/anarlog
- **License**: MIT。
- **Stars**: ~8.8k。
- **形态**: Rust + Tauri 桌面应用，Granola 风格。
- **录音**: 系统音频 + 麦克风；以 Markdown 文件保存笔记到本地磁盘。
- **转写**: 本地 Whisper / Parakeet，BYO LLM（Ollama/LM Studio 等）。
- **Diarization**: 公开资料未强调 speaker diarization，**不满足硬需求**。
- **结论**: 数据控制权极佳（本地 `.md`），但 diarization 缺失，**暂不推荐**。

### 3.4 pasrom/meeting-transcriber（原候选，因成熟度降级）

- **Repo**: https://github.com/pasrom/meeting-transcriber
- **License**: MIT。
- **Stars**: ~19，主要为个人 side project。
- **平台**: macOS 14.2+ Apple Silicon only。
- **录音/转写/diarization**: 功能完整（双音轨 + FluidAudio diarization），并提供 `127.0.0.1:9876` 本地 API。
- **结论**: 技术上最贴合 Lincoln 当前 macOS 环境，但**社区成熟度过低**，维护风险高。仅作为 OpenWhispr 集成失败时的 **macOS-only fallback**。

### 3.5 Vexa

- **Repo**: https://github.com/Vexa-ai/vexa
- **License**: Apache-2.0。
- **形态**: 会议机器人 + 自托管服务端（TypeScript/Playwright/CDP）。
- **结论**: 属于 bot/云端架构，违反“本地桌面录音 + 离线转写”约束。仅作为未来 bot 场景保留。

### 3.6 Millet / ScreenApp / MeetingBot

- **Millet**: GPL-3.0 + Linux-only 音频捕获，排除。
- **ScreenApp Meeting Bot**: MIT，但为 Docker 化 bot，非本地离线，排除。
- **MeetingBot**: LGPL-3.0 + AWS-centric，排除。

## 4. 评分矩阵（1 = 最差，5 = 最好）

| 候选 | License | 成熟度/社区 | 本地/离线 | Diarization | 跨平台 | 可编程集成 | 综合 |
|---|---|---|---|---|---|---|---|
| **OpenWhispr** | 5 (MIT) | 4 (~4.4k stars，活跃) | 5 | 4 | 5 | 4 (本地桥 + MCP) | **4.5** |
| Meetly | 5 (MIT) | 5 (~22.2k stars) | 5 | 1 (社区版无) | 4 | 1 (无 API) | 3.5 |
| anarlog | 5 (MIT) | 4 (~8.8k stars) | 5 | 1 | 2 (macOS 为主) | 2 (Markdown on disk) | 3.0 |
| pasrom/meeting-transcriber | 5 (MIT) | 1 (~19 stars，个人项目) | 5 | 5 | 1 (macOS AS only) | 4 (本地 API) | 3.4 |
| Vexa | 5 (Apache-2.0) | 3 | 2 | 2 | N/A | 5 | 3.4 |
| 保持现状 | 5 | 1 | 5 | 1 | 2 | 3 | 2.8 |

## 5. 推荐方案（修订）

**主选：OpenWhispr + Lincoln adapter**

- OpenWhispr 负责录音、本地离线转写、speaker diarization；
- Lincoln adapter 通过 **Local HTTP bridge** 或 **MCP server** 拉取 transcription/notes；
- 将拉取到的 transcript 标准化为 Lincoln 的 `issue-XX/interviews/<session>/transcript.md`，再触发 `process-interview` 生成摘要与洞察。

**不直接采用 Meetly**：社区版暂未提供 speaker diarization，且缺少可编程接口。

**不直接采用 anarlog**：虽然 star 数和本地 Markdown 存储很吸引人，但缺少成熟 diarization。

**不直接采用 pasrom**：功能匹配，但社区成熟度太低，不符合“以成熟度为准”的约束；仅保留为 macOS-only fallback。

**未来扩展**：若后续需求从本地桌面录音扩展为会议机器人录制，重新评估 **Vexa**。

## 6. 风险与假设

- **Electron 应用较重**：首次安装包体积大、启动资源高于原生 Swift 应用。
- **本地桥需桌面应用运行**：Lincoln adapter 需要检测 OpenWhispr 是否在运行，并提示用户启动；应用关闭时 CLI 可能回退到云端，需在 adapter 中强制本地模式或报错。
- **无官方“上传文件转写”API**： Lincoln 无法直接提交 WAV/M4A 给 OpenWhispr 转写；更适合“用户用 OpenWhispr 录制/导入，Lincoln 拉取结果”的模式。
- **Speaker fingerprint 首次标注**：跨会议说话人识别需要用户在 OpenWhispr UI 中完成首次 voice enrollment。

## 7. 来源

- [OpenWhispr GitHub](https://github.com/OpenWhispr/OpenWhispr)
- [OpenWhispr Docs — API overview](https://docs.openwhispr.com/api/overview)
- [OpenWhispr Docs — MCP](https://docs.openwhispr.com/integrations/mcp)
- [OpenWhispr vs Meetily comparison](https://openwhispr.com/compare/meetily)
- [Meetily GitHub](https://github.com/Zackriya-Solutions/meetily)
- [anarlog GitHub](https://github.com/fastrepl/anarlog)
- [anarlog homepage](https://anarlog.so/)
- [pasrom/meeting-transcriber GitHub](https://github.com/pasrom/meeting-transcriber)
- [Vexa GitHub](https://github.com/Vexa-ai/vexa)
- [Millet GitHub](https://github.com/pretyflaco/millet)
- [ScreenApp Meeting Bot GitHub](https://github.com/screenappai/meeting-bot)
- [MeetingBot GitHub](https://github.com/meetingbot/meetingbot)

---
*PM 确认时请添加 `<!-- status: approved -->` 或 `[x] PM 已确认调研结论`。*
