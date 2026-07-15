#!/usr/bin/env python3
"""Check upstream drift for pinned external skill dependencies (#62).

Compares each git-sourced skill/plugin's pinned `ref` in
`.claude/skills/dependencies.yaml` against the current upstream branch head
(`pinned_from`, default `main`). Prints a report; exits 1 when any dependency
has drifted (i.e. an upgrade review is due), 0 when all pins are current.

This tool needs network access and is run manually (or from scheduled jobs),
never from the offline test suite.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEPENDENCIES = ROOT / ".claude" / "skills" / "dependencies.yaml"
GIT_SOURCE_PREFIXES = ("http://", "https://", "git@")


def upstream_head(source: str, branch: str) -> str | None:
    proc = subprocess.run(
        ["git", "ls-remote", source, branch],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    return proc.stdout.split()[0]


def main() -> int:
    data = yaml.safe_load(DEPENDENCIES.read_text(encoding="utf-8"))
    drifted = False
    for name, dep in data.get("skills", {}).items():
        if dep.get("type") not in ("skill", "plugin"):
            continue
        source = str(dep.get("source", ""))
        if not source.startswith(GIT_SOURCE_PREFIXES):
            continue
        ref = str(dep.get("ref", ""))
        branch = str(dep.get("pinned_from", "main"))
        try:
            head = upstream_head(source, branch)
        except (subprocess.TimeoutExpired, OSError) as exc:
            print(f"WARN  {name}: upstream check failed ({exc}); skipped")
            continue
        if head is None:
            print(f"WARN  {name}: cannot resolve {branch} at {source}; skipped")
            continue
        if head == ref:
            print(f"OK    {name}: pinned at {ref[:12]} (current {branch})")
        else:
            drifted = True
            print(
                f"DRIFT {name}: pinned {ref[:12]}, upstream {branch} is {head[:12]}"
                " — review upstream changes, run the benchmark, then update the pin"
            )
    return 1 if drifted else 0


if __name__ == "__main__":
    sys.exit(main())
