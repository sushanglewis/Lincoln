#!/usr/bin/env python3
"""Lightweight local speaker diarization for testing and fallback.

This implementation uses zero-crossing rate heuristics and is intentionally
simple. In production it should be replaced with whisperx + pyannote.audio
once models and HuggingFace tokens are available.
"""

import argparse
import json
import math
import struct
import wave


def read_mono_16bit(path: str) -> tuple[int, bytes]:
    with wave.open(path, "rb") as wf:
        channels = wf.getnchannels()
        rate = wf.getframerate()
        frames = wf.getnframes()
        data = wf.readframes(frames)
        if channels != 1:
            raise ValueError("only mono WAV files are supported")
        return rate, data


def samples_from_bytes(data: bytes) -> list[float]:
    count = len(data) // 2
    ints = struct.unpack(f"<{count}h", data)
    return [s / 32768.0 for s in ints]


def zero_crossing_rate(samples: list[float]) -> float:
    if len(samples) < 2:
        return 0.0
    crossings = sum(1 for i in range(1, len(samples)) if samples[i - 1] * samples[i] < 0)
    return crossings / len(samples)


def rms(samples: list[float]) -> float:
    if not samples:
        return 0.0
    return math.sqrt(sum(s * s for s in samples) / len(samples))


def diarize(path: str, window_seconds: float = 0.5) -> list[dict]:
    rate, data = read_mono_16bit(path)
    samples = samples_from_bytes(data)
    window_size = int(rate * window_seconds)

    features = []
    for start in range(0, len(samples), window_size):
        chunk = samples[start : start + window_size]
        if rms(chunk) < 0.01:
            continue
        features.append(
            {
                "start": start / rate,
                "end": min(start + window_size, len(samples)) / rate,
                "zcr": zero_crossing_rate(chunk),
            }
        )

    if not features:
        return []

    # Classify into two speakers by median zero-crossing rate.
    zcrs = [f["zcr"] for f in features]
    threshold = sum(zcrs) / len(zcrs)

    segments = []
    current_speaker = "Speaker 1" if features[0]["zcr"] <= threshold else "Speaker 2"
    current_start = features[0]["start"]
    current_end = features[0]["end"]

    for feature in features[1:]:
        speaker = "Speaker 1" if feature["zcr"] <= threshold else "Speaker 2"
        if speaker == current_speaker:
            current_end = feature["end"]
        else:
            segments.append(
                {
                    "start": current_start,
                    "end": current_end,
                    "speaker": current_speaker,
                }
            )
            current_speaker = speaker
            current_start = feature["start"]
            current_end = feature["end"]

    segments.append(
        {
            "start": current_start,
            "end": current_end,
            "speaker": current_speaker,
        }
    )
    return segments


def main() -> None:
    parser = argparse.ArgumentParser(description="Local speaker diarization")
    parser.add_argument("audio", help="input WAV file")
    parser.add_argument("--output", required=True, help="output JSON file")
    parser.add_argument(
        "--window", type=float, default=0.5, help="analysis window in seconds"
    )
    args = parser.parse_args()

    segments = diarize(args.audio, args.window)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(segments, f, indent=2)


if __name__ == "__main__":
    main()
