#!/usr/bin/env python3
"""Print the content of a Lincoln agent role.

Usage:
    python3 scripts/lincoln_role.py --role pm [topic words...]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lincoln_paths import PROJECT_ROOT  # noqa: E402

AGENTS_DIR = PROJECT_ROOT / ".claude" / "agents"


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a Lincoln agent role")
    parser.add_argument("--role", required=True, help="Agent role filename stem")
    parser.add_argument("topic", nargs="*", help="Optional topic/context")
    args = parser.parse_args()

    path = AGENTS_DIR / f"{args.role}.md"
    if not path.exists():
        print(f"ERROR: agent role not found: {path}", file=sys.stderr)
        return 1

    text = path.read_text(encoding="utf-8")
    if args.topic:
        print(f"Topic/context: {' '.join(args.topic)}\n")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
