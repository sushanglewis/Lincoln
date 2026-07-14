#!/usr/bin/env python3
"""Merge diarization output with transcript segments."""

import argparse
import json


def overlap(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    return max(0.0, min(a_end, b_end) - max(a_start, b_start))


def merge(transcript: list[dict], diarization: list[dict]) -> list[dict]:
    merged = []
    for t in transcript:
        t_start = t.get("start", 0.0)
        t_end = t.get("end", t_start)
        best_speaker = None
        best_overlap = 0.0
        for d in diarization:
            d_start = d.get("start", 0.0)
            d_end = d.get("end", d_start)
            ov = overlap(t_start, t_end, d_start, d_end)
            if ov > best_overlap:
                best_overlap = ov
                best_speaker = d.get("speaker")
        merged.append(
            {
                "start": t_start,
                "end": t_end,
                "speaker": best_speaker,
                "text": t.get("text", ""),
            }
        )
    return merged


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge diarization with transcript")
    parser.add_argument("transcript", help="transcript JSON file")
    parser.add_argument("diarization", help="diarization JSON file")
    parser.add_argument("--output", required=True, help="output JSON file")
    args = parser.parse_args()

    with open(args.transcript, encoding="utf-8") as f:
        transcript = json.load(f)
    with open(args.diarization, encoding="utf-8") as f:
        diarization = json.load(f)

    merged = merge(transcript, diarization)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2)


if __name__ == "__main__":
    main()
