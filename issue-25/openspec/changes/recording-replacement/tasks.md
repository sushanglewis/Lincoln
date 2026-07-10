# OpenSpec Tasks: recording-replacement

## Phase 1 — CLI Skeleton
- [ ] Initialize `tools/lincoln-record/` Rust crate with `clap` and `tokio`.
- [ ] Implement `devices` subcommand using `cpal`.
- [ ] Implement configuration loading and defaults.
- [ ] Add unit tests for CLI argument parsing and config.

## Phase 2 — Audio Capture
- [ ] Implement microphone capture with `cpal`.
- [ ] Implement macOS system audio capture via `cidre` Core Audio tap.
- [ ] Implement audio pipeline mixing and VAD integration.
- [ ] Implement checkpoint saver and ffmpeg merge.
- [ ] Add integration tests with fixture audio.

## Phase 3 — Transcription
- [ ] Define `TranscriptionProvider` trait.
- [ ] Implement Whisper provider with `whisper-rs`.
- [ ] Implement Parakeet provider with `ort`.
- [ ] Implement transcription worker and `transcribe` subcommand.
- [ ] Add tests for transcript formatting.

## Phase 4 — Diarization
- [ ] Create Python sidecar `diarize/whisperx_diarize.py`.
- [ ] Create `diarize/merge.py` for result combination.
- [ ] Wire Rust CLI to invoke sidecar when `--diarize` is set.
- [ ] Add tests using fixture audio with two speakers.

## Phase 5 — Lincoln Integration
- [ ] Implement `metadata.json` and `transcript.md` output formatter.
- [ ] Update `tools/lincoln/src/recording/spawnRecorder.ts` to call `lincoln-record`.
- [ ] Run end-to-end test: record/transcribe → `process-interview`.

## Phase 6 — Cleanup & Documentation
- [ ] Mark `tools/record-interview` as deprecated.
- [ ] Update `.claude/skills/process-interview/SKILL.md`.
- [ ] Update root README installation section.
- [ ] Ensure `cargo test` coverage ≥ 80%.
