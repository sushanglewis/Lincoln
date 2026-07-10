pub use crate::transcription::provider::TranscriptSegment;

/// Format segments as a Lincoln-standard `transcript.md` document.
pub fn format_transcript(session_id: &str, segments: &[TranscriptSegment]) -> String {
    let mut speakers: Vec<String> = segments
        .iter()
        .filter_map(|segment| segment.speaker.clone())
        .fold(Vec::new(), |mut acc, speaker| {
            if !acc.contains(&speaker) {
                acc.push(speaker);
            }
            acc
        });
    speakers.sort();

    let mut output = String::new();
    output.push_str(&format!("# Interview: {}\n\n", session_id));
    output.push_str("## Speakers\n\n");
    for speaker in &speakers {
        output.push_str(&format!("- {}\n", speaker));
    }
    output.push_str("\n## Transcript\n\n");

    for segment in segments {
        let speaker = segment.speaker.as_deref().unwrap_or("Unknown");
        let timestamp = format_timestamp(segment.start);
        output.push_str(&format!(
            "**[{}] {}**: {}\n\n",
            timestamp, speaker, segment.text
        ));
    }

    output
}

fn format_timestamp(seconds: f64) -> String {
    let total_seconds = seconds as u64;
    let hours = total_seconds / 3600;
    let minutes = (total_seconds % 3600) / 60;
    let secs = total_seconds % 60;
    format!("{:02}:{:02}:{:02}", hours, minutes, secs)
}
