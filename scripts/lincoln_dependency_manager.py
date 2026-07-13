#!/usr/bin/env python3
"""Dependency manager for Lincoln setup automation.

Reads `.claude/skills/dependencies.yaml` as the single source of truth and
provides functions to check, install, and configure external skills, CLIs,
and repository settings used by the Lincoln workflow.
"""

from __future__ import annotations

import platform
import re
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml


# Placeholder values that signal an unconfigured OpenSpec config file.
_PLACEHOLDER_OWNERS = {"your-org", "sushanglewis"}
_PLACEHOLDER_NAMES = {"your-repo", "your-product-repo", "product-manager"}

_DEFAULT_OPENSPEC_CONFIG = {
    "repository": {
        "owner": "your-org",
        "name": "your-product-repo",
        "default_branch": "main",
    },
    "workflow": {
        "auto_create_issues": True,
        "default_labels": ["from-interview", "openspec"],
        "knowledge_sync": {"enabled": True, "actor": "github-actions"},
    },
    "openspec": {"profile": "default", "telemetry": False},
}


def load_dependencies(project_root: Path) -> dict[str, Any]:
    """Load and parse `.claude/skills/dependencies.yaml`."""
    dep_file = project_root / ".claude" / "skills" / "dependencies.yaml"
    if not dep_file.exists():
        raise FileNotFoundError(f"Dependency manifest not found: {dep_file}")
    return yaml.safe_load(dep_file.read_text(encoding="utf-8"))


def detect_platform() -> str | None:
    """Return 'macos', 'linux', or None for unsupported platforms."""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    if system == "linux":
        return "linux"
    return None


def _get_platform(dep: dict[str, Any], platform_name: str | None) -> str | None:
    """Return the install command for the given platform, if declared."""
    platforms = dep.get("platforms")
    if not platforms:
        return None
    return platforms.get(platform_name) if platform_name else None


def get_install_command(dep: dict[str, Any], platform_name: str | None) -> str | None:
    """Build the best-effort install command for a dependency.

    For skills/plugins without a platform map, fall back to a git clone command.
    For CLIs, use the platform map. Returns None when no command can be derived.
    """
    typ = dep.get("type", "skill")
    source = dep.get("source", "")
    ref = dep.get("ref", "")

    if typ in ("skill", "plugin"):
        platform_cmd = _get_platform(dep, platform_name)
        if platform_cmd:
            return platform_cmd
        if source and source != "inline":
            target = Path.home() / ".claude" / "skills" / dep.get("_name", "unknown")
            branch_arg = f"--branch {ref}" if ref else ""
            return f"git clone {branch_arg} --single-branch --depth 1 {source} {target}"
        return None

    if typ == "cli":
        return _get_platform(dep, platform_name)

    return None


def check_clis(manifest: dict[str, Any], platform_name: str | None = None) -> list[dict[str, Any]]:
    """Return a list of missing CLI dependencies with install instructions."""
    missing: list[dict[str, Any]] = []
    for name, cfg in manifest.get("skills", {}).items():
        if cfg.get("type") != "cli":
            continue
        binary = cfg.get("binary", name)
        if shutil.which(binary):
            continue
        missing.append(
            {
                "name": name,
                "type": "cli",
                "binary": binary,
                "required": cfg.get("required", True),
                "install_command": get_install_command(cfg, platform_name),
                "install_note": cfg.get("install_note", ""),
                "source": cfg.get("source", ""),
            }
        )
    return missing


def check_skills(
    manifest: dict[str, Any], project_root: Path, skills_dir: Path
) -> list[dict[str, Any]]:
    """Return a list of missing skill/plugin dependencies with install instructions."""
    missing: list[dict[str, Any]] = []
    for name, cfg in manifest.get("skills", {}).items():
        typ = cfg.get("type", "skill")
        if typ not in ("skill", "plugin"):
            continue

        source = cfg.get("source", "")
        is_required = cfg.get("required", True)
        default_install = cfg.get("default_install", is_required)

        if source == "inline":
            path = project_root / cfg.get("path", f".claude/skills/{name}")
            expected = path / "SKILL.md"
        else:
            expected = skills_dir / name / "SKILL.md"

        if expected.exists():
            continue

        cfg_with_name = dict(cfg)
        cfg_with_name["_name"] = name
        missing.append(
            {
                "name": name,
                "type": typ,
                "required": is_required,
                "default_install": default_install,
                "install_command": get_install_command(cfg_with_name, detect_platform()),
                "install_note": cfg.get("install_note", ""),
                "source": source,
                "ref": cfg.get("ref", ""),
                "expected_path": str(expected),
            }
        )
    return missing


def _run_command(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    """Run a shell command and return the completed process."""
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        check=False,
        **kwargs,
    )


def _resolve_remote_sha(target: Path, ref: str) -> str:
    """Resolve a remote ref (branch or tag) to a commit SHA; empty on failure."""
    proc = _run_command(["git", "-C", str(target), "ls-remote", "origin", ref])
    if proc.returncode != 0 or not proc.stdout.strip():
        return ""
    return proc.stdout.split()[0]


