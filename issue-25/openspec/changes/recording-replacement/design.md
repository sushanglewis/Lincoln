# OpenSpec Design: recording-replacement

## Architecture

See `issue-25/designs/recording-replacement/design-review.md` for full architecture diagram.

```
Lincoln CLI/TUI
      |
      v
lincoln-record (Rust CLI)
  |-- audio pipeline (cpal + cidre Core Audio tap)
  |-- transcription (whisper-rs / ort Parakeet)
  |-- output formatter
  |-- Python sidecar (WhisperX + pyannote diarization)
      |
      v
issue-XX/interviews/<session>/
  |-- transcript.md
  |-- metadata.json
  |-- audio.mp4
      |
      v
process-interview -> summary.md / raw-insights.md
```

## Components

### 1. CLI Layer (`src/main.rs`, `src/cli.rs`)
- Subcommands: `record`, `stop`, `transcribe`, `devices`, `warmup`.
- Configuration via CLI flags and `~/.config/lincoln-record/config.toml`.

### 2. Audio Capture (`src/audio/`)
- `capture/microphone.rs`: `cpal` input stream.
- `capture/system_macos.rs`: `cidre` Core Audio global tap.
- `pipeline.rs`: chunk buffering, mixing, VAD gating.
- `saver.rs`: 30-second checkpoints + ffmpeg merge.

### 3. Transcription (`src/transcription/`)
- Trait `TranscriptionProvider`.
- `whisper_provider.rs`: `whisper-rs` inference.
- `parakeet_provider.rs`: `ort` + Parakeet ONNX.

### 4. Diarization Sidecar (`diarize/`)
- `whisperx_diarize.py`: run WhisperX alignment + pyannote segmentation.
- `merge.py`: combine diarization output with transcript segments.

### 5. Output (`src/output/`)
- `metadata.rs`: `metadata.json` schema.
- `transcript.rs`: `transcript.md` formatting.

### 6. Lincoln Adapter
- Update `tools/lincoln/src/recording/spawnRecorder.ts` to invoke `lincoln-record`.
- Preserve session-id validation and metadata conventions from `record-interview`.

## Data Flow

1. User starts `record` with session ID and device options.
2. Audio pipeline captures chunks, applies VAD, sends speech segments to transcription worker.
3. Transcription worker emits `TranscriptSegment` structs with timestamps.
4. On stop, saver merges checkpoints into `audio.mp4`.
5. If `--diarize`, Rust CLI invokes Python sidecar on the audio file.
6. Python returns speaker mappings; Rust merges into final `transcript.md`.
7. `metadata.json` is written alongside the transcript.

## Interface Contracts

### CLI Exit Codes
- `0`: success
- `1`: generic error
- `2`: missing permissions
- `3`: no available audio device
- `4`: model download failed

### `transcript.md` Format
- Header with session ID.
- Speakers list.
- Timestamped lines: `**[HH:MM:SS] Speaker X**: text`.

### `metadata.json` Schema
See `issue-25/designs/recording-replacement/data-model.md`.
