use crate::audio::source::AudioSource;
use anyhow::{Context, Result};
use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use cpal::{SampleFormat, Stream, StreamConfig};
use crossbeam_channel::{Receiver, bounded};

const CHANNEL_CAPACITY: usize = 50;

/// An [AudioSource] that captures live microphone input for a fixed duration.
pub struct MicrophoneSource {
    sample_rate: u32,
    channels: u16,
    receiver: Receiver<Vec<f32>>,
    /// The stream must be kept alive for the iterator to receive samples.
    #[allow(dead_code)]
    stream: Stream,
    target_samples: usize,
}

impl MicrophoneSource {
    /// Open the requested microphone (or the system default) and start capturing.
    pub fn new(device_name: Option<&str>, duration_seconds: f32) -> Result<Self> {
        anyhow::ensure!(duration_seconds > 0.0, "duration must be greater than zero");

        let host = cpal::default_host();
        let device = match device_name {
            Some(name) => host
                .input_devices()?
                .find(|d| d.to_string() == name)
                .with_context(|| format!("microphone not found: {}", name))?,
            None => host
                .default_input_device()
                .context("no default input device")?,
        };

        let config = device.default_input_config()?;
        let sample_rate = config.sample_rate();
        let channels = config.channels();
        let sample_format = config.sample_format();

        let stream_config = StreamConfig {
            channels,
            sample_rate: config.sample_rate(),
            buffer_size: cpal::BufferSize::Default,
        };

        let (sender, receiver) = bounded::<Vec<f32>>(CHANNEL_CAPACITY);

        let stream = match sample_format {
            SampleFormat::F32 => device.build_input_stream(
                stream_config,
                move |data: &[f32], _: &cpal::InputCallbackInfo| {
                    if let Err(error) = sender.try_send(data.to_vec()) {
                        log::warn!("dropping audio chunk: {}", error);
                    }
                },
                |error| log::error!("microphone stream error: {}", error),
                None,
            ),
            other => anyhow::bail!("unsupported sample format: {:?}", other),
        }
        .context("failed to build microphone stream")?;

        stream.play().context("failed to start microphone stream")?;

        let frames = (sample_rate as f32 * duration_seconds).ceil() as usize;
        let target_samples = frames.saturating_mul(channels as usize);

        Ok(Self {
            sample_rate,
            channels,
            receiver,
            stream,
            target_samples,
        })
    }
}

impl AudioSource for MicrophoneSource {
    fn sample_rate(&self) -> u32 {
        self.sample_rate
    }

    fn channels(&self) -> u16 {
        self.channels
    }

    fn duration_seconds(&self) -> f32 {
        (self.target_samples / (self.channels as usize).max(1)) as f32 / (self.sample_rate as f32)
    }

    fn iter(&self) -> Box<dyn Iterator<Item = f32> + Send + '_> {
        Box::new(self.receiver.iter().flatten().take(self.target_samples))
    }
}
