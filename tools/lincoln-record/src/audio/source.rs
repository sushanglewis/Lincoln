use std::f32::consts::PI;

use anyhow::Result;

/// Metadata describing an audio source.
pub trait AudioSource: Send {
    /// Sample rate in Hz.
    fn sample_rate(&self) -> u32;
    /// Number of interleaved channels.
    fn channels(&self) -> u16;
    /// Total duration in seconds.
    fn duration_seconds(&self) -> f32;
    /// Return an iterator yielding interleaved `f32` PCM samples.
    fn iter(&self) -> Box<dyn Iterator<Item = f32> + Send + '_>;
}

/// A finite sine-wave source for tests and calibration.
pub struct SineWaveSource {
    sample_rate: f32,
    channels: u16,
    frequency: f32,
    duration: f32,
}

impl SineWaveSource {
    pub fn new(sample_rate: f32, channels: u16, frequency: f32, duration: f32) -> Result<Self> {
        anyhow::ensure!(sample_rate > 0.0, "sample_rate must be greater than zero");
        anyhow::ensure!(channels > 0, "channels must be greater than zero");
        anyhow::ensure!(duration >= 0.0, "duration must be non-negative");

        Ok(Self {
            sample_rate,
            channels,
            frequency,
            duration,
        })
    }
}

impl AudioSource for SineWaveSource {
    fn sample_rate(&self) -> u32 {
        self.sample_rate as u32
    }

    fn channels(&self) -> u16 {
        self.channels
    }

    fn duration_seconds(&self) -> f32 {
        self.duration
    }

    fn iter(&self) -> Box<dyn Iterator<Item = f32> + Send + '_> {
        let sample_rate = self.sample_rate;
        let frequency = self.frequency;
        let channels = self.channels as usize;
        let total_samples =
            ((sample_rate * self.duration).ceil().max(0.0) as usize).saturating_mul(channels);
        Box::new((0..total_samples).map(move |index| {
            let sample_index = index / channels;
            let t = sample_index as f32 / sample_rate;
            (2.0 * PI * frequency * t).sin()
        }))
    }
}
