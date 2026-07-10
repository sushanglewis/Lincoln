use anyhow::{Result, ensure};

/// Naive linear-interpolation resampling for interleaved `f32` PCM.
///
/// This is intentionally simple for Phase 2; it will be replaced with a
/// higher-quality resampler once the pipeline stabilizes.
pub fn resample_interleaved(
    input: &[f32],
    input_rate: u32,
    output_rate: u32,
    channels: u16,
) -> Result<Vec<f32>> {
    ensure!(input_rate > 0, "input_rate must be greater than zero");
    ensure!(output_rate > 0, "output_rate must be greater than zero");
    let channels = channels.max(1) as usize;
    ensure!(
        input.len() % channels == 0,
        "input length must be a multiple of channels"
    );

    let input_frames = input.len() / channels;
    let output_frames =
        (input_frames as f64 * output_rate as f64 / input_rate as f64).ceil() as usize;
    let ratio = input_rate as f64 / output_rate as f64;

    let mut output = Vec::with_capacity(output_frames * channels);

    for out_frame in 0..output_frames {
        let in_pos = out_frame as f64 * ratio;
        let index = in_pos as usize;
        let frac = in_pos - index as f64;
        let next_index = (index + 1).min(input_frames.saturating_sub(1));

        for channel in 0..channels {
            let current = input[index * channels + channel];
            let next = input[next_index * channels + channel];
            let sample = current + (next - current) * frac as f32;
            output.push(sample);
        }
    }

    Ok(output)
}
