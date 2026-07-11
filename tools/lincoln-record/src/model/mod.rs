use crate::config::Config;
use anyhow::{Context, Result};
use std::io::{Read, Write};
use std::path::{Path, PathBuf};

const HUGGINGFACE_BASE: &str = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main";

/// Known Whisper model names and their published filenames.
fn model_filename(name: &str) -> Option<&str> {
    match name {
        "tiny" => Some("ggml-tiny.bin"),
        "base" => Some("ggml-base.bin"),
        "small" => Some("ggml-small.bin"),
        "medium" => Some("ggml-medium.bin"),
        "large-v1" => Some("ggml-large-v1.bin"),
        "large-v2" => Some("ggml-large-v2.bin"),
        "large-v3" => Some("ggml-large-v3.bin"),
        "large-v3-turbo" => Some("ggml-large-v3-turbo.bin"),
        _ => None,
    }
}

fn model_url(name: &str) -> Option<String> {
    model_filename(name).map(|file| format!("{}/{}", HUGGINGFACE_BASE, file))
}

fn model_name_from_arg(model_arg: Option<&Path>) -> String {
    model_arg
        .and_then(|path| {
            if path.is_file() || looks_like_file_path(path) {
                // File paths are handled separately; do not treat them as model names.
                None
            } else {
                path.file_name().and_then(|name| name.to_str()).map(|s| s.to_string())
            }
        })
        .unwrap_or_default()
}

fn looks_like_file_path(path: &Path) -> bool {
    path.extension().is_some()
        || path
            .parent()
            .map(|parent| !parent.as_os_str().is_empty())
            .unwrap_or(false)
}

/// Return the default model-cache directory (`~/.cache/lincoln/models`).
pub fn default_cache_dir() -> PathBuf {
    dirs::home_dir()
        .map(|home| home.join(".cache").join("lincoln").join("models"))
        .unwrap_or_else(|| PathBuf::from(".lincoln").join("cache").join("models"))
}

/// Resolve the absolute path to the Whisper model.
///
/// Priority:
/// 1. `model_arg` if it points to an existing file.
/// 2. `model_arg` as a model name inside the cache directory.
/// 3. `config.transcription.model` as a model name inside the cache directory.
///
/// Returns an error with download instructions if the file is missing.
pub fn resolve_model_path(model_arg: Option<&Path>, config: &Config) -> Result<PathBuf> {
    let cache_dir = config
        .model_cache_dir
        .clone()
        .unwrap_or_else(default_cache_dir);
    let engine = config.transcription.engine.clone();

    if let Some(path) = model_arg.filter(|p| p.is_file() || looks_like_file_path(p)) {
        return Ok(path.to_path_buf());
    }

    let model_name = model_name_from_arg(model_arg);
    let model_name = if model_name.is_empty() {
        config.transcription.model.as_str()
    } else {
        model_name.as_str()
    };

    let path = cache_path_for_model(model_name, &engine, &cache_dir);

    if model_filename(model_name).is_some() {
        return Ok(path);
    }

    let url = manual_download_url(model_name);

    anyhow::bail!(
        "Whisper model not found: {}\n\n\
         You can either:\n\
         1. Download it automatically: lincoln-record warmup --model {}\n\
         2. Download manually: {}\n\
         3. Place it at: {}\n\n\
         To use a different model, pass --model <name-or-path> or set it in ~/.lincolnrc.",
        model_name,
        model_name,
        url,
        path.display()
    )
}

/// Resolve the cache path for a model name without checking existence.
pub fn cache_path_for_model(name: &str, engine: &str, cache_dir: &Path) -> PathBuf {
    cache_dir.join(engine).join(format!("ggml-{}.bin", name))
}

/// Return the manual download URL for a known model name.
pub fn manual_download_url(name: &str) -> String {
    model_url(name).unwrap_or_else(|| format!("{}/ggml-{}.bin", HUGGINGFACE_BASE, name))
}

/// Validate that a model name is known.
pub fn validate_model_name(name: &str) -> Result<()> {
    if model_filename(name).is_some() {
        Ok(())
    } else {
        anyhow::bail!(
            "unknown model '{}'. Known models: tiny, base, small, medium, large-v1, large-v2, large-v3, large-v3-turbo",
            name
        )
    }
}

/// Download a Whisper model into the cache directory.
///
/// Progress is reported via `progress(downloaded_bytes, total_bytes_hint)`.
/// If the model file already exists, it is returned immediately.
pub fn download_model<F>(
    name: &str,
    engine: &str,
    cache_dir: &Path,
    mut progress: F,
) -> Result<PathBuf>
where
    F: FnMut(usize, Option<u64>),
{
    validate_model_name(name)?;
    let dest = cache_path_for_model(name, engine, cache_dir);
    if dest.is_file() {
        return Ok(dest);
    }

    let parent = dest
        .parent()
        .context("model cache path has no parent directory")?;
    std::fs::create_dir_all(parent)
        .with_context(|| format!("failed to create cache directory: {}", parent.display()))?;

    let url = manual_download_url(name);
    let mut response = ureq::get(&url)
        .call()
        .with_context(|| format!("failed to start download from: {}", url))?;

    let total = response.body().content_length();

    let temp = dest.with_extension("bin.tmp");
    let mut file = std::fs::File::create(&temp)
        .with_context(|| format!("failed to create temporary file: {}", temp.display()))?;

    let mut reader = response.body_mut().as_reader();
    let mut buffer = [0u8; 8192];
    let mut downloaded = 0usize;

    loop {
        let n = reader
            .read(&mut buffer)
            .context("failed to read download chunk")?;
        if n == 0 {
            break;
        }
        file.write_all(&buffer[..n])
            .with_context(|| format!("failed to write to: {}", temp.display()))?;
        downloaded += n;
        progress(downloaded, total);
    }

    file.flush().context("failed to flush downloaded model")?;
    drop(file);

    std::fs::rename(&temp, &dest)
        .with_context(|| format!("failed to move downloaded model to: {}", dest.display()))?;

    Ok(dest)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn default_cache_dir_under_home() {
        let dir = default_cache_dir();
        assert!(dir.to_string_lossy().contains(".cache/lincoln/models"));
    }

    #[test]
    fn download_model_returns_existing_file_without_download() {
        let tmp = std::env::temp_dir().join(format!(
            "lincoln-model-test-{}",
            std::process::id()
        ));
        std::fs::create_dir_all(&tmp).unwrap();
        let cache_dir = tmp.join("cache");
        let dest = cache_path_for_model("tiny", "whisper", &cache_dir);
        std::fs::create_dir_all(dest.parent().unwrap()).unwrap();
        std::fs::write(&dest, b"fake model").unwrap();

        let result = download_model("tiny", "whisper", &cache_dir, |_downloaded, _total| {});
        assert_eq!(result.unwrap(), dest);

        std::fs::remove_dir_all(&tmp).ok();
    }
}
