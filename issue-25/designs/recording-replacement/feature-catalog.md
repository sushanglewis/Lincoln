# 功能目录: recording-replacement

## 功能清单

| 功能编号 | 功能名称 | 优先级 | 验收标准 |
|----------|----------|--------|----------|
| F-001 | 麦克风 + 系统音频录制 | P0 | CLI 能同时捕获双轨并保存为音频文件 |
| F-002 | 本地 Whisper/Parakeet 转写 | P0 | 离线生成带时间戳的转写文本 |
| F-003 | Speaker diarization | P0 | `--diarize` 输出带 speaker label 的 transcript |
| F-004 | 标准 Lincoln interview 输出 | P0 | 输出 `transcript.md` + `metadata.json` 到正确目录 |
| F-005 | 设备列表与选择 | P1 | `devices` 子命令列出可用输入/输出设备 |
| F-006 | 现有音频文件转写 | P1 | `transcribe <file>` 支持 mp3/wav/m4a |
| F-007 | 模型预热 | P1 | `warmup` 预下载 Whisper/pyannote 模型 |
| F-008 | 摘要生成 | P2 | 可选调用本地/远程 LLM 生成会议摘要 |
| F-009 | 跨平台支持 | P2 | v1 支持 macOS；后续支持 Windows/Linux |

## 非功能需求

- **性能**：本地模型推理，Apple Silicon 上优先 Metal/CoreML。
- **安全**：音频、模型、转写结果不离开本机；不硬编码 API key。
- **兼容性**：输出 Markdown 结构与现有 `process-interview` skill 一致。

## 验收映射

- [ ] F-001 对应 design-review 验收标准一
- [ ] F-002 对应 design-review 验收标准二
- [ ] F-003 对应 design-review 验收标准三
- [ ] F-004 对应 design-review 验收标准四
