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
3. 技术栈无偏好，以方案成熟度为准；
4. **Speaker diarization 是硬需求**。

## 3. 候选项目深度对比

### 3.1 pasrom/meeting-transcriber（推荐主选）

- **Repo**: https://github.com/pasrom/meeting-transcriber
- **官网**: https://meetingtranscriber.app/
- **License**: MIT — 可商业使用，无 copyleft 顾虑。
- **平台**: macOS 14.2+ Apple Silicon only。
- **形态**: 菜单栏原生 Swift 应用 + Local Automation API。
- **录音**: 通过 `CATapDescription` 同时捕获应用音频与麦克风（双音轨）。
- **转写**: 本地 WhisperKit（99+ 语言）或 Parakeet TDT v3（25 个欧洲语言，~10× 更快）。
- **Diarization**: 本地 FluidAudio（CoreML/ANE）双音轨 diarization + 说话人识别。
- **API**: Homebrew 构建提供 `127.0.0.1:9876` 本地 HTTP API，`POST /v1/transcribe?include=transcript` 可提交音频文件并获取 diarized transcript。
- **优势**: 完全符合“本地 + 离线 + diarization”约束；有本地 API 可被 Lincoln adapter 调用；MIT 协议友好。
- **劣势**: 仅支持 Apple Silicon macOS 14.2+；需要先运行菜单栏 GUI；API 只能转写已录制文件，不能直接远程“开始录音”；无 Linux/Windows。

### 3.2 Meetly / Meetily-Local

- **Repo**: https://github.com/Zackriya-Solutions/meetily
- **License**: MIT。
- **形态**: Tauri 桌面应用（Rust + Next.js）。
- **录音**: 本地麦克风 + 系统音频。
- **转写**: Whisper / Whisper.cpp / NVIDIA Parakeet，本地运行。
- **Diarization**: 官网与第三方评测均表示 speaker diarization 仍在 roadmap/早期阶段。
- **API/CLI**: 当前版本无稳定 CLI 或公开 API；旧版 FastAPI/Docker 后端已归档不再维护。
- **结论**: 协议安全，但作为 Lincoln 后端缺少可编程接口与成熟 diarization，**不适合作为直接替换**。

### 3.3 Vexa

- **Repo**: https://github.com/Vexa-ai/vexa
- **License**: Apache-2.0。
- **形态**: TypeScript 会议机器人 + 自托管服务端，支持 Docker/Kubernetes。
- **录音**: Playwright/CDP 浏览器机器人加入 Zoom/Meet/Teams 录制。
- **转写**: 实时 WebSocket 转写，云端或自托管。
- **Diarization**: 当前评测为“尚未实现”。
- **结论**: 技术栈与 API-first 设计优秀，但属于**云端/bot 录制**，违反“本地桌面录音 + 离线转写”约束。仅作为未来扩展方向保留。

### 3.4 Millet

- **Repo**: https://github.com/pretyflaco/millet
- **License**: GPL-3.0 — copyleft，纳入 Lincoln 需法律评审。
- **形态**: Python CLI（PyPI: `millet-pipeline`）。
- **录音**: 目前仅支持 Linux PipeWire/PulseAudio；macOS 仅支持后处理（转写/标注）。
- **转写**: WhisperX。
- **Diarization**: pyannote.audio，支持说话人 diarization。
- **结论**: 协议存在 copyleft 风险，且**当前音频捕获不支持 macOS**，与 Lincoln 当前环境不符。

### 3.5 ScreenApp Meeting Bot / MeetingBot

- **ScreenApp**: MIT，Docker 化会议机器人，轻量但属于 bot 云端架构。
- **MeetingBot**: LGPL-3.0，AWS-centric 全栈参考应用。
- **结论**: 均不符合本地离线约束。

### 3.6 保持现状

- 继续维护 `record-interview` + `lincoln` TUI。
- **结论**: 功能与体验均不满足 diarization 与系统音频捕获需求，维护成本高，**不推荐**。

