use lincoln_record::cli::Cli;
use clap::Parser;

#[test]
fn test_cli_parses_record_command() {
    let cli = Cli::try_parse_from([
        "lincoln-record",
        "record",
        "--session-id",
        "2026-07-09-recording-replacement",
        "--mic",
        "MacBook Pro Microphone",
        "--system-auto",
        "--engine",
        "whisper",
        "--model",
        "large-v3-turbo",
        "--diarize",
        "--output",
        "/tmp/interviews",
        "--language",
        "zh",
    ])
    .expect("record args should parse");

    match cli {
        Cli::Record(args) => {
            assert_eq!(args.session_id, "2026-07-09-recording-replacement");
            assert_eq!(args.mic, Some("MacBook Pro Microphone".to_string()));
            assert!(args.system_auto);
            assert_eq!(args.engine, "whisper");
            assert_eq!(args.model, Some("large-v3-turbo".to_string()));
            assert!(args.diarize);
            assert_eq!(args.output, Some("/tmp/interviews".to_string()));
            assert_eq!(args.language, Some("zh".to_string()));
        }
        other => panic!("expected Record command, got {:?}", other),
    }
}

#[test]
fn test_cli_parses_transcribe_command() {
    let cli = Cli::try_parse_from([
        "lincoln-record",
        "transcribe",
        "/tmp/sample.wav",
        "--session-id",
        "test-session",
        "--diarize",
    ])
    .expect("transcribe args should parse");

    match cli {
        Cli::Transcribe(args) => {
            assert_eq!(args.path, "/tmp/sample.wav");
            assert_eq!(args.session_id, Some("test-session".to_string()));
            assert!(args.diarize);
            assert!(!args.engine.is_empty());
        }
        other => panic!("expected Transcribe command, got {:?}", other),
    }
}

#[test]
fn test_cli_parses_devices_command() {
    let cli = Cli::try_parse_from(["lincoln-record", "devices"]).expect("devices should parse");
    matches!(cli, Cli::Devices);
}

#[test]
fn test_cli_record_requires_session_id() {
    let result = Cli::try_parse_from(["lincoln-record", "record"]);
    assert!(result.is_err(), "record command should require --session-id");
}
