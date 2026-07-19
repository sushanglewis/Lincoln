#!/usr/bin/env python3
"""Deterministic packaging for the Lincoln plugin (#68).

Builds a reproducible distribution archive from an explicit allowlist, rejects
dirty worktrees, regenerates harness artifacts after version bumps, and emits a
SHA256 checksum. Does not upload to any marketplace or registry.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]

ALLOWLIST_DIRS = (".claude", ".claude-plugin", "scripts", "tools")
ALLOWLIST_FILES = (
    "README.md",
    "CLAUDE.md",
    "LICENSE",
    "RELEASE.md",
    ".version-bump.json",
    "requirements.txt",
)
DENYLIST_NAMES = {
    ".git",
    ".context",
    ".venv",
    "venv",
    "dist",
    "oss",
    ".pytest_cache",
    "__pycache__",
    ".DS_Store",
    "node_modules",
}
DENYLIST_PREFIXES = ("issue-",)
SKIP_PATHS = (".claude/templates/issue-package",)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build or validate a deterministic Lincoln plugin package."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="Repository root (default: repository containing this script).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    pkg = subparsers.add_parser("package", help="Build the distribution archive.")
    pkg.add_argument(
        "--output-dir",
        type=Path,
        default=Path("dist"),
        help="Output directory for the archive and checksum.",
    )
    pkg.add_argument(
        "--format",
        choices=("tgz", "zip"),
        default="tgz",
        help="Archive format (default: tgz).",
    )
    pkg.add_argument(
        "--force-harness",
        action="store_true",
        help="Regenerate harness artifacts even if they already exist.",
    )

    chk = subparsers.add_parser(
        "check", help="Validate allowlist/denylist without building."
    )
    chk.add_argument(
        "--check-dirty",
        action="store_true",
        help="Also reject dirty worktrees in check mode.",
    )

    return parser.parse_args(argv)


def load_version(root: Path) -> str:
    source = root / ".version-bump.json"
    if not source.exists():
        sys.exit("missing version source: .version-bump.json")
    data = json.loads(source.read_text(encoding="utf-8"))
    version = data.get("version", "")
    if not (isinstance(version, str) and len(version.split(".")) == 3):
        sys.exit(f".version-bump.json has invalid version: {version!r}")
    return version


def is_dirty(root: Path) -> bool:
    """Return True if the working tree has uncommitted tracked changes."""
    for diff_flag in ("--quiet", "--cached", "--quiet"):
        result = subprocess.run(
            ["git", "diff", diff_flag, "HEAD"],
            cwd=root,
            capture_output=True,
        )
        if result.returncode != 0:
            return True
    return False


def git_head_timestamp(root: Path) -> int:
    """Return the Unix timestamp of HEAD for reproducible archives."""
    result = subprocess.run(
        ["git", "log", "-1", "--format=%ct"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        env_epoch = os.environ.get("SOURCE_DATE_EPOCH", "")
        if env_epoch.isdigit():
            return int(env_epoch)
        return 0
    return int(result.stdout.strip())


def regenerate_harness(root: Path, force: bool) -> None:
    """Regenerate codex/opencode harness artifacts if they exist or force=True."""
    adapter = root / "scripts" / "lincoln_harness_adapter.py"
    any_artifact = any(
        (root / ".claude" / "harnesses" / f"{harness}.yaml").exists()
        for harness in ("codex", "opencode")
    )
    if not adapter.exists():
        if any_artifact:
            sys.exit("missing harness adapter: scripts/lincoln_harness_adapter.py")
        return

    for harness in ("codex", "opencode"):
        artifact = root / ".claude" / "harnesses" / f"{harness}.yaml"
        if artifact.exists() and not force:
            continue
        print(f"Regenerating harness artifact: {artifact.relative_to(root)}")
        result = subprocess.run(
            [sys.executable, str(adapter), "--harness", harness],
            cwd=root,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(result.stderr, file=sys.stderr)
            sys.exit(f"harness generation failed for {harness}")


def collect_sources(root: Path) -> Iterable[Path]:
    """Yield every file that belongs in the package, validating the allowlist."""
    for name in ALLOWLIST_DIRS:
        src_dir = root / name
        if not src_dir.exists():
            sys.exit(f"allowlist directory missing: {name}")
        for path in src_dir.rglob("*"):
            if path.is_file():
                yield path

    for name in ALLOWLIST_FILES:
        src_file = root / name
        if not src_file.exists():
            sys.exit(f"allowlist file missing: {name}")
        yield src_file


def is_denylisted(relative: str) -> bool:
    parts = Path(relative).parts
    return any(
        part in DENYLIST_NAMES or part.startswith(DENYLIST_PREFIXES)
        for part in parts
    )


def is_skipped(relative: str) -> bool:
    return any(relative.startswith(skip) for skip in SKIP_PATHS)


def clean_generated(root: Path) -> None:
    """Remove generated artifacts that should never be packaged."""
    for name in ALLOWLIST_DIRS:
        base = root / name
        if not base.exists():
            continue
        for pycache in base.rglob("__pycache__"):
            if pycache.is_dir():
                shutil.rmtree(pycache, ignore_errors=True)
        for ds_store in base.rglob(".DS_Store"):
            if ds_store.is_file():
                ds_store.unlink(missing_ok=True)


def validate_manifest(root: Path) -> None:
    clean_generated(root)
    version = load_version(root)
    for src in collect_sources(root):
        rel = str(src.relative_to(root))
        if is_skipped(rel):
            continue
        if is_denylisted(rel):
            sys.exit(f"denylist violation in package: {rel}")
    print(f"Package manifest OK for version {version}")


def stage_package(root: Path, staging: Path) -> None:
    """Copy allowlisted sources into a staging directory for archiving."""
    clean_generated(root)
    for src in collect_sources(root):
        rel = src.relative_to(root)
        if is_skipped(str(rel)) or is_denylisted(str(rel)):
            continue
        dst = staging / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def archive_mtime(root: Path) -> int:
    env = os.environ.get("SOURCE_DATE_EPOCH", "")
    if env.isdigit():
        return int(env)
    return git_head_timestamp(root)


def archive_time_tuple(epoch: int) -> tuple[int, int, int, int, int, int]:
    dt = datetime.fromtimestamp(epoch, tz=timezone.utc)
    return (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)


def build_tgz(root: Path, staging: Path, output: Path, epoch: int) -> None:
    with tarfile.open(output, "w:gz") as tar:

        def _reset(tarinfo: tarfile.TarInfo) -> tarfile.TarInfo:
            tarinfo.mtime = epoch
            tarinfo.uid = tarinfo.gid = 0
            tarinfo.uname = tarinfo.gname = ""
            return tarinfo

        tar.add(staging, arcname=f"lincoln-{load_version(root)}", filter=_reset)


def build_zip(root: Path, staging: Path, output: Path, epoch: int) -> None:
    time_tuple = archive_time_tuple(epoch)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in staging.rglob("*"):
            if not file_path.is_file():
                continue
            arcname = (
                f"lincoln-{load_version(root)}/{file_path.relative_to(staging)}"
            )
            zf.write(file_path, arcname)
            # Normalize timestamps after writing (zipfile does not expose this easily)
            info = zf.getinfo(arcname)
            info.date_time = time_tuple


def write_checksum(output: Path) -> None:
    sha256 = hashlib.sha256(output.read_bytes()).hexdigest()
    checksum_file = output.with_suffix(output.suffix + ".sha256")
    checksum_file.write_text(f"{sha256}  {output.name}\n", encoding="utf-8")


def cmd_check(args: argparse.Namespace) -> int:
    if args.check_dirty and is_dirty(args.root):
        print("error: working tree has uncommitted changes", file=sys.stderr)
        return 1
    validate_manifest(args.root)
    return 0


def cmd_package(args: argparse.Namespace) -> int:
    if is_dirty(args.root):
        print(
            "error: refusing to package a dirty working tree. "
            "Commit or stash changes first.",
            file=sys.stderr,
        )
        return 1

    regenerate_harness(args.root, args.force_harness)
    validate_manifest(args.root)

    output_dir = args.root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    version = load_version(args.root)
    ext = "tar.gz" if args.format == "tgz" else "zip"
    output = output_dir / f"lincoln-{version}.{ext}"

    epoch = archive_mtime(args.root)

    staging = args.root / ".context" / "package-staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    try:
        stage_package(args.root, staging)
        if args.format == "tgz":
            build_tgz(args.root, staging, output, epoch)
        else:
            build_zip(args.root, staging, output, epoch)
        write_checksum(output)
        print(f"Packaged {output.relative_to(args.root)}")
        print(f"Checksum  {output.with_suffix(output.suffix + '.sha256').relative_to(args.root)}")
        return 0
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "check":
        return cmd_check(args)
    if args.command == "package":
        return cmd_package(args)
    return 2


if __name__ == "__main__":
    sys.exit(main())
