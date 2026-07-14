use crate::transcription::provider::TranscriptSegment;
use anyhow::{Context, Result};
use std::path::Path;
use std::process::Command;

/// Run the Python diarization sidecar on `audio_path` and merge the result with
/// `transcript_segments`. Returns a new segment list with speaker labels.
pub fn diarize_and_merge(
    audio_path: &Path,
    transcript_segments: &[TranscriptSegment],
    work_dir: &Path,
) -> Result<Vec<TranscriptSegment>> {
    let transcript_json = work_dir.join("transcripts.json");
    let diarization_json = work_dir.join("diarization.json");
    let merged_json = work_dir.join("merged.json");

    std::fs::write(
        &transcript_json,
        serde_json::to_string_pretty(transcript_segments)?,
    )
    .with_context(|| "failed to write transcripts.json")?;

    let project_root = Path::new(env!("CARGO_MANIFEST_DIR"));
    let diarize_script = project_root.join("diarize/diarize.py");
    let merge_script = project_root.join("diarize/merge.py");

    let diarize_output = Command::new("python3")
        .arg(&diarize_script)
        .arg(audio_path)
        .arg("--output")
        .arg(&diarization_json)
        .output()
        .with_context(|| format!("failed to execute {}", diarize_script.display()))?;
    if !diarize_output.status.success() {
        anyhow::bail!(
            "{} failed: {}",
            diarize_script.display(),
            String::from_utf8_lossy(&diarize_output.stderr)
        );
    }

    let merge_output = Command::new("python3")
        .arg(&merge_script)
        .arg(&transcript_json)
        .arg(&diarization_json)
        .arg("--output")
        .arg(&merged_json)
        .output()
        .with_context(|| format!("failed to execute {}", merge_script.display()))?;
    if !merge_output.status.success() {
        anyhow::bail!(
            "{} failed: {}",
            merge_script.display(),
            String::from_utf8_lossy(&merge_output.stderr)
        );
    }

    let raw = std::fs::read_to_string(&merged_json)
        .with_context(|| format!("failed to read {}", merged_json.display()))?;
    let segments: Vec<TranscriptSegment> =
        serde_json::from_str(&raw).with_context(|| "failed to parse merged diarization json")?;

    Ok(segments)
}
