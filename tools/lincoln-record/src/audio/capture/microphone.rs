use crate::audio::source::AudioSource;
use anyhow::{Context, Result};
use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use cpal::{SampleFormat, Stream, StreamConfig};
use crossbeam_channel::{Receiver, Select, Sender, bounded};
use std::sync::Arc;
use std::sync::atomic::{AtomicBool, Ordering};

const AUDIO_CHANNEL_CAPACITY: usize = 50;

/// An [AudioSource] that captures live microphone input until stopped or the
/// maximum duration is reached.
pub struct MicrophoneSource {
    sample_rate: u32,
    channels: u16,
    audio_sender: Sender<Option<Vec<f32>>>,
    audio_receiver: Receiver<Option<Vec<f32>>>,
    /// Kept alive so the OS continues to deliver samples while we iterate.
    #[allow(dead_code)]
    stream: Stream,
    target_samples: usize,
    stop_flag: Arc<AtomicBool>,
    stop_sender: Sender<()>,
    stop_receiver: Receiver<()>,
}

/// Handle that can request an early stop of a [MicrophoneSource].
#[derive(Clone)]
pub struct StopHandle {
    sender: Sender<()>,
}

impl StopHandle {
    /// Request a stop. The associated iterator will terminate after draining
    /// any buffered audio chunks.
    pub fn stop(&self) {
        let _ = self.sender.try_send(());
    }
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

        let (audio_sender, audio_receiver) = bounded::<Option<Vec<f32>>>(AUDIO_CHANNEL_CAPACITY);
        let callback_sender = audio_sender.clone();
        let stop_flag = Arc::new(AtomicBool::new(false));
        let callback_stop_flag = Arc::clone(&stop_flag);

        let stream = match sample_format {
            SampleFormat::F32 => device.build_input_stream(
                stream_config,
                move |data: &[f32], _: &cpal::InputCallbackInfo| {
                    if callback_stop_flag.load(Ordering::Relaxed) {
                        let _ = callback_sender.try_send(None);
                        return;
                    }
                    if let Err(error) = callback_sender.try_send(Some(data.to_vec())) {
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
        let (stop_sender, stop_receiver) = bounded::<()>(1);

        Ok(Self {
            sample_rate,
            channels,
            audio_sender,
            audio_receiver,
            stream,
            target_samples,
            stop_flag,
            stop_sender,
            stop_receiver,
        })
    }

    /// Return a handle that can be used to request an early stop.
    pub fn stop_handle(&self) -> StopHandle {
        StopHandle {
            sender: self.stop_sender.clone(),
        }
    }

    /// Signal the capture to stop. The iterator will terminate after draining
    /// any buffered chunks.
    pub fn stop(&self) {
        self.stop_flag.store(true, Ordering::Relaxed);
        let _ = self.audio_sender.try_send(None);
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
        Box::new(MicrophoneIter {
            audio_receiver: &self.audio_receiver,
            stop_receiver: &self.stop_receiver,
            chunk: Vec::new(),
            position: 0,
            remaining: self.target_samples,
        })
    }
}

struct MicrophoneIter<'a> {
    audio_receiver: &'a Receiver<Option<Vec<f32>>>,
    stop_receiver: &'a Receiver<()>,
    chunk: Vec<f32>,
    position: usize,
    remaining: usize,
}

impl Iterator for MicrophoneIter<'_> {
    type Item = f32;

    fn next(&mut self) -> Option<f32> {
        loop {
            if self.remaining == 0 {
                return None;
            }
            if self.position < self.chunk.len() {
                let sample = self.chunk[self.position];
                self.position += 1;
                self.remaining -= 1;
                return Some(sample);
            }

            let mut select = Select::new();
            let audio_handle = select.recv(self.audio_receiver);
            let stop_handle = select.recv(self.stop_receiver);
            let oper = select.select();

            match oper.index() {
                index if index == audio_handle => match oper.recv(self.audio_receiver) {
                    Ok(Some(chunk)) => {
                        self.chunk = chunk;
                        self.position = 0;
                    }
                    Ok(None) | Err(_) => return None,
                },
                index if index == stop_handle => {
                    let _ = oper.recv(self.stop_receiver);
                    return None;
                }
                _ => return None,
            }
        }
    }
}
