#!/usr/bin/env python3
"""Reject branch-only Lincoln process artifacts from main-bound PRs."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.lincoln_paths import RESERVED_PROCESS_DIRS


ROOT_PROCESS_DIRS = {
    "designs",
    "interviews",
    "recordings",
    "requirements",
}

PROCESS_SUBPATHS = {
    "designs",
    "docs/research",
    "handoffs",
    "interviews",
    "openspec/changes",
    "recordings",
    "requirements",
}

ALLOWED_ROOT_PREFIXES = (
    ".claude/",
    ".conductor/",
    ".github/",
    "CLAUDE.md",
    "README.md",
    "docs/framework/",
    "knowledge/",
    "oss/README.md",
    "oss/projects.yaml",
    "products/",
    "scripts/",
    "tests/",
    "tools/",
)


def changed_paths(base: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def is_process_package_path(path: str) -> bool:
    parts = Path(path).parts
    if not parts:
        return False
    top = parts[0]
    if top in RESERVED_PROCESS_DIRS or top in ROOT_PROCESS_DIRS:
        return False
    if len(parts) == 2 and parts[1] == "workflow-stage.yaml":
        return True
    rest = "/".join(parts[1:])
    return any(rest == sub or rest.startswith(f"{sub}/") for sub in PROCESS_SUBPATHS)


def is_root_process_artifact(path: str) -> bool:
    return any(path.startswith(f"{prefix}/") for prefix in ROOT_PROCESS_DIRS) or path.startswith("openspec/changes/") or path.startswith("docs/research/")


def allowed_durable_path(path: str) -> bool:
    return any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in ALLOWED_ROOT_PREFIXES)


def violations(paths: list[str]) -> list[str]:
    rejected: list[str] = []
    for path in paths:
        if is_process_package_path(path) or is_root_process_artifact(path):
            rejected.append(path)
            continue
        if path.startswith("oss/clones/"):
            rejected.append(path)
    return rejected


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Lincoln main merge hygiene")
    parser.add_argument("--base", default="origin/main")
    parser.add_argument("--path", action="append", dest="paths", help="Changed path to check; repeatable")
    args = parser.parse_args()

    paths = args.paths if args.paths is not None else changed_paths(args.base)
    bad = violations(paths)
    if bad:
        print("FAIL: branch-only Lincoln process artifacts must not merge to main:")
        for path in bad:
            print(f"  - {path}")
        print("Move durable knowledge to knowledge/ and keep process work in the feature branch.")
        return 1

    print("PASS: no branch-only Lincoln process artifacts detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
