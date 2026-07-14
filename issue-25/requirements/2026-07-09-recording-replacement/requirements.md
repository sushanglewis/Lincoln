# 需求文档: 2026-07-09-recording-replacement

<!-- status: approved -->

## 背景

- Issue: #25
- 当前 Lincoln 录音链路依赖 `tools/record-interview`（Python/ffmpeg 麦克风录制）+ `tools/lincoln`（Ink TUI）+ `.claude/skills/process-interview`（提示词驱动转写）。该链路只能捕获默认麦克风、无系统/会议音频、TUI 音量条为 mock、转写未自动化，且为 macOS-only。
- 目标：以 OSS 优先的方式替换自研录音工具，先更好集成到 Lincoln 工作流，再考虑基于场景的改造。

## 问题

1. 自研录音组件功能薄弱、维护成本高，且无法产出带说话人区分的转写。
2. 需要评估开源方案（包括 Meetly）的许可协议是否可纳入 Lincoln 项目。
3. 需要明确替换后的集成方式、数据流和 fallback 策略。

## 用户

- Lincoln 的使用者（产品经理、设计师、研发）在进行访谈或会议录音时需要稳定、离线、带 diarization 的录音/转写能力。
- Lincoln 框架维护者希望减少自研录制代码，转向成熟开源方案。

## 方案

1. **首选方案**：采用 `pasrom/meeting-transcriber`（MIT License）作为本地录音+转写+speaker diarization 引擎，Lincoln 侧新增 adapter 消费其输出。
   - 理由：本地/离线、支持 Apple Silicon macOS、具备双音轨 diarization、提供本地 HTTP API 便于工作流集成、MIT 协议无 copyleft 顾虑。
2. **不采用 Meetly 作为直接替换**：MIT License 可用，但当前版本无稳定 CLI/API，speaker diarization 未成熟，无法无感嵌入 Lincoln。
3. **未来扩展**：若后续需求从“本地桌面录音”扩展为“会议机器人录制”，可重新评估 Vexa（Apache-2.0、API-first）。
4. **Fallback**：在 macOS 14.2+ Apple Silicon 环境不可用或需跨平台时，基于 WhisperKit/WhisperX + pyannote 自建本地 pipeline；旧 `tools/record-interview` 保留 deprecated 状态直到新链路稳定。

## 验收标准

- [ ] 完成对现有录音链路的梳理和痛点分析。
- [ ] 产出候选开源方案对比文档，覆盖协议、集成成本、平台、diarization、API/CLI、成熟度。
- [ ] 明确推荐方案及不采用其他方案的理由，形成决策记录（ADR）。
- [ ] 完成 PoC：通过 `pasrom/meeting-transcriber` 的 Local Automation API 获取 diarized transcript，并能被 `process-interview` 消费生成 Lincoln 标准 interview 产物。
- [ ] 产出集成设计文档，定义 Lincoln adapter 的接口、数据流、错误处理与 fallback 机制。
- [ ] 后续实现阶段基于设计文档产出 TDD 计划与 OpenSpec 变更提案。

---
*PM 确认时请添加 `<!-- status: approved -->` 或 `[x] PM 已确认需求`。*
