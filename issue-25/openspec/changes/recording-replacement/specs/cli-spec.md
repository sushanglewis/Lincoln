# Spec: CLI Arguments and Configuration

## Command: `record`

```text
lincoln-record record
  --session-id <SESSION>
  [--mic <DEVICE>]
  [--system-auto]
  [--engine whisper|parakeet]
  [--model <NAME>]
  [--diarize]
  [--output <DIR>]
  [--language <LANG>]
```

## Command: `transcribe`

```text
lincoln-record transcribe <PATH>
  [--session-id <SESSION>]
  [--engine whisper|parakeet]
  [--model <NAME>]
  [--diarize]
  [--output <DIR>]
```

## Configuration File

Path: `~/.config/lincoln-record/config.toml`

```toml
[audio]
sample_rate = 48000
channels = 2

[transcription]
engine = "whisper"
model = "large-v3-turbo"
language = "auto"

[diarization]
enabled = false
hf_token = ""  # required when enabled

[output]
format = "markdown"
keep_recording = true
```

## Error Handling

- Missing `--session-id` for `record`: exit code 1 with usage hint.
- No microphone available: exit code 3.
- Missing HF token with `--diarize`: exit code 1 with config hint.
