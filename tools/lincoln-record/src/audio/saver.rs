use crate::audio::resampler::resample_interleaved;
use crate::audio::source::AudioSource;
use anyhow::{Context, Result};
use hound::{WavSpec, WavWriter};
use std::path::Path;

const MAX_AMPLITUDE: f32 = i16::MAX as f32;

/// Write all samples from `source` to a 16-bit PCM WAV file at `output`.
///
/// If `target_sample_rate` or `target_channels` differ from the source, the
/// samples are resampled and duplicated/mixed down using simple rules.
pub fn write_source_to_wav(
    source: &dyn AudioSource,
    output: &Path,
    target_sample_rate: u32,
    target_channels: u16,
) -> Result<()> {
    let spec = WavSpec {
        channels: target_channels,
        sample_rate: target_sample_rate,
        bits_per_sample: 16,
        sample_format: hound::SampleFormat::Int,
    };

    let mut writer = WavWriter::create(output, spec)
        .with_context(|| format!("failed to create wav writer: {}", output.display()))?;

    let frames = (source.sample_rate() as f32 * source.duration_seconds()) as usize;
    let expected_samples = frames * source.channels() as usize;
    let samples: Vec<f32> = source.iter().take(expected_samples).collect();

    let final_samples = if source.sample_rate() != target_sample_rate {
        resample_interleaved(
            &samples,
            source.sample_rate(),
            target_sample_rate,
            source.channels(),
        )?
    } else {
        samples
    };

    let final_channels = target_channels.max(1) as usize;
    let source_channels = source.channels().max(1) as usize;

    for frame in final_samples.chunks(source_channels) {
        match (source_channels, final_channels) {
            (1, 2) => {
                let value = frame.first().copied().unwrap_or(0.0);
                writer.write_sample(to_i16(value))?;
                writer.write_sample(to_i16(value))?;
            }
            (2, 1) => {
                let left = frame.first().copied().unwrap_or(0.0);
                let right = frame.get(1).copied().unwrap_or(0.0);
                writer.write_sample(to_i16((left + right) * 0.5))?;
            }
            _ => {
                for value in frame {
                    writer.write_sample(to_i16(*value))?;
                }
            }
        }
    }

    writer.finalize()?;
    Ok(())
}

fn to_i16(sample: f32) -> i16 {
    (sample.clamp(-1.0, 1.0) * MAX_AMPLITUDE) as i16
}
