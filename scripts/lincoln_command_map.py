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
import sys
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lincoln_paths import PROJECT_ROOT  # noqa: E402

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


def list_workflows() -> dict[str, dict[str, Any]]:
    workflows: dict[str, dict[str, Any]] = {}
    for path in sorted(WORKFLOWS_DIR.glob("*.yaml")):
        data = load_yaml(path)
        wf = data.get("workflow", {})
        workflows[path.stem] = {
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
        agents[path.stem] = {
            "name": front.get("name", path.stem),
            "description": front.get("description", ""),
        }
    return agents


def list_skills() -> dict[str, dict[str, Any]]:
    skills: dict[str, dict[str, Any]] = {}
    for path in sorted(SKILLS_DIR.iterdir()):
        if not path.is_dir():
            continue
        skill_md = path / "SKILL.md"
        if not skill_md.exists():
            continue
        front, _ = split_frontmatter(skill_md.read_text(encoding="utf-8"))
        skills[path.name] = {
            "name": front.get("name", path.name),
            "description": front.get("description", ""),
        }
    return skills


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    try:
        front = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        front = {}
    if not isinstance(front, dict):
        front = {}
    return front, parts[2].lstrip("\n")


def build_commands() -> dict[str, dict[str, Any]]:
    existing = load_command_map().get("commands", {})
    commands: dict[str, dict[str, Any]] = {}

    # 1. Preserve static commands exactly as they are.
    for key in STATIC_COMMANDS:
        if key in existing:
            commands[key] = existing[key]

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
        key = f"lc-skill-{folder}"
        if key in STATIC_COMMANDS:
            continue
        commands[key] = {
            "description": skill["description"] or f"调用 {folder} 技能",
            "action": f"python3 scripts/lincoln_skill_prompt.py --skill {folder}",
            "args_hint": "$ARGUMENTS",
        }

    # 5. Scenario commands.
    for sid, scenario in load_scenarios().items():
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
    COMMAND_MAP_PATH.write_text(HEADER + "\n" + yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"Updated {COMMAND_MAP_PATH.relative_to(PROJECT_ROOT)} ({len(commands)} commands)")


def refresh_plugin_json() -> None:
    if not PLUGIN_PATH.exists():
        raise SystemExit(f"ERROR: plugin.json not found: {PLUGIN_PATH}")
    plugin = json.loads(PLUGIN_PATH.read_text(encoding="utf-8"))

    skill_paths = []
    for path in sorted(SKILLS_DIR.iterdir()):
        if not path.is_dir():
            continue
        if not (path / "SKILL.md").exists():
            continue
        skill_paths.append(f"./.claude/skills/{path.name}/")

    plugin["skills"] = skill_paths
    PLUGIN_PATH.write_text(json.dumps(plugin, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
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
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Maintain Lincoln /lc-* command surface")
    parser.add_argument("--refresh", action="store_true", help="Regenerate command-map.yaml and plugin.json")
    parser.add_argument("--check", action="store_true", help="Check if command-map.yaml is in sync")
    args = parser.parse_args()

    if args.refresh:
        refresh_command_map()
        refresh_plugin_json()
        return 0
    if args.check:
        return check()
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
