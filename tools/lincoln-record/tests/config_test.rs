use lincoln_record::config::Config;
use std::io::Write;

#[test]
fn test_config_defaults() {
    let config = Config::default();
    assert_eq!(config.audio.sample_rate, 48000);
    assert_eq!(config.audio.channels, 2);
    assert_eq!(config.transcription.engine, "whisper");
    assert_eq!(config.transcription.model, "large-v3");
    assert_eq!(config.transcription.language, "auto");
    assert!(!config.diarization.enabled);
    assert_eq!(config.diarization.hf_token, "");
    assert_eq!(config.output.format, "markdown");
    assert!(config.output.keep_recording);
}

#[test]
fn test_config_loads_from_toml_file() {
    let mut tmp = tempfile::NamedTempFile::new().expect("temp file");
    write!(
        tmp,
        r#"
[audio]
sample_rate = 16000
channels = 1

[transcription]
engine = "parakeet"
model = "parakeet-tiny"
language = "zh"

[diarization]
enabled = true
hf_token = "hf_xxx"

[output]
format = "json"
keep_recording = false
"#
    )
    .expect("write config");

    let config = Config::load_from_path(tmp.path()).expect("load config");
    assert_eq!(config.audio.sample_rate, 16000);
    assert_eq!(config.audio.channels, 1);
    assert_eq!(config.transcription.engine, "parakeet");
    assert_eq!(config.transcription.model, "parakeet-tiny");
    assert_eq!(config.transcription.language, "zh");
    assert!(config.diarization.enabled);
    assert_eq!(config.diarization.hf_token, "hf_xxx");
    assert_eq!(config.output.format, "json");
    assert!(!config.output.keep_recording);
}

#[test]
fn test_config_load_missing_file_falls_back_to_defaults() {
    let config = Config::load_from_path(std::path::Path::new("/nonexistent/lincoln-record.toml"))
        .expect("missing file should fall back to defaults");
    assert_eq!(config.audio.sample_rate, 48000);
    assert_eq!(config.output.format, "markdown");
}

#[test]
fn test_config_rejects_invalid_toml() {
    let mut tmp = tempfile::NamedTempFile::new().expect("temp file");
    write!(tmp, "not valid toml [[[").expect("write invalid config");
    let result = Config::load_from_path(tmp.path());
    assert!(result.is_err(), "invalid TOML should error");
}
