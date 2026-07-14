# PRD: 录音工具 OSS 替换

<!-- status: draft -->

## 目标

将 Lincoln 当前自研的录音/转写链路替换为以开源项目为核心的方案，实现本地、离线、带 speaker diarization 的会议/访谈录制，并无缝集成到 Lincoln 的 interview-to-knowledge 工作流。

## 范围

- **In scope**：
  - 开源录音/转写方案调研与选型。
  - Lincoln adapter 的设计与实现。
  - 与 `process-interview` skill 的 transcript 消费对接。
  - 旧 `tools/record-interview` 与 `tools/lincoln` 录制链路的 deprecate 策略。
- **Out of scope**（本阶段）：
  - 会议机器人（bot）加入 Zoom/Meet/Teams 的云端录制。
  - 跨平台支持（Linux/Windows）。
  - 实时字幕/UI 重设计。

## 用户场景

1. **访谈录制**：用户运行 Lincoln CLI 创建会话，系统自动使用新录音引擎捕获访谈音频并转写。
2. **会议后处理**：用户使用 `pasrom/meeting-transcriber` 录制会议，Lincoln adapter 将其输出导入对应 issue 工作包。
3. **知识沉淀**：转写结果经 `process-interview` 生成摘要与洞察，写入 `knowledge/`。

## 功能需求

| ID | 功能 | 优先级 | 说明 |
|---|---|---|---|
| FR-1 | 本地音频捕获 | P0 | 捕获系统/应用音频 + 麦克风 |
| FR-2 | 离线转写 | P0 | 使用本地 Whisper/WhisperKit/Parakeet |
| FR-3 | Speaker diarization | P0 | 区分说话人 |
| FR-4 | Lincoln adapter | P0 | 将开源方案输出标准化为 Lincoln interview 产物 |
| FR-5 | 与现有 CLI/TUI 集成 | P1 | 在 `tools/lincoln` 中调用 adapter 或提示用户启动外部应用 |
| FR-6 | Fallback 机制 | P1 | 在目标环境不可用时回退到旧方案或提示 |
| FR-7 | 协议合规 | P0 | 仅使用与 Lincoln 兼容的开源协议 |

## 非功能需求

- **隐私**：音频、模型、转写结果均保留在本地。
- **许可**：首选 MIT/Apache-2.0；GPL/LGPL 需法律评审，默认不采用。
- **可维护性**：adapter 代码量小，依赖外部应用通过 Homebrew 安装。
- **稳定性**：PoC 验证端到端流程后再替换旧链路。

## 成功指标

- 新链路能在目标 Mac（Apple Silicon, macOS 14.2+）上完成一次完整录音→转写→知识沉淀。
- 转写结果包含 speaker label。
- 旧录制链路标记 deprecated，但不影响现有用户。

---
*PM 确认时请添加 `<!-- status: approved -->` 或 `[x] PM 已确认PRD`。*
