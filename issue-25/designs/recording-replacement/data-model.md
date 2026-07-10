# 数据模型: recording-replacement

## 实体

### Session（一次录制会话）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| session_id | string | PK | 如 `2026-07-10-stakeholder` |
| process_slug | string | FK | 关联的 Lincoln issue 工作包 |
| started_at | datetime | 必填 | 录制开始时间 |
| ended_at | datetime | 可选 | 录制结束时间 |
| engine | string | 必填 | `whisper` / `parakeet` |
| model | string | 必填 | 模型名，如 `large-v3-turbo` |
| diarization | boolean | 必填 | 是否启用 diarization |
| devices | object | 必填 | `{microphone, system}` |
| files | object | 必填 | `{transcript, audio, metadata}` |

### Transcript Segment（转写片段）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| start | float | 必填 | 相对录音开始的时间（秒） |
| end | float | 必填 | 结束时间（秒） |
| speaker | string | 可选 | 说话人标识 |
| text | string | 必填 | 转写文本 |

### Output Files

| 文件 | 说明 |
|------|------|
| `transcript.md` | 带 speaker label 的 Markdown 转写 |
| `metadata.json` | Session 元数据 |
| `audio.mp4` | 合并后的录音（可选保留） |

## 关系

- 一个 Session 包含多个 Transcript Segment：一对多。
- Session 属于一个 Lincoln issue 工作包：多对一。

## 约束

- `session_id` 必须符合 `YYYY-MM-DD-descriptive-name` 格式。
- 输出目录必须在对应 `issue-XX/interviews/` 下。
- 如果 diarization 失败，speaker 字段允许为空，但 transcript 必须保留。
