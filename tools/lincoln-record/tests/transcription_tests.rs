use lincoln_record::output::metadata::{DeviceInfo, FileInfo, SessionMetadata};
use lincoln_record::output::transcript::{TranscriptSegment, format_transcript};
use lincoln_record::transcription::provider::{MockProvider, TranscriptionProvider};
use std::path::PathBuf;

#[test]
fn test_mock_provider_returns_segments() {
    let provider = MockProvider::new(vec![TranscriptSegment {
        start: 0.0,
        end: 2.0,
        speaker: Some("Speaker 1".to_string()),
        text: "Hello world".to_string(),
    }]);

    let segments = provider
        .transcribe(&PathBuf::from("/tmp/sample.wav"), Some("en"))
        .expect("mock provider should always succeed");

    assert_eq!(segments.len(), 1);
    assert_eq!(segments[0].text, "Hello world");
}

#[test]
fn test_transcript_formatting_includes_session_and_speakers() {
    let segments = vec![
        TranscriptSegment {
            start: 0.0,
            end: 2.0,
            speaker: Some("Speaker 1".to_string()),
            text: "Hello".to_string(),
        },
        TranscriptSegment {
            start: 2.5,
            end: 4.0,
            speaker: Some("Speaker 2".to_string()),
            text: "Hi there".to_string(),
        },
    ];

    let markdown = format_transcript("2026-07-11-test", &segments);
    assert!(markdown.contains("# Interview: 2026-07-11-test"));
    assert!(markdown.contains("- Speaker 1"));
    assert!(markdown.contains("- Speaker 2"));
    assert!(markdown.contains("**[00:00:00] Speaker 1**: Hello"));
    assert!(markdown.contains("**[00:00:02] Speaker 2**: Hi there"));
}

#[test]
fn test_metadata_serializes_required_fields() {
    let metadata = SessionMetadata {
        session_id: "2026-07-11-test".to_string(),
        process_slug: "issue-25".to_string(),
        started_at: "2026-07-11T10:00:00Z".to_string(),
        ended_at: Some("2026-07-11T10:30:00Z".to_string()),
        engine: "whisper".to_string(),
        model: "large-v3-turbo".to_string(),
        diarization: false,
        devices: DeviceInfo {
            microphone: "MacBook Pro Microphone".to_string(),
            system: None,
        },
        files: FileInfo {
            transcript: "transcript.md".to_string(),
            audio: "audio.wav".to_string(),
            metadata: "metadata.json".to_string(),
        },
    };

    let json = serde_json::to_string_pretty(&metadata).expect("serialize");
    assert!(json.contains("2026-07-11-test"));
    assert!(json.contains("issue-25"));
    assert!(json.contains("large-v3-turbo"));
}
