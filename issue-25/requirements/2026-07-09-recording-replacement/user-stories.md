# 用户故事

<!-- status: draft -->

## Issue #25 用户故事

### US-1: 作为 Lincoln 用户，我希望录音能捕获会议应用和麦克风音频
- **验收标准**：
  - 录音输出包含双音轨或已混合的会议音频与麦克风音频。
  - 不再只依赖默认麦克风输入。

### US-2: 作为 Lincoln 用户，我希望转写结果自动区分说话人
- **验收标准**：
  - 转写文本带有 speaker label（Speaker A / Speaker B 或具体人名）。
  - 同一说话人在跨会议场景下可被识别。

### US-3: 作为 Lincoln 维护者，我希望以 OSS 方案替换自研录制工具
- **验收标准**：
  - 录音/转写核心依赖开源项目， Lincoln 侧仅保留 adapter/集成代码。
  - 所选开源项目协议允许纳入 Lincoln（首选 MIT/Apache-2.0，避免 GPL copyleft）。

### US-4: 作为 Lincoln 用户，我希望所有音频和转写都在本地完成
- **验收标准**：
  - 录音文件、转写模型、diarization 均不离开本机。
  - 不强制依赖云端 API。

### US-5: 作为 Lincoln 用户，我希望新方案与现有 interview-to-knowledge 工作流兼容
- **验收标准**：
  - 转写结果可被 `process-interview` skill 消费，生成 `transcript.md`、`summary.md`、`raw-insights.md`。
  - 会话目录结构与现有 `issue-XX/interviews/<session>/` 一致。

---
*PM 确认时请添加 `<!-- status: approved -->` 或 `[x] PM 已确认用户故事`。*
