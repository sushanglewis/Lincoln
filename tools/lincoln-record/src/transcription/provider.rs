use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::path::Path;

/// A single transcript segment with timing and optional speaker label.
#[derive(Clone, Debug, Default, PartialEq, Serialize, Deserialize)]
pub struct TranscriptSegment {
    pub start: f64,
    pub end: f64,
    pub speaker: Option<String>,
    pub text: String,
}

/// Abstraction over local transcription engines.
pub trait TranscriptionProvider: Send + Sync {
    /// Transcribe `audio_path` and return segments ordered by time.
    fn transcribe(
        &self,
        audio_path: &Path,
        language: Option<&str>,
    ) -> Result<Vec<TranscriptSegment>>;
}

/// A deterministic provider for tests and development.
pub struct MockProvider {
    segments: Vec<TranscriptSegment>,
}

impl MockProvider {
    pub fn new(segments: Vec<TranscriptSegment>) -> Self {
        Self { segments }
    }
}

impl TranscriptionProvider for MockProvider {
    fn transcribe(
        &self,
        _audio_path: &Path,
        _language: Option<&str>,
    ) -> Result<Vec<TranscriptSegment>> {
        Ok(self.segments.clone())
    }
}
