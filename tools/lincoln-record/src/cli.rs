use clap::Parser;

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
    Warmup,
}

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
    pub output: Option<String>,

    #[arg(long, help = "Language code (e.g. en, zh)")]
    pub language: Option<String>,
}

#[derive(Debug, Clone, Parser)]
pub struct StopArgs {
    #[arg(long, help = "Session identifier to stop")]
    pub session_id: String,
}

#[derive(Debug, Clone, Parser)]
pub struct TranscribeArgs {
    pub path: String,

    #[arg(long, help = "Session identifier")]
    pub session_id: Option<String>,

    #[arg(long, default_value = "whisper", help = "Transcription engine")]
    pub engine: String,

    #[arg(long, help = "Model name or path")]
    pub model: Option<String>,

    #[arg(long, help = "Enable speaker diarization")]
    pub diarize: bool,

    #[arg(long, help = "Output directory")]
    pub output: Option<String>,

    #[arg(long, help = "Language code (e.g. en, zh)")]
    pub language: Option<String>,
}
