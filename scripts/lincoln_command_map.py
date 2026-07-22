#!/usr/bin/env python3
"""Auto-maintain the Lincoln /lc-* command surface.

Usage:
    python3 scripts/lincoln_command_map.py --refresh
    python3 scripts/lincoln_command_map.py --check

--refresh regenerates `.claude/harnesses/command-map.yaml` and syncs
`.claude-plugin/plugin.json` from the current on-disk skill/agent/workflow
facts.  Static lifecycle commands are preserved.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lincoln_paths import (  # noqa: E402
    PROJECT_ROOT,
    atomic_write_text,
    validate_name,
)

COMMAND_MAP_PATH = PROJECT_ROOT / ".claude" / "harnesses" / "command-map.yaml"
SCENARIOS_PATH = PROJECT_ROOT / ".claude" / "harnesses" / "scenarios.yaml"
PLUGIN_PATH = PROJECT_ROOT / ".claude-plugin" / "plugin.json"
WORKFLOWS_DIR = PROJECT_ROOT / ".claude" / "workflows"
AGENTS_DIR = PROJECT_ROOT / ".claude" / "agents"
SKILLS_DIR = PROJECT_ROOT / ".claude" / "skills"

# Lifecycle commands that are hand-maintained and must never be overwritten.
STATIC_COMMANDS = {
    "lc-status",
    "lc-setup",
    "lc-init-branch",
    "lc-validate",
    "lc-handoff",
    "lc-submit",
    "lc-approve",
    "lc-benchmark",
    "lc-wf-list",
}

HEADER = """# lc-* 命令单一事实源(Single source of truth)
# 三个 harness manifest(claude-code.yaml / codex.yaml / opencode.yaml)通过
# command_map_source: command-map.yaml 引用本文件。
# 新增/修改命令请运行: python3 scripts/lincoln_command_map.py --refresh
"""

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_command_map() -> dict[str, Any]:
    if not COMMAND_MAP_PATH.exists():
        return {}
    return load_yaml(COMMAND_MAP_PATH)


def load_scenarios() -> dict[str, Any]:
    if not SCENARIOS_PATH.exists():
        return {}
    return load_yaml(SCENARIOS_PATH).get("scenarios", {})


def _clean_name(value: str, kind: str) -> str:
    """Validate an identifier before embedding it into commands or paths."""
    return validate_name(value, kind)


def _iter_skill_dirs():
    """Yield skill directories that contain a SKILL.md manifest."""
    for path in sorted(SKILLS_DIR.iterdir()):
        if not path.is_dir():
            continue
        if not (path / "SKILL.md").exists():
            continue
        yield path


def list_workflows() -> dict[str, dict[str, Any]]:
    workflows: dict[str, dict[str, Any]] = {}
    for path in sorted(WORKFLOWS_DIR.glob("*.yaml")):
        data = load_yaml(path)
        wf = data.get("workflow", {}) if isinstance(data, dict) else {}
        stem = _clean_name(path.stem, "workflow name")
        workflows[stem] = {
            "name": wf.get("name", path.stem),
            "description": wf.get("description", ""),
            "execution_mode": wf.get("execution_mode", "team"),
        }
    return workflows


def list_agents() -> dict[str, dict[str, Any]]:
    agents: dict[str, dict[str, Any]] = {}
    excluded = {"default.md", "_contract.md"}
    for path in sorted(AGENTS_DIR.glob("*.md")):
        if path.name in excluded:
            continue
        front, _ = split_frontmatter(path.read_text(encoding="utf-8"))
        stem = _clean_name(path.stem, "agent name")
        agents[stem] = {
            "name": front.get("name", path.stem),
            "description": front.get("description", ""),
        }
    return agents


def list_skills() -> dict[str, dict[str, Any]]:
    skills: dict[str, dict[str, Any]] = {}
    for path in _iter_skill_dirs():
        front, _ = split_frontmatter((path / "SKILL.md").read_text(encoding="utf-8"))
        folder = _clean_name(path.name, "skill folder name")
        skills[folder] = {
            "name": front.get("name", path.name),
            "description": front.get("description", ""),
        }
    return skills


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    try:
        front = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        front = {}
    if not isinstance(front, dict):
        front = {}
    body_start = match.end()
    return front, text[body_start:].lstrip("\n")


def _skill_command_key(folder: str) -> str:
    """Avoid lc-skill-lc-* duplication by stripping a leading lc- prefix."""
    return f"lc-skill-{folder.removeprefix('lc-')}"


def build_commands() -> dict[str, dict[str, Any]]:
    existing = load_command_map().get("commands", {})
    commands: dict[str, dict[str, Any]] = {}

    # 1. Preserve static commands exactly as they are.
    missing_static = []
    for key in STATIC_COMMANDS:
        if key in existing:
            commands[key] = existing[key]
        else:
            missing_static.append(key)
    if missing_static:
        print(
            f"WARNING: static commands missing from existing map: {', '.join(missing_static)}",
            file=sys.stderr,
        )

    # 2. Workflow commands.
    for stem, wf in list_workflows().items():
        key = f"lc-wf-{stem}"
        if key in STATIC_COMMANDS:
            continue
        if wf["execution_mode"] == "team":
            args_hint = f"start --workflow {stem} --issue-number <N>"
        else:
            args_hint = f"start --workflow {stem}"
        commands[key] = {
            "description": wf["description"] or f"启动 {stem} 工作流",
            "action": "python3 scripts/lincoln_workflow.py",
            "args_hint": args_hint,
        }

    # 3. Agent commands.
    for stem, agent in list_agents().items():
        key = f"lc-agent-{stem}"
        if key in STATIC_COMMANDS:
            continue
        commands[key] = {
            "description": agent["description"] or f"调用 {stem} 角色",
            "action": f"python3 scripts/lincoln_role.py --role {stem}",
            "args_hint": "$ARGUMENTS",
        }

    # 4. Skill commands.
    for folder, skill in list_skills().items():
        key = _skill_command_key(folder)
        if key in STATIC_COMMANDS:
            continue
        commands[key] = {
            "description": skill["description"] or f"调用 {folder} 技能",
            "action": f"python3 scripts/lincoln_skill_prompt.py --skill {folder}",
            "args_hint": "$ARGUMENTS",
        }

    # 5. Scenario commands.
    for sid, scenario in load_scenarios().items():
        sid = _clean_name(sid, "scenario id")
        key = f"lc-scenario-{sid}"
        if key in STATIC_COMMANDS:
            continue
        commands[key] = {
            "description": scenario.get("description", f"场景: {sid}"),
            "action": f"python3 scripts/lincoln_scenario.py --scenario {sid}",
            "args_hint": "$ARGUMENTS",
        }

    return dict(sorted(commands.items()))


def refresh_command_map() -> None:
    commands = build_commands()
    data = {"commands": commands}
    atomic_write_text(
        COMMAND_MAP_PATH,
        HEADER + yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    print(f"Updated {COMMAND_MAP_PATH.relative_to(PROJECT_ROOT)} ({len(commands)} commands)")


def refresh_plugin_json() -> None:
    if not PLUGIN_PATH.exists():
        raise SystemExit(f"ERROR: plugin.json not found: {PLUGIN_PATH}")
    plugin = json.loads(PLUGIN_PATH.read_text(encoding="utf-8"))

    skill_paths = [f"./.claude/skills/{path.name}/" for path in _iter_skill_dirs()]

    plugin["skills"] = skill_paths
    atomic_write_text(
        PLUGIN_PATH,
        json.dumps(plugin, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Updated {PLUGIN_PATH.relative_to(PROJECT_ROOT)} ({len(skill_paths)} skills)")


def check() -> int:
    commands = build_commands()
    existing = load_command_map().get("commands", {})
    missing = set(commands) - set(existing)
    extra = set(existing) - set(commands)
    changed: list[str] = []
    for key in set(commands) & set(existing):
        if commands[key] != existing[key]:
            changed.append(key)
    if not (missing or extra or changed):
        print("command-map.yaml is up to date.")
        return 0
    if missing:
        print("Missing commands:", ", ".join(sorted(missing)))
    if extra:
        print("Extra commands:", ", ".join(sorted(extra)))
    if changed:
        print("Changed commands:", ", ".join(sorted(changed)))
    try:
        script_rel = Path(__file__).relative_to(PROJECT_ROOT)
    except ValueError:
        script_rel = Path("scripts/lincoln_command_map.py")
    print(f"Run: python3 {script_rel} --refresh")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Maintain Lincoln /lc-* command surface")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--refresh", action="store_true", help="Regenerate command-map.yaml and plugin.json")
    group.add_argument("--check", action="store_true", help="Check if command-map.yaml is in sync")
    args = parser.parse_args()

    if args.refresh:
        refresh_command_map()
        refresh_plugin_json()
        return 0
    return check()


if __name__ == "__main__":
    sys.exit(main())
