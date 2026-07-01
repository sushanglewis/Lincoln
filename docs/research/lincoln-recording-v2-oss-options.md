# Lincoln 录音优化 #14 — 开源方案调研

## 背景与约束

GitHub issue #14 要求优化 Lincoln 的访谈录音功能，本次迭代聚焦：

- **默认录音场景**：PM 使用 MacBook 内置麦克风录制，输入为单声道（mono）音频。
- **转写**：沿用本地 Whisper（`faster-whisper`）；未安装时提示部署或提供 OpenAI API Key 走 Whisper API 兜底。
- **发言人区分**：需要开源、可本地运行的 speaker diarization 方案。
- **处理模式**：不需要实时/流式，不需要录制中分 chunk。录制完成后按 **10 分钟为一段** 批量转写 + 区分发言人 + 生成阶段总结；最终汇总为整体总结。
- **总结**：使用 API LLM，优先通过 `claude` CLI 基于文件路径进行总结，并要求关联仓库知识（`docs/knowledge/`）引用来源。
- **集成语言**：Python，与现有 `tools/record-interview/` 保持一致。
- **许可偏好**：宽松开源许可（MIT/Apache 2.0），避免强制商业 SaaS。

## 候选方案

### 1. pyannote.audio + faster-whisper（推荐主方案）

- **项目**：https://github.com/pyannote/pyannote-audio
- **定位**：业界最主流的 speaker diarization 工具包，提供 `pyannote/speaker-diarization-3.1` / `speaker-diarization-community-1` 预训练流水线。
- **原理**：语音活动检测（VAD）+ 说话人分割 + 说话人嵌入 + 聚类。
- **输入**：自动下混为单声道、重采样至 16kHz，正好适配 MacBook 麦克风。
- **许可**：`pyannote.audio` 自身 MIT；模型 `speaker-diarization-3.1` 为 MIT，`community-1` 为 CC-BY-4.0（需 HuggingFace token 并接受用户协议）。
- **集成方式**：
  1. 用 `faster-whisper` 对整段/10 分钟片段做 ASR，得到带时间戳的文本片段。
  2. 用 `pyannote.audio` 的 `Pipeline.from_pretrained(...)` 得到说话人时间段。
  3. 将 ASR 片段与 diarization 时间段按时间对齐，得到 `Speaker A / Speaker B` 标注的 transcript。
- **优点**：
  - 最成熟、文档完善、社区活跃。
  - 对单声道有专门优化，无需额外硬件。
  - 可设置 `num_speakers` / `min_speakers` / `max_speakers` 约束。
  - CPU 可运行（Apple Silicon 或 Intel Mac 均可）。
- **缺点**：
  - 需要 HuggingFace token 并接受模型用户协议（一次性配置）。
  - PyTorch 依赖较重，首次安装/模型下载体积大。
  - 与 `faster-whisper` 分别维护，需要自行拼接两段结果。

### 2. WhisperX（一站式替代方案）

- **项目**：https://github.com/m-bain/whisperX（主流原版） / https://github.com/stratforge/whisperX（维护分支）
- **定位**：在 faster-whisper 基础上加入 wav2vec 强制对齐、词级时间戳、以及基于 pyannote 的 speaker diarization。
- **原理**：Whisper 转写 → wav2vec2 对齐到词级时间戳 → pyannote diarization → 将词分配到说话人。
- **许可**：BSD-3-Clause（WhisperX 代码）；底层模型同 pyannote。
- **集成方式**：直接调用 `whisperx.load_model()` + `whisperx.DiarizationPipeline()` + `whisperx.assign_word_speakers()`，输出即带 speaker 标签的 segment。
- **优点**：
  - 一次调用即可得到“带时间戳 + 发言人”的完整结果，集成工作量最小。
  - 词级对齐比 Whisper 原生日戳更精准。
  - 社区讨论多，示例丰富。
- **缺点**：
  - 历史版本与 `pyannote.audio 3.0` 存在依赖冲突；需锁定 `pyannote.audio>=3.1` 并验证兼容性。
  - 封装较厚，出错时调试链路更长。
  - 对 batch size / 显存有优化，CPU 上可能不如方案 1 灵活。

### 3. diarize（轻量无账号方案）

