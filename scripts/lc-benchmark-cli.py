#!/usr/bin/env python3
"""Explicit CLI entry point for Lincoln benchmark reports (#72).

This wrapper resolves the current workflow state (using the same logic as the
hooks) and forwards to scripts/lincoln_benchmark.py. It makes `/lc-benchmark`
a deterministic, opt-in command instead of an implicit side effect of session
stop or PR events.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts import lincoln_benchmark  # noqa: E402
from scripts.lincoln_paths import resolve_state_path  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a Lincoln benchmark report (opt-in)."
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        help="Path to workflow-stage.yaml. Auto-resolved if omitted.",
    )
    parser.add_argument(
        "--trigger",
        choices=["manual", "handoff", "pr_created", "pr_merged", "session_stop"],
        default="manual",
        help="Benchmark trigger context (default: manual).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    state_file = args.state_file
    if state_file is None:
        state_file = resolve_state_path(None, _PROJECT_ROOT)

    if not state_file.exists():
        print(
            "No Lincoln workflow state found. "
            "Run this from a repo with an active issue work package.",
            file=sys.stderr,
        )
        return 1

    # Avoid recursive trace logging when benchmark is invoked from a hook.
    os.environ["LINCOLN_SKIP_TRACE"] = "1"
    return lincoln_benchmark.main(
        ["--state-file", str(state_file), "--trigger", args.trigger]
    )


if __name__ == "__main__":
    sys.exit(main())
