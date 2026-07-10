use hound::WavReader;
use lincoln_record::audio::saver::write_source_to_wav;
use lincoln_record::audio::source::{AudioSource, SineWaveSource};
use tempfile::TempDir;

#[test]
fn test_synthetic_source_writes_wav_file() {
    let tmp = TempDir::new().expect("temp dir");
    let output = tmp.path().join("sine.wav");

    let source = SineWaveSource::new(48000.0, 1, 1000.0, 1.0).expect("valid source");
    write_source_to_wav(&source, &output, 48000, 1).expect("write wav");

    assert!(output.exists(), "output wav file should exist");
    let reader = WavReader::open(&output).expect("open wav");
    let spec = reader.spec();
    assert_eq!(spec.sample_rate, 48000);
    assert_eq!(spec.channels, 1);
    let samples: Vec<i32> = reader
        .into_samples::<i32>()
        .filter_map(Result::ok)
        .collect();
    assert_eq!(
        samples.len(),
        48000,
        "one second of 48 kHz mono should have 48000 samples"
    );
}

#[test]
fn test_resample_changes_sample_rate() {
    let input: Vec<f32> = SineWaveSource::new(16000.0, 1, 440.0, 1.0)
        .expect("valid source")
        .iter()
        .take(16000)
        .collect();
    let resampled = lincoln_record::audio::resampler::resample_interleaved(&input, 16000, 48000, 1)
        .expect("resample");
    assert_eq!(
        resampled.len(),
        48000,
        "16000 mono samples resampled to 48000 should produce 48000"
    );
}
