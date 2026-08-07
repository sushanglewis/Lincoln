#!/usr/bin/env python3
"""从 RELEASE.md 抽取指定版本的发布说明,供 GitHub Release 等发布流程复用。

匹配的节标题形态:`# Lincoln vX.Y.Z ...`、`# vX.Y.Z ...`、`## vX.Y.Z ...`;
抽取范围从节标题起到下一个同级或更高级标题之前。用法:

    python3 scripts/extract_release_notes.py 1.6.0
    python3 scripts/extract_release_notes.py v1.6.0 --root /path/to/repo
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
RELEASE_FILE = "RELEASE.md"


def section_matcher(version: str) -> re.Pattern:
    """匹配节标题文本:`Lincoln ` 前缀可选,版本号后必须是空白或行尾。"""
    return re.compile(rf"^(?:Lincoln\s+)?v{re.escape(version)}(?=\s|$)")


def extract_section(text: str, version: str) -> str | None:
    """抽取 version 对应章节;找不到返回 None。"""
    matcher = section_matcher(version)
    lines = text.splitlines()
    start: int | None = None
    level = 0
    for i, line in enumerate(lines):
        heading = HEADING.match(line)
        if heading and len(heading.group(1)) <= 2 and matcher.match(heading.group(2)):
            start, level = i, len(heading.group(1))
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        heading = HEADING.match(lines[j])
        if heading and len(heading.group(1)) <= level:
            end = j
            break
    return "\n".join(lines[start:end]).rstrip()


def main(argv: list[str], root: Path = ROOT) -> int:
    args = argv[1:]
    if "--root" in args:
        index = args.index("--root")
        if index + 1 >= len(args):
            print("--root requires a path", file=sys.stderr)
            return 2
        root = Path(args[index + 1])
        del args[index : index + 2]
    if len(args) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    version = args[0].removeprefix("v")
    if not SEMVER.match(version):
        print(f"invalid semver (want X.Y.Z): {args[0]!r}", file=sys.stderr)
        return 2
    release = root / RELEASE_FILE
    if not release.exists():
        print(f"missing release notes: {RELEASE_FILE}", file=sys.stderr)
        return 1
    section = extract_section(release.read_text(encoding="utf-8"), version)
    if section is None:
        print(f"section for v{version} not found in {RELEASE_FILE}", file=sys.stderr)
        return 1
    print(section)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
