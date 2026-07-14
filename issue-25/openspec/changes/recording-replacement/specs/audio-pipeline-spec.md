# Spec: Audio Pipeline

## Inputs

- Microphone stream via `cpal`.
- System audio stream via `cidre` Core Audio tap (macOS).

## Pipeline Stages

1. **Capture** — raw f32 PCM chunks at device sample rate.
2. **Resample** — unify to 48 kHz using `rubato`.
3. **Mix** — sum mic + system streams with soft clipping.
4. **Enhance** — apply RNNoise noise suppression to mic path; EBU R128 loudness normalization.
5. **VAD** — `silero_rs` detects speech segments.
6. **Segment** — forward speech windows to transcription worker.
7. **Save** — write mixed audio to 30-second checkpoints; merge on stop.

## Output

- `audio.mp4` — AAC-encoded final recording.
- `transcripts.json` — intermediate segments with timestamps.

## Concurrency

- Audio capture and transcription run on separate tokio tasks.
- Communication via lock-free ring buffer + unbounded channel.
