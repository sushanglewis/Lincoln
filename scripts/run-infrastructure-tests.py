#!/usr/bin/env python3
"""Run the deterministic infrastructure test suite (#67).

This script is the entry point for the CI `infrastructure-tests` job. It runs
only tests that do not depend on LLM calls, network access, or stochastic
behavior, so they can be used as a fast, reliable gate.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INFRASTRUCTURE_TESTS = [
    "tests/test_yaml_schemas.py",
    "tests/test_bump_version.py",
    "tests/test_harness_default_off.py",
    "tests/test_session_start_shape.py",
    "tests/test_infrastructure_layers.py",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Lincoln deterministic infrastructure tests."
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="Exit with non-zero status if any test fails.",
    )
    parser.add_argument(
        "--collect-only",
        action="store_true",
        help="List the tests that would be run without executing them.",
    )
    parser.add_argument(
        "pytest_args",
        nargs="*",
        help="Additional arguments to pass to pytest.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    missing = [t for t in INFRASTRUCTURE_TESTS if not (ROOT / t).exists()]
    if missing:
        print("Missing infrastructure test files:")
        for m in missing:
            print(f"  - {m}")
        return 1

    if args.collect_only:
        print("Infrastructure test suite:")
        for t in INFRASTRUCTURE_TESTS:
            print(f"  {t}")
        return 0

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        *INFRASTRUCTURE_TESTS,
        "-v",
        *(args.pytest_args or []),
    ]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=ROOT)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
