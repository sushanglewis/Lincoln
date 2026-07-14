use serde::{Deserialize, Serialize};

/// Recording session metadata written alongside `transcript.md`.
#[derive(Clone, Debug, Default, PartialEq, Serialize, Deserialize)]
pub struct SessionMetadata {
    pub session_id: String,
    pub process_slug: String,
    pub started_at: String,
    pub ended_at: Option<String>,
    pub engine: String,
    pub model: String,
    pub diarization: bool,
    pub devices: DeviceInfo,
    pub files: FileInfo,
}

/// Audio devices used for the session.
#[derive(Clone, Debug, Default, PartialEq, Serialize, Deserialize)]
pub struct DeviceInfo {
    pub microphone: String,
    pub system: Option<String>,
}

/// Output file names relative to the session directory.
#[derive(Clone, Debug, Default, PartialEq, Serialize, Deserialize)]
pub struct FileInfo {
    pub transcript: String,
    pub audio: String,
    pub metadata: String,
}
