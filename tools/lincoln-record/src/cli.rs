use clap::Parser;
use std::path::PathBuf;

/// Top-level CLI for `lincoln-record`.
#[derive(Debug, Clone, Parser)]
#[command(name = "lincoln-record")]
#[command(about = "Headless local recorder and transcriber for Lincoln interviews")]
#[command(version)]
pub enum Cli {
    /// Record microphone and optional system audio.
    Record(RecordArgs),
    /// Stop a running recording session.
    Stop(StopArgs),
    /// Transcribe an existing audio file.
    Transcribe(TranscribeArgs),
    /// List available audio input devices.
    Devices,
    /// Download models and warm up caches.
    Warmup(WarmupArgs),
}

/// Arguments for the `warmup` subcommand.
#[derive(Debug, Clone, Parser)]
pub struct WarmupArgs {
    #[arg(long, help = "Model name to download")]
    pub model: Option<String>,

    #[arg(long, help = "Engine name")]
    pub engine: Option<String>,

    #[arg(long, help = "Output directory for the model cache")]
    pub cache_dir: Option<PathBuf>,
}

/// Arguments for the `record` subcommand.
#[derive(Debug, Clone, Parser)]
pub struct RecordArgs {
    #[arg(long, help = "Unique session identifier for this interview")]
    pub session_id: String,

    #[arg(long, help = "Microphone device name to use")]
    pub mic: Option<String>,

    #[arg(long, help = "Automatically capture system audio on macOS")]
    pub system_auto: bool,

    #[arg(long, default_value = "whisper", help = "Transcription engine")]
    pub engine: String,

    #[arg(long, help = "Model name or path")]
    pub model: Option<String>,

    #[arg(long, help = "Enable speaker diarization")]
    pub diarize: bool,

    #[arg(long, help = "Output directory")]
    pub output: Option<PathBuf>,

    #[arg(long, help = "Language code (e.g. en, zh)")]
    pub language: Option<String>,

    /// Recording duration in seconds. Hidden while full SIGINT stop control is in progress.
    #[arg(long, hide = true)]
    pub duration: Option<f32>,
}

/// Arguments for the `stop` subcommand.
#[derive(Debug, Clone, Parser)]
pub struct StopArgs {
    #[arg(long, help = "Session identifier to stop")]
    pub session_id: String,
}

/// Arguments for the `transcribe` subcommand.
#[derive(Debug, Clone, Parser)]
pub struct TranscribeArgs {
    pub path: PathBuf,

    #[arg(long, help = "Session identifier")]
    pub session_id: Option<String>,

    #[arg(long, default_value = "whisper", help = "Transcription engine")]
    pub engine: String,

    #[arg(long, help = "Model name or path")]
    pub model: Option<String>,

    #[arg(long, help = "Enable speaker diarization")]
    pub diarize: bool,

    #[arg(long, help = "Output directory")]
    pub output: Option<PathBuf>,

    #[arg(long, help = "Language code (e.g. en, zh)")]
    pub language: Option<String>,
}
