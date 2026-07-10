# 场景分析: recording-replacement

## 用户画像

- **PM/设计师/研发**：需要在访谈或会议后快速得到带说话人区分的转写和摘要。
- **Lincoln 维护者**：希望减少自研录音代码，转向成熟开源方案。

## 核心场景

### 场景一：访谈录制并自动生成知识沉淀

- **触发条件**：用户准备进行一次利益相关者访谈。
- **用户行为**：
  1. 在 Lincoln 工作包下创建会话；
  2. 运行 `lincoln-record record --session-id ...`；
  3. 访谈结束后按 Ctrl+C 停止。
- **预期结果**：
  - 生成 `transcript.md`（带 speaker label）；
  - `claude process-interview` 自动生成 `summary.md` 和 `raw-insights.md`。

### 场景二：处理已有会议录音

- **触发条件**：用户拿到一段历史会议录音（MP3/WAV）。
- **用户行为**：运行 `lincoln-record transcribe meeting.wav --session-id ...`。
- **预期结果**：同样得到标准 Lincoln interview 产物。

## 边界场景

- 用户未授权麦克风/屏幕录制权限：CLI 应清晰提示并退出。
- 系统音频不可用（如 Linux 无 PulseAudio）：回退到仅麦克风录制或报错。
- 模型首次下载无网络：提示用户先运行 `lincoln-record warmup`。

## 异常场景

- 录制过程中设备断开：保存已录制片段并返回错误码。
- Diarization 失败：保留无 speaker label 的转写，避免阻塞整条链路。
