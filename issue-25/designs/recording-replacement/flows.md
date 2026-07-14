# 流程图: recording-replacement

## 主流程

```mermaid
graph TD
    A[用户运行 lincoln-record record] --> B[解析设备与参数]
    B --> C[启动 Audio Pipeline]
    C --> D[捕获麦克风 + 系统音频]
    D --> E[VAD 检测语音段]
    E --> F[实时 Whisper/Parakeet 转写]
    F --> G[用户停止录制]
    G --> H[合并音频 checkpoints]
    H --> I[Python 后处理 diarization]
    I --> J[生成 transcript.md + metadata.json]
    J --> K[ Lincoln process-interview 生成 summary]
```

## 分支流程

### 已有音频文件处理

```mermaid
graph TD
    A[lincoln-record transcribe file.wav] --> B[提取音频]
    B --> C[Whisper/Parakeet 转写]
    C --> D{启用 --diarize?}
    D -->|是| E[pyannote diarization]
    D -->|否| F[无 speaker label]
    E --> G[生成 transcript.md]
    F --> G
```

## 状态机

- `idle` → `recording`（`record` 命令）
- `recording` → `processing`（停止录制）
- `processing` → `done`（生成输出）
- `processing` → `partial`（diarization 失败但转写成功）
