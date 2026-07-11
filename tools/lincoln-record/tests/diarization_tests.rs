use lincoln_record::audio::saver::write_source_to_wav;
use lincoln_record::audio::source::{AudioSource, SineWaveSource};
use std::path::PathBuf;
use std::process::Command;
use tempfile::TempDir;

fn generate_two_speaker_fixture(path: &std::path::Path) {
    let speaker_a = SineWaveSource::new(48000.0, 1, 440.0, 1.0).expect("valid source");
    let speaker_b = SineWaveSource::new(48000.0, 1, 880.0, 1.0).expect("valid source");

    // Concatenate one second of speaker A followed by one second of speaker B.
    let samples: Vec<f32> = speaker_a
        .iter()
        .take(48000)
        .chain(speaker_b.iter().take(48000))
        .collect();

    let combined = lincoln_record::audio::source::InMemorySource::new(samples, 48000, 1, 2.0);
    write_source_to_wav(&combined, path, 48000, 1).expect("write fixture");
}

#[test]
fn test_diarize_labels_two_speakers() {
    let tmp = TempDir::new().expect("temp dir");
    let fixture = tmp.path().join("two_speakers.wav");
    generate_two_speaker_fixture(&fixture);

    let project_root = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let script = project_root.join("diarize/diarize.py");

    let output = Command::new("python3")
        .arg(&script)
        .arg(&fixture)
        .arg("--output")
        .arg(tmp.path().join("diarization.json"))
        .output()
        .expect("run diarize.py");

    assert!(
        output.status.success(),
        "diarize.py failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );

    let raw = std::fs::read_to_string(tmp.path().join("diarization.json")).expect("read output");
    let diarization: serde_json::Value = serde_json::from_str(&raw).expect("parse json");
    let speakers = diarization
        .as_array()
        .expect("diarization is array")
        .iter()
        .map(|entry| entry["speaker"].as_str().unwrap_or(""))
        .collect::<std::collections::HashSet<_>>();
    assert_eq!(
        speakers.len(),
        2,
        "fixture should contain two distinct speakers"
    );
}

#[test]
fn test_merge_combines_diarization_with_transcript() {
    let tmp = TempDir::new().expect("temp dir");
    let project_root = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let script = project_root.join("diarize/merge.py");

    let transcript = serde_json::json!([
        {"start": 0.0, "end": 1.0, "text": "hello"},
        {"start": 1.0, "end": 2.0, "text": "world"}
    ]);
    let diarization = serde_json::json!([
        {"start": 0.0, "end": 1.0, "speaker": "A"},
        {"start": 1.0, "end": 2.0, "speaker": "B"}
    ]);

    std::fs::write(tmp.path().join("transcript.json"), transcript.to_string())
        .expect("write transcript");
    std::fs::write(tmp.path().join("diarization.json"), diarization.to_string())
        .expect("write diarization");

    let output = Command::new("python3")
        .arg(&script)
        .arg(tmp.path().join("transcript.json"))
        .arg(tmp.path().join("diarization.json"))
        .arg("--output")
        .arg(tmp.path().join("merged.json"))
        .output()
        .expect("run merge.py");

    assert!(
        output.status.success(),
        "merge.py failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );

    let raw = std::fs::read_to_string(tmp.path().join("merged.json")).expect("read output");
    let merged: serde_json::Value = serde_json::from_str(&raw).expect("parse json");
    let first = &merged.as_array().unwrap()[0];
    assert_eq!(first["speaker"], "A");
    let second = &merged.as_array().unwrap()[1];
    assert_eq!(second["speaker"], "B");
}
