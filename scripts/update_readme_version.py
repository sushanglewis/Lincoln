#!/usr/bin/env python3
"""README 版本引用锁步工具(配合 bump_version.py 的事实源 `.version-bump.json`)。

README.md / README.en.md 中的 release 徽章与版本公告行不属于 JSON manifest,
无法被 bump 的 JSON Pointer 覆盖,由本脚本按正则锁步。用法:

    python3 scripts/update_readme_version.py                    # 锁步更新两份 README
    python3 scripts/update_readme_version.py --check            # CI:验证 README 与事实源一致
    python3 scripts/update_readme_version.py --root /path/repo  # 指定仓库根(默认脚本上一级)
    python3 scripts/update_readme_version.py --allow-downgrade  # 允许把 README 版本号改小
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
VERSION_EXTRACT = re.compile(r"v(\d+\.\d+\.\d+)")

BADGE = re.compile(r"(https://img\.shields\.io/badge/release-v)\d+\.\d+\.\d+(-blue)")
CALLOUT_ZH = re.compile(r"(\*\*v)\d+\.\d+\.\d+(\*\* 已发布)")
CALLOUT_EN = re.compile(r"(\*\*v)\d+\.\d+\.\d+(\*\* is released)")

READMES = (
    ("README.md", CALLOUT_ZH),
    ("README.en.md", CALLOUT_EN),
)


def parse_semver(version: str) -> tuple[int, int, int]:
    return tuple(int(part) for part in version.split("."))


def is_newer(left: str, right: str) -> bool:
    return parse_semver(left) > parse_semver(right)


def load_version(root: Path) -> str:
    source = root / ".version-bump.json"
    if not source.exists():
        sys.exit("missing version source: .version-bump.json")
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.exit(f"malformed .version-bump.json: {exc}")
    version = data.get("version", "")
    if not SEMVER.match(version):
        sys.exit(f".version-bump.json has invalid version: {version!r}")
    return version


def sync_text(text: str, version: str, patterns: Iterable[re.Pattern[str]]) -> str:
    """把 text 中所有 pattern 命中的版本号替换为 version,返回新文本(不原地修改)。"""
    for pattern in patterns:
        text = pattern.sub(lambda m: m.group(1) + version + m.group(2), text)
    return text


def find_stale(text: str, version: str, patterns: Iterable[re.Pattern[str]]) -> str | None:
    """返回第一个与事实源不一致的命中片段;无命中或已一致返回 None。"""
    for pattern in patterns:
        for match in pattern.finditer(text):
            if match.group(0) != match.group(1) + version + match.group(2):
                return match.group(0)
    return None


def readme_version(text: str) -> str | None:
    """从 README 文本中提取第一个 vX.Y.Z 版本号(徽章或公告行)。"""
    match = VERSION_EXTRACT.search(text)
    return match.group(1) if match else None


def cmd_update(root: Path, check: bool, allow_downgrade: bool) -> int:
    version = load_version(root)
    drifted: list[tuple[str, str]] = []
    skipped: list[tuple[str, str]] = []

    for name, callout in READMES:
        path = root / name
        if not path.exists():
            sys.exit(f"missing README: {name}")
        original = path.read_text(encoding="utf-8")
        stale = find_stale(original, version, (BADGE, callout))
        if stale is None:
            continue

        current = readme_version(original)
        if current is not None and is_newer(current, version) and not allow_downgrade:
            skipped.append((name, current))
            continue

        drifted.append((name, stale))
        if not check:
            path.write_text(
                sync_text(original, version, (BADGE, callout)), encoding="utf-8"
            )

    if skipped:
        print(
            f"README version(s) newer than source v{version}; skipping to avoid downgrade. "
            "Use --allow-downgrade to force.",
            file=sys.stderr,
        )
        for name, current in skipped:
            print(f"  {name}: v{current} -> v{version} skipped", file=sys.stderr)

    if check:
        if drifted:
            print(f"README version drift detected (source: v{version}):", file=sys.stderr)
            for name, stale in drifted:
                print(f"  {name}: {stale!r} != v{version}", file=sys.stderr)
            print("fix: python3 scripts/update_readme_version.py", file=sys.stderr)
            return 1
        print(f"README version lockstep OK: {version} ({len(READMES)} files)")
        return 0

    for name, _ in drifted:
        print(f"  updated {name} -> v{version}")
    if drifted:
        print(f"updated {len(drifted)} README(s) to v{version}")
    elif not skipped:
        print(f"READMEs already at v{version}; nothing to do")
    return 0 if not skipped else 1


def main(argv: list[str], root: Path = ROOT) -> int:
    parser = argparse.ArgumentParser(
        description="Sync README version badges and callouts with .version-bump.json."
    )
    parser.add_argument("--check", action="store_true", help="verify lockstep without writing")
    parser.add_argument("--root", type=Path, default=root, help="repository root")
    parser.add_argument(
        "--allow-downgrade",
        action="store_true",
        help="allow rewriting README version to an older version",
    )
    args = parser.parse_args(argv[1:])
    return cmd_update(args.root, check=args.check, allow_downgrade=args.allow_downgrade)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