def install_skill(
    name: str,
    source: str,
    ref: str,
    skills_dir: Path,
    offline_cache: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Install or update an external skill/plugin into `skills_dir/name`.

    Returns a result dict with keys: name, installed, skipped, error.
    """
    target = skills_dir / name
    result: dict[str, Any] = {"name": name, "installed": False, "skipped": False, "error": ""}

    if target.exists():
        # Check current ref and working tree state.
        status_proc = _run_command(["git", "-C", str(target), "status", "--porcelain"])
        if status_proc.stdout.strip():
            result["error"] = f"Working tree of {target} is dirty; aborting."
            return result

        describe_proc = _run_command(
            ["git", "-C", str(target), "describe", "--tags", "--exact-match"]
        )
        current_tag = describe_proc.stdout.strip() if describe_proc.returncode == 0 else ""
        if current_tag == ref:
            result["skipped"] = True
            return result

        rev_proc = _run_command(["git", "-C", str(target), "rev-parse", "HEAD"])
        local_sha = rev_proc.stdout.strip() if rev_proc.returncode == 0 else ""
        remote_sha = _resolve_remote_sha(target, ref)
        if remote_sha and local_sha == remote_sha:
            result["skipped"] = True
            return result

        current_ref = current_tag or local_sha
        if dry_run:
            result["error"] = f"Would update {name} from {current_ref} to {ref}."
            return result

        fetch_proc = _run_command(["git", "-C", str(target), "fetch", "origin", ref])
        if fetch_proc.returncode != 0:
            result["error"] = f"Failed to fetch {ref}: {fetch_proc.stderr.strip()}"
            return result

        checkout_proc = _run_command(["git", "-C", str(target), "checkout", "FETCH_HEAD"])
        if checkout_proc.returncode != 0:
            result["error"] = f"Failed to checkout {ref}: {checkout_proc.stderr.strip()}"
            return result

        result["installed"] = True
        return result

    # Fresh install.
    if dry_run:
        result["error"] = f"Would clone {name} at {ref}."
        result["dry_run"] = True
        return result

    target.parent.mkdir(parents=True, exist_ok=True)

    # Try offline cache first when provided.
    if offline_cache:
        cached = offline_cache / name
        if cached.exists():
            clone_proc = _run_command(
                ["git", "clone", "--branch", ref, "--single-branch", "--depth", "1", str(cached), str(target)]
            )
            if clone_proc.returncode == 0:
                result["installed"] = True
                return result

    branch_args = ["--branch", ref] if ref else []
    args = ["git", "clone", *branch_args, "--single-branch", "--depth", "1", source, str(target)]
    clone_proc = _run_command(args)
    if clone_proc.returncode != 0:
        result["error"] = f"Failed to clone {name}: {clone_proc.stderr.strip()}"
        return result

    result["installed"] = True
    return result


def install_cli(name: str, command: str, dry_run: bool = False) -> dict[str, Any]:
    """Install a CLI dependency using the platform-specific command.

    Returns a result dict with keys: name, installed, dry_run, error.
    """
    result: dict[str, Any] = {"name": name, "installed": False, "dry_run": dry_run, "error": ""}

    if dry_run:
        return result

    # Tokenize the command string, preserving quoted arguments.
    args = shlex.split(command)
    proc = _run_command(args)
    if proc.returncode != 0:
        result["error"] = proc.stderr.strip() or f"Command exited with {proc.returncode}"
        return result

    result["installed"] = True
    return result


def init_openspec_config(
    owner: str, name: str, branch: str, config_path: Path
) -> dict[str, Any]:
    """Write or update `.github/openspec-config.yml` when it still has placeholders.

    Returns a result dict with keys: updated, skipped, error.
    """
    result: dict[str, Any] = {"updated": False, "skipped": False, "error": ""}

    config_path.parent.mkdir(parents=True, exist_ok=True)

    if config_path.exists():
        try:
            data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except Exception as exc:
            result["error"] = f"Failed to parse {config_path}: {exc}"
            return result
    else:
        data = {}

    repository = data.get("repository") or {}
    current_owner = repository.get("owner", "")
    current_name = repository.get("name", "")

    if (
        current_owner not in _PLACEHOLDER_OWNERS
        and current_name not in _PLACEHOLDER_NAMES
        and current_owner
        and current_name
    ):
        result["skipped"] = True
        return result

    base = _DEFAULT_OPENSPEC_CONFIG.copy()
    base["repository"] = {
        "owner": owner,
        "name": name,
        "default_branch": branch,
    }
    # Merge with any existing non-repository sections to preserve user edits.
    merged = {**base, **{k: v for k, v in data.items() if k != "repository"}}
    merged["repository"] = base["repository"]

    try:
        config_path.write_text(
            yaml.safe_dump(merged, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
    except Exception as exc:
        result["error"] = f"Failed to write {config_path}: {exc}"
        return result

    result["updated"] = True
    return result
