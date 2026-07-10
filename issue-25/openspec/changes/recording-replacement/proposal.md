# OpenSpec Proposal: recording-replacement

## Summary

Replace Lincoln's current self-built recording stack (`tools/record-interview` + `tools/lincoln` TUI) with a headless CLI recorder inspired by Meetily's Rust backend design. The new tool, `lincoln-record`, captures microphone + system audio locally, transcribes offline with Whisper/Parakeet, performs speaker diarization via a Python sidecar (WhisperX + pyannote), and outputs Lincoln-standard interview artifacts.

## Motivation

Current pain points:
- Records only default microphone, no system/meeting audio.
- TUI audio meter is mocked.
- Transcription is manual; nested `claude` subprocess is brittle.
- macOS-only and hard to maintain.

This change addresses LEW-17 / GitHub issue #25.

## Scope

- Build `tools/lincoln-record/` Rust CLI.
- Implement macOS audio capture (microphone + system audio via Core Audio Tap).
- Integrate local Whisper/Parakeet transcription.
- Add speaker diarization through Python post-processing.
- Output `transcript.md` + `metadata.json` compatible with `process-interview`.
- Adapt `tools/lincoln` TUI to spawn `lincoln-record`.
- Deprecate `tools/record-interview`.

## Out of Scope

- Cloud transcription or meeting-bot capture.
- Windows/Linux audio capture in v1.
- UI beyond the existing Lincoln TUI integration.

## Success Criteria

- `lincoln-record record --diarize` produces a diarized `transcript.md` on macOS.
- `cargo test` passes with ≥ 80% coverage.
- End-to-end flow works: record → transcript → `process-interview` → summary.
- No hardcoded secrets; all processing stays local by default.

## References

- `issue-25/designs/recording-replacement/design-review.md`
- `issue-25/designs/recording-replacement/tdd-plan.md`
- `issue-25/docs/research/recording-replacement-oss-options.md`
