use crate::audio::resampler::resample_interleaved;
use crate::transcription::provider::{TranscriptSegment, TranscriptionProvider};
use anyhow::{Context, Result};
use hound::WavReader;
use std::path::Path;
use whisper_rs::{FullParams, SamplingStrategy, WhisperContext, WhisperContextParameters};

const WHISPER_SAMPLE_RATE: u32 = 16000;
const WHISPER_CHANNELS: u16 = 1;

/// A local Whisper transcription provider using whisper.cpp via `whisper-rs`.
pub struct WhisperProvider {
    model_path: std::path::PathBuf,
    language: Option<String>,
}

impl WhisperProvider {
    pub fn new(model_path: impl Into<std::path::PathBuf>, language: Option<String>) -> Self {
        Self {
            model_path: model_path.into(),
            language,
        }
    }
}

impl TranscriptionProvider for WhisperProvider {
    fn transcribe(&self,
        audio_path: &Path,
        language: Option<&str>,
    ) -> Result<Vec<TranscriptSegment>> {
        anyhow::ensure!(
            self.model_path.is_file(),
            "Whisper model not found: {}",
            self.model_path.display()
        );

        let samples = load_whisper_audio(audio_path)
            .with_context(|| format!("failed to load audio: {}", audio_path.display()))?;

        let ctx = WhisperContext::new_with_params(
            self.model_path.to_string_lossy().as_ref(),
            WhisperContextParameters::default(),
        )
        .with_context(|| format!("failed to load Whisper model: {}", self.model_path.display()))?;

        let mut params = FullParams::new(SamplingStrategy::Greedy { best_of: 1 });

        let lang = language
            .filter(|l| *l != "auto")
            .or_else(|| self.language.as_deref().filter(|l| *l != "auto"));
        params.set_language(lang);
        params.set_print_special(false);
        params.set_print_progress(false);
        params.set_print_realtime(false);
        params.set_print_timestamps(false);

        let mut state = ctx.create_state().context("failed to create Whisper state")?;
        state
            .full(params, &samples)
            .context("Whisper transcription failed")?;

        let num_segments = state.full_n_segments().context("failed to get segment count")?;
        let mut segments = Vec::with_capacity(num_segments as usize);
        for index in 0..num_segments {
            let text = state
                .full_get_segment_text(index)
                .context("failed to get segment text")?;
            let start = state
                .full_get_segment_t0(index)
                .context("failed to get segment start")? as f64 / 1000.0;
            let end = state
                .full_get_segment_t1(index)
                .context("failed to get segment end")? as f64 / 1000.0;
            segments.push(TranscriptSegment {
                start,
                end,
                speaker: None,
                text: text.trim().to_string(),
            });
        }

        Ok(segments)
    }
}

/// Load a WAV file and convert it to 16 kHz mono f32 samples for Whisper.
fn load_whisper_audio(path: &Path) -> Result<Vec<f32>> {
    let mut reader = WavReader::open(path)
        .with_context(|| format!("failed to open wav: {}", path.display()))?;
    let spec = reader.spec();

    anyhow::ensure!(
        spec.sample_rate > 0,
        "invalid sample rate: {}",
        spec.sample_rate
    );

    let samples: Vec<f32> = match spec.sample_format {
        hound::SampleFormat::Int => reader
            .samples::<i16>()
            .map(|sample| sample.map(|s| s as f32 / i16::MAX as f32))
            .collect::<Result<_, _>>()
            .context("failed to read i16 samples")?,
        hound::SampleFormat::Float => reader
            .samples::<f32>()
            .collect::<Result<_, _>>()
            .context("failed to read f32 samples")?,
    };

    let channels = spec.channels;
    let mono = if channels == 1 {
        samples
    } else {
        downmix_to_mono(&samples, channels)
            .context("failed to downmix audio to mono")?
    };

    if spec.sample_rate == WHISPER_SAMPLE_RATE {
        return Ok(mono);
    }

    resample_interleaved(
        &mono,
        spec.sample_rate,
        WHISPER_SAMPLE_RATE,
        WHISPER_CHANNELS,
    )
    .context("failed to resample audio to 16 kHz")
}

fn downmix_to_mono(samples: &[f32], channels: u16) -> Result<Vec<f32>> {
    let channels = channels as usize;
    anyhow::ensure!(channels > 0, "channels must be greater than zero");
    anyhow::ensure!(
        samples.len().is_multiple_of(channels),
        "sample length is not a multiple of channels"
    );

    let divisor = channels as f32;
    Ok(samples
        .chunks_exact(channels)
        .map(|frame| frame.iter().sum::<f32>() / divisor)
        .collect())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    #[test]
    fn test_downmix_stereo_to_mono() {
        let stereo = vec![1.0f32, 1.0f32, -1.0f32, -1.0f32, 0.5f32, 0.5f32];
        let mono = downmix_to_mono(&stereo, 2).unwrap();
        assert_eq!(mono, vec![1.0f32, -1.0f32, 0.5f32]);
    }

    #[test]
    fn test_whisper_provider_missing_model_errors() {
        let provider = WhisperProvider::new("/nonexistent/model.bin", None);
        let result = provider.transcribe(Path::new("/nonexistent/audio.wav"), None);
        assert!(result.is_err());
        let msg = format!("{}", result.unwrap_err());
        assert!(msg.contains("Whisper model not found"));
    }

    #[test]
    #[ignore = "requires a local Whisper ggml model"]
    fn test_whisper_provider_transcribes_fixture() {
        let model_path = PathBuf::from(std::env::var("WHISPER_MODEL").unwrap());
        let audio_path = PathBuf::from(std::env::var("WHISPER_AUDIO").unwrap());
        let provider = WhisperProvider::new(&model_path, None);
        let segments = provider.transcribe(&audio_path, None).unwrap();
        assert!(!segments.is_empty());
    }
}
