#!/usr/bin/env python3
"""Print the content of a Lincoln skill.

Usage:
    python3 scripts/lincoln_skill_prompt.py --skill lc-first-principles
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lincoln_paths import PROJECT_ROOT  # noqa: E402

SKILLS_DIR = PROJECT_ROOT / ".claude" / "skills"


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a Lincoln skill prompt")
    parser.add_argument("--skill", required=True, help="Skill folder name")
    args = parser.parse_args()

    skill_dir = SKILLS_DIR / args.skill
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        print(f"ERROR: skill not found: {skill_dir}", file=sys.stderr)
        return 1

    parts = [skill_md.read_text(encoding="utf-8")]
    prompt_path = skill_dir / "prompts" / "main.md"
    if prompt_path.exists():
        parts.append(prompt_path.read_text(encoding="utf-8"))

    print("\n\n".join(parts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
