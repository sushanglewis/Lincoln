use serde::{Deserialize, Serialize};
use std::path::Path;

#[derive(Debug, Default, Clone, Serialize, Deserialize, PartialEq)]
pub struct Config {
    #[serde(default)]
    pub audio: AudioConfig,
    #[serde(default)]
    pub transcription: TranscriptionConfig,
    #[serde(default)]
    pub diarization: DiarizationConfig,
    #[serde(default)]
    pub output: OutputConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct AudioConfig {
    #[serde(default = "default_sample_rate")]
    pub sample_rate: u32,
    #[serde(default = "default_channels")]
    pub channels: u16,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct TranscriptionConfig {
    #[serde(default = "default_engine")]
    pub engine: String,
    #[serde(default = "default_model")]
    pub model: String,
    #[serde(default = "default_language")]
    pub language: String,
}

#[derive(Debug, Default, Clone, Serialize, Deserialize, PartialEq)]
pub struct DiarizationConfig {
    #[serde(default)]
    pub enabled: bool,
    #[serde(default)]
    pub hf_token: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
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
            engine: "whisper".to_string(),
            model: "large-v3-turbo".to_string(),
            language: "auto".to_string(),
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
    pub fn load_from_path<P: AsRef<Path>>(path: P) -> anyhow::Result<Self> {
        let path = path.as_ref();
        if !path.exists() {
            return Ok(Self::default());
        }
        let contents = std::fs::read_to_string(path)?;
        let config: Config = toml::from_str(&contents)?;
        Ok(config)
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
    "large-v3-turbo".to_string()
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
