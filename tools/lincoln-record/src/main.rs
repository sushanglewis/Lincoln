use anyhow::Context;
use clap::Parser;
use lincoln_record::audio::capture::microphone::MicrophoneSource;
use lincoln_record::audio::devices::{
    default_input_device, list_input_devices, log_device_enumeration_error,
};
use lincoln_record::audio::saver::write_source_to_wav;
use lincoln_record::audio::source::AudioSource;
use lincoln_record::cli::{Cli, RecordArgs, TranscribeArgs, WarmupArgs};
use lincoln_record::config::Config;
use lincoln_record::model::{default_cache_dir, download_model, resolve_model_path};
use lincoln_record::output::metadata::{DeviceInfo, FileInfo, SessionMetadata};
use lincoln_record::output::transcript::format_transcript;
use lincoln_record::transcription::diarization::diarize_and_merge;
use lincoln_record::transcription::provider::{
    MockProvider, TranscriptSegment, TranscriptionProvider,
};
use lincoln_record::transcription::whisper::WhisperProvider;
use std::path::PathBuf;

#[tokio::main]
async fn main() {
    env_logger::init();

    let config = match Config::load() {
        Ok(config) => config,
        Err(error) => {
            log::error!("failed to load config: {:#}", error);
            std::process::exit(1);
        }
    };

    let result = match Cli::parse() {
        Cli::Devices => {
            run_devices();
            Ok(())
        }
        Cli::Record(args) => run_record(args).await,
        Cli::Transcribe(args) => run_transcribe(args, &config).await,
        Cli::Warmup(args) => run_warmup(args, &config),
        other => {
            eprintln!("{:?} is not yet implemented", other);
            std::process::exit(1);
        }
    };

    if let Err(error) = result {
        log::error!("{:#}", error);
        std::process::exit(1);
    }
}

fn run_devices() {
    match default_input_device() {
        Some(name) => println!("Default input: {}", name),
        None => eprintln!("No default input device found"),
    }
    match list_input_devices() {
        Ok(devices) => {
            for name in devices {
                println!("  {}", name);
            }
        }
        Err(error) => log_device_enumeration_error(&error),
    }
}

async fn run_record(args: RecordArgs) -> anyhow::Result<()> {
    validate_session_id(&args.session_id)?;

    let output_dir = args.output.unwrap_or_else(|| PathBuf::from("."));
    let session_dir = output_dir.join(&args.session_id);
    tokio::fs::create_dir_all(&session_dir).await?;

    let output_path = session_dir.join("audio.wav");
    let duration = args.duration.unwrap_or(30.0);
    let mic = args.mic;

    let output_path_clone = output_path.clone();
    let source = MicrophoneSource::new(mic.as_deref(), duration)?;
    let stop_handle = source.stop_handle();
    let mut handle = tokio::task::spawn_blocking(move || {
        write_source_to_wav(
            &source,
            &output_path_clone,
            source.sample_rate(),
            source.channels(),
        )
    });

    tokio::select! {
        _ = tokio::signal::ctrl_c() => {
            log::info!("received stop signal, shutting down recording");
            stop_handle.stop();
            (&mut handle).await??;
        }
        result = &mut handle => {
            result??;
        }
    }

    println!("Wrote {}", output_path.display());
    Ok(())
}

