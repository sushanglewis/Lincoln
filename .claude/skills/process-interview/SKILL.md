---
name: process-interview
description: 处理访谈录音，生成转写、摘要和初始洞察
triggers:
  - "处理访谈录音"
  - "process-interview"
inputs:
  - name: recording_path
    description: 录音文件路径，如 {process_slug}/recordings/2026-06-27-stakeholder.m4a 或 {process_slug}/interviews/{session_id}/audio.wav
    required: true
outputs:
  - "{process_slug}/interviews/{session_id}/metadata.json"
  - "{process_slug}/interviews/{session_id}/transcript.md"
  - "{process_slug}/interviews/{session_id}/summary.md"
  - "{process_slug}/interviews/{session_id}/raw-insights.md"
required_tools:
  - Read
  - Bash
---

# process-interview

处理访谈录音，生成带时间戳与说话人标签的 transcript、summary 和 raw-insights。

录音应优先由 `tools/lincoln-record` 生成，输出到 `{process_slug}/interviews/{session_id}/audio.wav`，然后调用本 skill 进行转写与后处理。

运行入口： prompts/main.md