## 4. 评分矩阵（1 = 最差，5 = 最好）

| 候选 | License | 集成成本 | 本地/离线 | Diarization | macOS 适配 | API/CLI | 成熟度 | 综合 |
|---|---|---|---|---|---|---|---|---|
| **pasrom/meeting-transcriber** | 5 (MIT) | 4 | 5 | 5 | 4 (AS only) | 4 | 4 | **4.4** |
| Meetly | 5 (MIT) | 2 | 5 | 2 | 4 | 1 | 3 | 3.1 |
| Meetily-Local fork | 5 (MIT) | 2 | 5 | 2 | 4 | 1 | 2 | 2.8 |
| Vexa | 5 (Apache-2.0) | 4 | 2 | 2 | N/A | 5 | 4 | 3.7 |
| Millet | 1 (GPL-3.0) | 3 | 5 | 4 | 1 (Linux only) | 3 | 2 | 2.6 |
| ScreenApp Meeting Bot | 5 (MIT) | 4 | 2 | 2 | N/A | 3 | 2 | 3.0 |
| MeetingBot | 2 (LGPL-3.0) | 2 | 2 | 2 | N/A | 3 | 3 | 2.6 |
| 保持现状 | 5 | 2 | 5 | 1 | 3 | 3 | 1 | 2.5 |

## 5. 推荐方案

**主选：`pasrom/meeting-transcriber` + Lincoln adapter**

- 由 Meeting Transcriber 负责录音、本地转写与 speaker diarization；
- Lincoln 侧新增 adapter，通过 `127.0.0.1:9876` `/v1/transcribe` 接口消费其输出，或将应用生成的 Markdown 标准化为 `issue-XX/interviews/<session>/` 结构；
- 复用现有 `process-interview` skill 生成 `summary.md` 与 `raw-insights.md`。

**不采用 Meetly**：协议可用，但缺少稳定 API/CLI 与成熟 diarization，无法无感嵌入工作流。

**未来备选**：若需求从本地桌面录音扩展为会议机器人，重新评估 **Vexa**（Apache-2.0、API-first）。

**Fallback**：若目标环境不是 Apple Silicon macOS 14.2+，则基于 WhisperKit/WhisperX + pyannote 自建本地 pipeline，或保留旧 `record-interview` 作为 deprecated fallback。

## 6. 风险与假设

- **Apple Silicon + macOS 14.2+ 门槛**：若 Lincoln 用户含 Intel Mac 或 Linux，主方案不可用。
- **菜单栏 GUI 应用**：需要先运行一个原生应用，非纯 CLI；adapter 需检测运行状态并友好提示。
- **API 仅转写已录制文件**：无法远程开始录音，Lincoln 要么依赖自动会议检测，要么让用户手动触发录制。
- **Speaker DB 只读**：headless API 不会自动注册新说话人，首次标注需在 UI 完成。

## 7. 来源

- [pasrom/meeting-transcriber GitHub](https://github.com/pasrom/meeting-transcriber)
- [Meeting Transcriber 官网](https://meetingtranscriber.app/)
- [Meetily GitHub](https://github.com/Zackriya-Solutions/meetily)
- [Hankanman/Meetily-Local GitHub](https://github.com/Hankanman/Meetily-Local)
- [Vexa GitHub](https://github.com/Vexa-ai/vexa)
- [Millet GitHub](https://github.com/pretyflaco/millet)
- [ScreenApp Meeting Bot GitHub](https://github.com/screenappai/meeting-bot)
- [MeetingBot GitHub](https://github.com/meetingbot/meetingbot)
- [OpenWhispr vs Meetily comparison](https://openwhispr.com/compare/meetily)
- [Meetily review at char.com](https://char.com/blog/meetily-review/)

---
*PM 确认时请添加 `<!-- status: approved -->` 或 `[x] PM 已确认调研结论`。*
