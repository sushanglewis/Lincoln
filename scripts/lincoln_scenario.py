#!/usr/bin/env python3
"""Print the prompt for a Lincoln scenario.

Usage:
    python3 scripts/lincoln_scenario.py --scenario make-prd [topic words...]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lincoln_paths import PROJECT_ROOT, validate_name  # noqa: E402

SCENARIOS_PATH = PROJECT_ROOT / ".claude" / "harnesses" / "scenarios.yaml"


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a Lincoln scenario prompt")
    parser.add_argument("--scenario", required=True, help="Scenario id")
    parser.add_argument("topic", nargs="*", help="Optional topic/context")
    args = parser.parse_args()

    if not SCENARIOS_PATH.exists():
        print(f"ERROR: scenarios file not found: {SCENARIOS_PATH}", file=sys.stderr)
        return 1

    try:
        validate_name(args.scenario, "scenario id")
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    data = yaml.safe_load(SCENARIOS_PATH.read_text(encoding="utf-8")) or {}
    scenarios = data.get("scenarios", {})
    scenario = scenarios.get(args.scenario)
    if not scenario:
        available = ", ".join(sorted(scenarios))
        print(f"ERROR: scenario '{args.scenario}' not found. Available: {available}", file=sys.stderr)
        return 1

    if args.topic:
        print(f"Topic/context: {' '.join(args.topic)}\n")
    print(f"# Scenario: {args.scenario}")
    print(f"\nDescription: {scenario.get('description', '')}")
    print(f"Recommended role: {scenario.get('role', '')}")
    print(f"Skills: {', '.join(scenario.get('skills', []))}")
    print(f"\nGoal: {scenario.get('goal', '')}")
    print("\nExecute the recommended skills in order. Follow Lincoln stage gates and human_gate rules.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
