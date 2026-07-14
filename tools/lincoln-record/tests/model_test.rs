use lincoln_record::config::Config;
use lincoln_record::model::resolve_model_path;
use std::path::PathBuf;

#[test]
fn test_config_loads_model_cache_dir() {
    let config: Config = toml::from_str(
        r#"
model_cache_dir = "/custom/cache"
[transcription]
engine = "whisper"
model = "small"
"#,
    )
    .unwrap();
    assert_eq!(
        config.model_cache_dir,
        Some(PathBuf::from("/custom/cache"))
    );
    assert_eq!(config.transcription.model, "small");
}

#[test]
fn test_resolve_model_path_uses_absolute_cli_path() {
    let config = Config::default();
    let path = PathBuf::from("/absolute/ggml-custom.bin");
    let resolved = resolve_model_path(Some(&path), &config).unwrap();
    assert_eq!(resolved, path);
}

#[test]
fn test_resolve_model_path_uses_name_from_config() {
    let mut config = Config::default();
    config.model_cache_dir = Some(PathBuf::from("/cache"));
    config.transcription.model = "tiny".to_string();

    let resolved = resolve_model_path(None, &config).unwrap();
    assert_eq!(
        resolved,
        PathBuf::from("/cache/whisper/ggml-tiny.bin")
    );
}

#[test]
fn test_resolve_model_path_cli_name_overrides_config() {
    let mut config = Config::default();
    config.model_cache_dir = Some(PathBuf::from("/cache"));
    config.transcription.model = "large".to_string();

    let resolved = resolve_model_path(Some(PathBuf::from("base").as_path()), &config).unwrap();
    assert_eq!(
        resolved,
        PathBuf::from("/cache/whisper/ggml-base.bin")
    );
}

#[test]
fn test_resolve_model_path_missing_returns_error_with_url() {
    let mut config = Config::default();
    config.model_cache_dir = Some(PathBuf::from("/cache"));
    config.transcription.model = "missing-model".to_string();

    let err = resolve_model_path(None, &config).unwrap_err();
    let msg = format!("{}", err);
    assert!(msg.contains("missing-model"));
    assert!(msg.contains("huggingface"));
    assert!(msg.contains("lincoln-record warmup"));
}