async fn run_transcribe(args: TranscribeArgs, config: &Config) -> anyhow::Result<()> {
    let session_id = args.session_id.unwrap_or_else(|| {
        args.path
            .file_stem()
            .unwrap_or_default()
            .to_string_lossy()
            .to_string()
    });
    validate_session_id(&session_id)?;

    let output_dir = args.output.unwrap_or_else(|| PathBuf::from("."));
    let session_dir = output_dir.join(&session_id);
    tokio::fs::create_dir_all(&session_dir).await?;

    let provider: Box<dyn TranscriptionProvider + Send + Sync> = match args.engine.as_str() {
        "mock" => Box::new(MockProvider::new(vec![TranscriptSegment {
            start: 0.0,
            end: 1.0,
            speaker: None,
            text: "Mock transcription output".to_string(),
        }])),
        "whisper" => {
            let model_arg = args.model.as_ref().map(|s| std::path::Path::new(s.as_str()));
            let model_path = resolve_model_path(model_arg, config)?;
            Box::new(WhisperProvider::new(
                model_path,
                language_choice(args.language.as_deref(), config.transcription.language.as_str()),
            ))
        }
        other => anyhow::bail!(
            "transcription engine '{}' is not yet implemented; use 'mock' or 'whisper'",
            other
        ),
    };

    let audio_path = args.path.clone();
    let language = args.language.clone();
    let diarize = args.diarize;
    let diarize_work_dir = session_dir.clone();
    let segments = tokio::task::spawn_blocking(move || {
        let mut segs = provider.transcribe(&audio_path, language.as_deref())?;
        if diarize {
            segs = diarize_and_merge(&audio_path, &segs, &diarize_work_dir)?;
        }
        Ok::<_, anyhow::Error>(segs)
    })
    .await??;

    let transcript = format_transcript(&session_id, &segments);
    tokio::fs::write(session_dir.join("transcript.md"), transcript).await?;

    let metadata = SessionMetadata {
        session_id: session_id.clone(),
        process_slug: "issue-25".to_string(),
        started_at: chrono::Utc::now().to_rfc3339(),
        ended_at: Some(chrono::Utc::now().to_rfc3339()),
        engine: args.engine,
        model: args.model.unwrap_or_else(|| config.transcription.model.clone()),
        diarization: args.diarize,
        devices: DeviceInfo {
            microphone: "unknown".to_string(),
            system: None,
        },
        files: FileInfo {
            transcript: "transcript.md".to_string(),
            audio: args
                .path
                .file_name()
                .unwrap_or_default()
                .to_string_lossy()
                .to_string(),
            metadata: "metadata.json".to_string(),
        },
    };
    tokio::fs::write(
        session_dir.join("metadata.json"),
        serde_json::to_string_pretty(&metadata)?,
    )
    .await?;

    println!("Wrote transcript and metadata to {}", session_dir.display());
    Ok(())
}

fn run_warmup(args: WarmupArgs, config: &Config) -> anyhow::Result<()> {
    let model_name = args
        .model
        .as_deref()
        .unwrap_or(config.transcription.model.as_str());
    let engine = args
        .engine
        .as_deref()
        .unwrap_or(config.transcription.engine.as_str());
    let cache_dir = args
        .cache_dir
        .clone()
        .or_else(|| config.model_cache_dir.clone())
        .unwrap_or_else(default_cache_dir);

    eprintln!("Warming up {} model '{}' into {}...", engine, model_name, cache_dir.display());

    let path = download_model(model_name, engine, &cache_dir, |downloaded, total| {
        match total {
            Some(t) => {
                let pct = (downloaded as f64 / t as f64) * 100.0;
                eprint!("\r  downloaded {} / {} bytes ({:.1}%)", downloaded, t, pct);
            }
            None => {
                eprint!("\r  downloaded {} bytes", downloaded);
            }
        }
    })
    .context("model warmup failed")?;

    eprintln!();
    println!("Model ready at {}", path.display());
    Ok(())
}

fn language_choice(cli: Option<&str>, config: &str) -> Option<String> {
    cli.filter(|l| *l != "auto")
        .or_else(|| if config == "auto" { None } else { Some(config) })
        .map(|s| s.to_string())
}

fn validate_session_id(session_id: &str) -> anyhow::Result<()> {
    if session_id.is_empty() {
        anyhow::bail!("session-id must not be empty");
    }
    if session_id.len() > 128 {
        anyhow::bail!("session-id must be 128 characters or fewer");
    }
    if session_id.contains('/') || session_id.contains('\\') || session_id.contains("..") {
        anyhow::bail!("session-id must not contain path separators or parent references");
    }
    Ok(())
}
