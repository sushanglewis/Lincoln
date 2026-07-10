use std::f32::consts::PI;

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
    pub fn new(sample_rate: f32, channels: u16, frequency: f32, duration: f32) -> Self {
        Self {
            sample_rate,
            channels,
            frequency,
            duration,
        }
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
        let channels = self.channels.max(1) as usize;
        let total_samples = (sample_rate * self.duration) as usize * channels;
        Box::new((0..total_samples).map(move |index| {
            let sample_index = index / channels;
            let t = sample_index as f32 / sample_rate;
            (2.0 * PI * frequency * t).sin()
        }))
    }
}
