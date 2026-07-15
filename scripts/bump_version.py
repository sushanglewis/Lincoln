#!/usr/bin/env python3
"""版本锁步工具(#68:借鉴 superpowers 的 plugin/marketplace 版本漂移教训)。

`.version-bump.json` 是版本号唯一事实源,用 RFC 6901 JSON Pointer 列出所有
携带版本号的 manifest 位置。用法:

    python3 scripts/bump_version.py bump 1.3.0     # 锁步更新事实源与所有 manifest
    python3 scripts/bump_version.py --check        # CI:验证所有 manifest 与事实源一致
    python3 scripts/bump_version.py --audit 1.2.0  # 发布前:列出残留的旧版本引用
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")

# audit 模式中合理保留旧版本号的位置(历史记录,不是漂移);
# package-lock 内依赖自身版本号易误报,其产品版本由 bump 按 pointer 精确维护
AUDIT_EXCLUDES = (
    ":!RELEASE.md",
    ":!knowledge",
    ":!issue-*",
    ":!.context",
    ":!tools/lincoln/package-lock.json",
)


def load_source(root: Path) -> dict:
    source = root / ".version-bump.json"
    if not source.exists():
        sys.exit("missing version source: .version-bump.json")
    data = json.loads(source.read_text(encoding="utf-8"))
    if not SEMVER.match(data.get("version", "")):
        sys.exit(f".version-bump.json has invalid version: {data.get('version')!r}")
    return data


def parse_pointer(pointer: str) -> list[str]:
    if not pointer.startswith("/"):
        raise ValueError(f"pointer must start with '/': {pointer!r}")
    return [t.replace("~1", "/").replace("~0", "~") for t in pointer.split("/")[1:]]


def resolve(container, tokens: list[str]):
    """沿 pointer tokens 走到末段的父容器,返回 (父容器, 末段 key)。"""
    node = container
    for token in tokens[:-1]:
        node = node[int(token)] if isinstance(node, list) else node[token]
    last = tokens[-1]
    return node, int(last) if isinstance(node, list) else last


def iter_versions(data: dict, root: Path):
    """yield (manifest_path, pointer, current_value);manifest 缺失即失败。"""
    for manifest in data["manifests"]:
        path = root / manifest["path"]
        if not path.exists():
            sys.exit(f"manifest listed in .version-bump.json is missing: {manifest['path']}")
        doc = json.loads(path.read_text(encoding="utf-8"))
        for pointer in manifest["pointers"]:
            parent, key = resolve(doc, parse_pointer(pointer))
            yield manifest["path"], pointer, parent[key]


def cmd_check(data: dict, root: Path) -> int:
    expected = data["version"]
    drift = [
        f"  {path}{pointer}: {value!r} != {expected!r}"
        for path, pointer, value in iter_versions(data, root)
        if value != expected
    ]
    if drift:
        print("version drift detected:", file=sys.stderr)
        print("\n".join(drift), file=sys.stderr)
        print(f"fix: python3 scripts/bump_version.py bump {expected}", file=sys.stderr)
        return 1
    print(f"version lockstep OK: {expected} ({len(data['manifests'])} manifests)")
    return 0


def cmd_bump(data: dict, root: Path, new_version: str) -> int:
    if not SEMVER.match(new_version):
        sys.exit(f"invalid semver (want X.Y.Z): {new_version!r}")
    old_version = data["version"]
    for manifest in data["manifests"]:
        path = root / manifest["path"]
        doc = json.loads(path.read_text(encoding="utf-8"))
        for pointer in manifest["pointers"]:
            parent, key = resolve(doc, parse_pointer(pointer))
            parent[key] = new_version
        path.write_text(
            json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"  bumped {manifest['path']}")
    data["version"] = new_version
    (root / ".version-bump.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"bumped {old_version} -> {new_version}")
    print(f"next: python3 scripts/bump_version.py --audit {old_version}")
    return 0


def cmd_audit(root: Path, old_version: str) -> int:
    if not SEMVER.match(old_version):
        sys.exit(f"invalid semver (want X.Y.Z): {old_version!r}")
    result = subprocess.run(
        ["git", "grep", "-n", "-F", old_version, "--", ".", *AUDIT_EXCLUDES],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode not in (0, 1):
        sys.exit(f"git grep failed: {result.stderr.strip()}")
    if result.returncode == 1:
        print(f"audit OK: no stale {old_version} references")
        return 0
    print(f"stale {old_version} references (review each; RELEASE.md/knowledge 等历史记录已排除):")
    print(result.stdout, end="")
    return 1


def main(argv: list[str], root: Path = ROOT) -> int:
    args = argv[1:]
    if args == ["--check"]:
        return cmd_check(load_source(root), root)
    if len(args) == 2 and args[0] == "bump":
        return cmd_bump(load_source(root), root, args[1])
    if len(args) == 2 and args[0] == "--audit":
        return cmd_audit(root, args[1])
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
