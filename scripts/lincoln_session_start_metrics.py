#!/usr/bin/env python3
"""Estimate the token cost of a Lincoln session-start hook output (#63).

Tries tiktoken for an accurate count; falls back to a stable heuristic
(CJK characters as one token each, whitespace-separated non-CJK words as
tokens) so the metric stays deterministic without requiring an extra dependency.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

CJK_RE = re.compile(
    r"[一-鿿぀-ゟ゠-ヿ가-힯]"
)


def estimate_tokens(text: str) -> int:
    """Return a deterministic token estimate for *text*."""
    try:
        import tiktoken  # type: ignore

        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        pass

    cjk_tokens = len(CJK_RE.findall(text))
    non_cjk = CJK_RE.sub(" ", text)
    word_tokens = len(non_cjk.split())
    return cjk_tokens + word_tokens


def compute_metrics(text: str, stage: str = "", status: str = "") -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "stage": stage,
        "status": status,
        "bytes": len(text.encode("utf-8")),
        "chars": len(text),
        "tokens": estimate_tokens(text),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Estimate token count for a Lincoln session-start output."
    )
    parser.add_argument("--input", type=Path, required=True, help="File to analyze.")
    parser.add_argument("--output", type=Path, required=True, help="JSON output path.")
    parser.add_argument("--stage", default="", help="Current stage id.")
    parser.add_argument("--status", default="", help="Current stage status.")
    args = parser.parse_args(argv)

    text = args.input.read_text(encoding="utf-8")
    metrics = compute_metrics(text, stage=args.stage, status=args.status)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
