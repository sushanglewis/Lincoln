use anyhow::Context;
use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};

/// Top-level configuration for `lincoln-record`.
#[derive(Clone, Debug, Default, PartialEq, Serialize, Deserialize)]
pub struct Config {
    #[serde(default)]
    pub audio: AudioConfig,
    #[serde(default)]
    pub transcription: TranscriptionConfig,
    #[serde(default)]
    pub diarization: DiarizationConfig,
    #[serde(default)]
    pub output: OutputConfig,
    #[serde(default)]
    pub model_cache_dir: Option<std::path::PathBuf>,
}

/// Audio capture and pipeline settings.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct AudioConfig {
    #[serde(default = "default_sample_rate")]
    pub sample_rate: u32,
    #[serde(default = "default_channels")]
    pub channels: u16,
}

/// Transcription engine settings.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct TranscriptionConfig {
    #[serde(default = "default_engine")]
    pub engine: String,
    #[serde(default = "default_model")]
    pub model: String,
    #[serde(default = "default_language")]
    pub language: String,
}

/// Speaker diarization settings.
#[derive(Clone, Debug, Default, PartialEq, Serialize, Deserialize)]
pub struct DiarizationConfig {
    #[serde(default)]
    pub enabled: bool,
    #[serde(default)]
    pub hf_token: String,
}

/// Output formatting and retention settings.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct OutputConfig {
    #[serde(default = "default_output_format")]
    pub format: String,
    #[serde(default = "default_keep_recording")]
    pub keep_recording: bool,
}

impl Default for AudioConfig {
    fn default() -> Self {
        Self {
            sample_rate: 48000,
            channels: 2,
        }
    }
}

impl Default for TranscriptionConfig {
    fn default() -> Self {
        Self {
            engine: default_engine(),
            model: default_model(),
            language: default_language(),
        }
    }
}

impl Default for OutputConfig {
    fn default() -> Self {
        Self {
            format: "markdown".to_string(),
            keep_recording: true,
        }
    }
}

impl Config {
    /// Load configuration from `path`. Returns defaults if the file is missing.
    pub fn load_from_path<P: AsRef<Path>>(path: P) -> anyhow::Result<Self> {
        let path = path.as_ref();
        if !path.exists() {
            return Ok(Self::default());
        }
        let contents = std::fs::read_to_string(path)
            .with_context(|| format!("failed to read config: {}", path.display()))?;
        let config: Config = toml::from_str(&contents)
            .with_context(|| format!("failed to parse config: {}", path.display()))?;
        Ok(config)
    }

    /// Load configuration from `~/.lincolnrc`, falling back to defaults.
    pub fn load() -> anyhow::Result<Self> {
        let path = dirs::home_dir()
            .map(|home| home.join(".lincolnrc"))
            .unwrap_or_else(|| PathBuf::from(".lincolnrc"));
        Self::load_from_path(path)
    }
}

fn default_sample_rate() -> u32 {
    48000
}

fn default_channels() -> u16 {
    2
}

fn default_engine() -> String {
    "whisper".to_string()
}

fn default_model() -> String {
    "large-v3".to_string()
}

fn default_language() -> String {
    "auto".to_string()
}

fn default_output_format() -> String {
    "markdown".to_string()
}

fn default_keep_recording() -> bool {
    true
}
