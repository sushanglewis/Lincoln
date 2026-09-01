#!/usr/bin/env python3
"""Risk analyzer for Lincoln pre-tool-use security gate.

Loads `.claude/policies/security.yaml` and evaluates a tool call against the
configured policies. Designed to be invoked from `.claude/hooks/pre-tool-use.sh`
and from generated harness-specific hook scripts.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

DEFAULT_POLICY_PATH = ".claude/policies/security.yaml"


def load_policy(root: Path) -> dict[str, Any]:
    """Load the risk policy YAML, returning an empty policy if missing."""
    path = root / DEFAULT_POLICY_PATH
    if not path.exists():
        return {"policies": []}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {"policies": []}


def _normalize_command(command: str) -> str:
    """Strip leading whitespace and collapse internal spaces for matching."""
    return re.sub(r"\s+", " ", command.strip())


def _split_command_segments(command: str) -> list[str]:
    """Split a shell command on chain operators so each segment is matched.

    Handles `&&`, `||`, `;`, and `|`.
    """
    segments = re.split(r"\s*(&&|\|\||;|\|)\s*", command)
    return [_normalize_command(seg) for seg in segments if seg and not re.match(r"^(&&|\|\||;|\|)$", seg.strip())]


def _strip_command_prefix(segment: str) -> str:
    """Remove common leading prefixes that should not hide the real command.

    Examples: `sudo rm foo`, `env VAR=1 rm foo`, `cd /tmp && rm foo`.
    """
    segment = _normalize_command(segment)
    while re.match(r"^[A-Za-z_][A-Za-z0-9_]*=\S+\s+", segment):
        segment = _normalize_command(re.sub(r"^[A-Za-z_][A-Za-z0-9_]*=\S+\s+", "", segment))
    if re.match(r"^(sudo|doas)\s+", segment):
        segment = _normalize_command(re.sub(r"^(sudo|doas)\s+", "", segment))
    if re.match(r"^cd\s+\S+\s*(&&|;|\|)", segment):
        segment = _normalize_command(re.sub(r"^cd\s+\S+\s*(&&|;|\|)", "", segment))
    return segment


def _command_matches(condition: str, command: str) -> bool:
    """Evaluate a human-readable condition against a bash command."""
    lowered = condition.lower()
    segments = _split_command_segments(command)

    def _any_segment(pattern: str) -> bool:
        return any(re.search(pattern, _strip_command_prefix(seg)) for seg in segments)

    if "rm -rf" in lowered or 'command matches "rm -rf"' in lowered:
        if _any_segment(r"\brm\s+-rf\b"):
            return True

    if 'command matches "rm -r" or "rm -rf"' in lowered:
        if _any_segment(r"\brm\s+-r(?:f)?\b"):
            return True

    if 'command matches any of ["rm", "rmdir"]' in lowered:
        if _any_segment(r"(?:^|\s)(?:rm\b|rmdir\b)"):
            return True

    if 'command matches "git push"' in lowered:
        if _any_segment(r"\bgit\s+push\b"):
            return True

    if "external http client" in lowered or "curl, wget" in lowered:
        if _any_segment(r"\b(?:curl|wget|httpie)\b"):
            return True

    if 'command matches "rm"' in lowered and "rmdir" not in lowered:
        if _any_segment(r"\brm\b"):
            return True

    return False


def _resolve_target_path(target: str, root: Path) -> Path:
    """Resolve a Write/Edit target to an absolute, canonical path."""
    path = Path(target)
    if not path.is_absolute():
        path = root / path
    try:
        return path.resolve()
    except (OSError, ValueError):
        return path.absolute()


def _target_matches(condition: str, target: str, process_slug: str, root: Path) -> bool:
    """Evaluate a file-target condition using canonical absolute paths."""
    lowered = condition.lower()
    resolved = _resolve_target_path(target, root)
    try:
        package_root = (root / process_slug).resolve()
    except (OSError, ValueError):
        package_root = (root / process_slug).absolute()

    if "outside current process_slug" in lowered:
        try:
            resolved.relative_to(package_root)
            return False
        except ValueError:
            return True

    if "inside current process_slug" in lowered:
        try:
            resolved.relative_to(package_root)
            return True
        except ValueError:
            return False

    return False


def _evaluate_policy(policy: dict[str, Any], tool_name: str, tool_args: dict[str, Any], process_slug: str, root: Path) -> bool:
    """Return True if the policy applies to this tool call."""
    tools = [t.strip() for t in policy.get("tool", "").split("|")]
    if tool_name not in tools:
        return False

    condition = policy.get("condition", "")
    if tool_name == "Bash":
        command = tool_args.get("command", "")
        return _command_matches(condition, command)

    if tool_name in ("Write", "Edit"):
        target = tool_args.get("file_path") or tool_args.get("path") or ""
        return _target_matches(condition, target, process_slug, root)

    return False


def _log_security_event(
    log_dir: Path,
    tool_name: str,
    tool_args: dict[str, Any],
    result: dict[str, Any],
) -> None:
    """Append a JSON line to issue-<N>/logs/security.log."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "security.log"
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool": tool_name,
        "level": result["level"],
        "policy": result.get("policy", ""),
        "action": "blocked" if result["confirm_required"] else "allowed",
        "args": {k: v for k, v in tool_args.items() if k in ("command", "file_path", "path")},
    }
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def analyze(
    root: Path,
    tool_name: str,
    tool_args: dict[str, Any],
    process_slug: str = "",
    log_dir: str | None = None,
) -> dict[str, Any]:
    """Analyze a tool call and return risk assessment."""
    if os.environ.get("LINCOLN_SECURITY_MODE") == "permissive":
        return {
            "level": "low",
            "policy": "",
            "message": "Security analyzer is in permissive mode.",
            "confirm_required": False,
            "log": False,
        }

    policy_data = load_policy(root)
    policies = policy_data.get("policies", [])

    for policy in policies:
        if not _evaluate_policy(policy, tool_name, tool_args, process_slug, root):
            continue

        result = {
            "level": policy.get("level", "unknown"),
            "policy": policy.get("name", ""),
            "message": policy.get("message", ""),
            "confirm_required": bool(policy.get("confirm", False)),
            "log": bool(policy.get("log", False)),
        }
        if log_dir:
            _log_security_event(Path(log_dir), tool_name, tool_args, result)
        return result

    return {
        "level": "low",
        "policy": "",
        "message": "",
        "confirm_required": False,
        "log": False,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze tool call risk")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--tool", required=True)
    parser.add_argument("--args", default="{}")
    parser.add_argument("--process-slug", default="")
    parser.add_argument("--log-dir", default=None)
    args = parser.parse_args()

    tool_args = json.loads(args.args)
    result = analyze(
        args.root,
        args.tool,
        tool_args,
        process_slug=args.process_slug,
        log_dir=args.log_dir,
    )
    print(json.dumps(result, ensure_ascii=False))
