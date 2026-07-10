use clap::Parser;
use lincoln_record::audio::capture::microphone::MicrophoneSource;
use lincoln_record::audio::devices::{
    default_input_device, list_input_devices, log_device_enumeration_error,
};
use lincoln_record::audio::saver::write_source_to_wav;
use lincoln_record::audio::source::AudioSource;
use lincoln_record::cli::{Cli, RecordArgs};
use std::path::PathBuf;

#[tokio::main]
async fn main() {
    env_logger::init();

    let result = match Cli::parse() {
        Cli::Devices => {
            run_devices();
            Ok(())
        }
        Cli::Record(args) => run_record(args).await,
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
    let output_dir = args.output.unwrap_or_else(|| PathBuf::from("."));
    let session_dir = output_dir.join(&args.session_id);
    tokio::fs::create_dir_all(&session_dir).await?;

    let output_path = session_dir.join("audio.wav");
    let duration = args.duration.unwrap_or(30.0);
    let mic = args.mic;

    let output_path_clone = output_path.clone();
    tokio::task::spawn_blocking(move || {
        let source = MicrophoneSource::new(mic.as_deref(), duration)?;
        write_source_to_wav(
            &source,
            &output_path_clone,
            source.sample_rate(),
            source.channels(),
        )
    })
    .await??;

    println!("Wrote {}", output_path.display());
    Ok(())
}