- **项目**：https://github.com/FoxNoseTech/diarize
- **定位**：纯 CPU、无需 HuggingFace token/API key、Apache 2.0 的 speaker diarization 库。
- **原理**：Silero VAD → WeSpeaker ResNet34-LM（ONNX） speaker embedding → GMM BIC 估计说话人数 → Spectral Clustering 分配说话人。
- **许可**：Apache 2.0。
- **集成方式**：`pip install diarize` 后直接 `from diarize import DiarizationPipeline`；结合 `faster-whisper` 自行对齐。
- **优点**：
  - 无需 HuggingFace 账号或 token，对终端用户最友好。
  - 号称 VoxConverse dev 加权 DER ~4.8%，CPU 速度 8x 实时。
  - 依赖轻量（ONNX + scikit-learn）。
- **缺点**：
  - 项目较新（2026-02），生态和长期维护尚待观察。
  - 跨数据集泛化能力未经充分验证。
  - 若后续需要微调或企业支持，生态不如 pyannote。

### 4. diart（实时方案，不推荐）

- **项目**：https://github.com/juanmc2005/diart
- **定位**：实时/在线 speaker diarization 框架，基于 pyannote 模型。
- **优点**：低延迟增量 diarization。
- **缺点**：本次迭代不需要实时；实时模型对 MacBook CPU 负担更重；且与录制后批量处理的模式不匹配。
- **结论**：仅作为未来实时扩展的参考，本次不采用。

### 5. 从零实现基线（fallback）

- **思路**：仅依赖 `faster-whisper` 的 timestamp segment，按时间顺序交替标记为 Speaker A / Speaker B；TUI 中允许用户手动修正。
- **优点**：零额外依赖，实现最简单。
- **缺点**：无法真实区分说话人，多说话人场景质量差。
- **结论**：作为 pyannote/diarize 均不可用的降级方案保留，不作为主路径。

## 评分

| 维度 | pyannote + faster-whisper | WhisperX | diarize | 从零实现 |
|---|---|---|---|---|
| **业务适配** | ★★★★☆ 单声道友好，可约束人数 | ★★★★☆ 一站式输出 | ★★★★☆ 无账号，轻量 | ★★☆☆☆ 无法真实区分 |
| **技术适配** | ★★★★☆ 与现有 Whisper 路径自然拼接 | ★★★★★ 集成最简单 | ★★★★☆ 易集成 | ★★★★★ 最简单 |
| **许可** | ★★★★☆ MIT + 模型协议 | ★★★★☆ BSD-3-Clause + 模型协议 | ★★★★★ Apache 2.0 | ★★★★★ 自有代码 |
| **维护活跃度** | ★★★★★ 高 | ★★★★☆ 中（依赖冲突待解决） | ★★★☆☆ 新 | ★★★☆☆ 取决于我们 |
| **集成成本** | ★★★☆☆ 需拼接两段结果 | ★★★★★ 最少 | ★★★★☆ 中等 | ★★★★★ 最低 |
| **MacBook CPU 运行** | ★★★★☆ 可行 | ★★★☆☆ 可行但较重 | ★★★★★ 专为 CPU 优化 | ★★★★★ 最轻 |

## 推荐结论

**主推荐：pyannote.audio + faster-whisper**

- 与 Lincoln 现有本地 Whisper 路径最契合：转写和 diarization 职责清晰，便于分别降级、替换和测试。
- 成熟度最高，文档和社区资源丰富，适合长期维护。
- 对 MacBook 单声道录音有明确支持（自动下混、16kHz 重采样）。

**备选：diarize**

- 如果 PM 或最终用户不希望配置 HuggingFace token，可一键替换为 `diarize`；两者接口可封装在同一 `Diarizer` 协议后。

**不采用 WhisperX 作为主方案的原因**：

- 封装过厚，调试和版本锁定成本高于收益；Lincoln 本身已有 Whisper 转写流程，直接叠加 pyannote 更可控。
- 但仍保留为备选：若后续需要词级对齐或想减少拼接代码，可评估迁移。

## 对实现计划的影响

1. 在 `record_interview/transcriber.py` 中保留 `FasterWhisperTranscriber` 和 `OpenAIWhisperTranscriber`。
2. 新增 `record_interview/diarizer.py`，抽象 `Diarizer` 协议；首批实现：
   - `PyannoteDiarizer`（默认）
   - `DiarizeDiarizer`（无 HF token 备选）
   - `HeuristicDiarizer`（交替 Speaker A/B 降级）
3. 录制完成后，将音频按 10 分钟切片；每片依次执行 `transcribe → diarize → align speaker labels → write transcript segment`。
4. 阶段总结基于切片后的 transcript segment 生成，最终汇总为 `summary.md`。
5. 若本地 `faster-whisper` 未安装，TUI Setup 屏幕提示安装命令；若同时未配置 OpenAI API Key，则阻止进入 Recording。
