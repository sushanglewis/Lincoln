#!/usr/bin/env python3
"""Check prompt drift across Lincoln's agent/stage/workflow/skill layers.

Rules:
  R1: agent extends targets must exist.
  R2: workflow step action must be in corresponding stage skills.required.
  R3: workflow step artifacts must match stage artifacts.
  R4: primary skill outputs must match stage artifacts.
  R5: agent artifact paths must be a subset of stage artifacts.
  R6: stage skill references must be declared in dependencies or local skills.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = ROOT / ".claude" / "agents"
STAGES_DIR = ROOT / ".claude" / "stages"
WORKFLOWS_DIR = ROOT / ".claude" / "workflows"
SKILLS_DIR = ROOT / ".claude" / "skills"
DEP_FILE = ROOT / ".claude" / "skills" / "dependencies.yaml"

PM_STAGES = {"clarify", "product-design-docs", "product-prototype"}


def parse_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("---", 3)
    if end == -1:
        return {}
    try:
        return yaml.safe_load(text[3:end]) or {}
    except yaml.YAMLError:
        return {}


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def normalize_path(path: str) -> str:
    """Strip trailing slashes and collapse placeholders for comparison."""
    return path.rstrip("/")


def glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Convert a simple glob pattern with * and ** to a regex."""
    parts = []
    i = 0
    while i < len(pattern):
        if pattern[i : i + 2] == "**":
            parts.append(".*")
            i += 2
        elif pattern[i] == "*":
            parts.append("[^/]*")
            i += 1
        else:
            parts.append(re.escape(pattern[i]))
            i += 1
    return re.compile("^" + "".join(parts) + "$")


def paths_match(a: str, b: str) -> bool:
    """Compare two artifact paths, treating globs specially."""
    a = normalize_path(a)
    b = normalize_path(b)
    if a == b:
        return True
    # If one is a glob, see if the other matches.
    if "*" in a:
        return bool(glob_to_regex(a).match(b))
    if "*" in b:
        return bool(glob_to_regex(b).match(a))
    return False


def path_in_set(path: str, path_set: set[str]) -> bool:
    for candidate in path_set:
        if paths_match(path, candidate):
            return True
    return False


def collect_agents() -> dict[str, dict[str, Any]]:
    agents: dict[str, dict[str, Any]] = {}
    for path in sorted(AGENTS_DIR.glob("*.md")):
        front = parse_frontmatter(path)
        agents[path.name] = {
            "path": path,
            "front": front,
            "body": path.read_text(encoding="utf-8"),
        }
    return agents


def collect_stages() -> dict[str, dict[str, Any]]:
    stages: dict[str, dict[str, Any]] = {}
    for path in sorted(STAGES_DIR.glob("*.yaml")):
        if path.name == "stage-manifest.yaml":
            continue
        data = load_yaml(path)
        if isinstance(data, dict):
            stages[data.get("id", path.stem)] = {"path": path, "data": data}
    return stages


def collect_workflows() -> dict[str, dict[str, Any]]:
    workflows: dict[str, dict[str, Any]] = {}
    for path in sorted(WORKFLOWS_DIR.glob("*.yaml")):
        data = load_yaml(path)
        if isinstance(data, dict) and "workflow" in data:
            workflows[data["workflow"].get("name", path.stem)] = {"path": path, "data": data["workflow"]}
    return workflows


def collect_skills() -> dict[str, dict[str, Any]]:
    skills: dict[str, dict[str, Any]] = {}
    for path in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        front = parse_frontmatter(path)
        skills[path.parent.name] = {"path": path, "front": front}
    return skills


def collect_dependencies() -> set[str]:
    declared: set[str] = set()
    if not DEP_FILE.exists():
        return declared
    data = load_yaml(DEP_FILE)
    if not isinstance(data, dict):
        return declared
    for namespace, info in (data.get("skills") or {}).items():
        if not isinstance(info, dict):
            continue
        # Local inline skills are implicitly declared.
        if info.get("source") == "inline" or info.get("type") == "inline":
            declared.add(namespace)
            continue
        # Register the namespace itself so any namespaced ref under it is acceptable.
        declared.add(namespace)
        for skill in info.get("required_skills", []) or []:
            declared.add(normalize_skill_ref(namespace, skill))
        for skill in info.get("recommended_skills", []) or []:
            declared.add(normalize_skill_ref(namespace, skill))
    return declared


def normalize_skill_ref(namespace: str, skill: str) -> str:
    """Return a canonical namespaced skill reference.

    dependencies.yaml mixes formats: some entries are already namespaced
    ("superpowers:brainstorming", "oh-my-claudecode:plan") while others use
    a prefixed bare name ("gsd-import"). Normalize to "namespace:name".
    """
    skill = skill.strip()
    if skill.startswith(f"{namespace}:"):
        return skill
    if skill.startswith(f"{namespace}-"):
        return f"{namespace}:{skill[len(namespace) + 1:]}"
    return f"{namespace}:{skill}"


def collect_local_skill_names() -> set[str]:
    return {p.parent.name for p in SKILLS_DIR.glob("*/SKILL.md")}


def artifact_paths(stage: dict[str, Any]) -> tuple[set[str], set[str]]:
    required = set()
    optional = set()
    artifacts = stage.get("artifacts", {})
    for p in artifacts.get("required", []):
        required.add(normalize_path(str(p)))
    for p in artifacts.get("optional", []):
        optional.add(normalize_path(str(p)))
    return required, optional


def check_r1_extends_resolve(agents: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    findings = []
    for name, info in agents.items():
        for extends_ref in info["front"].get("extends", []) or []:
            resolved = ROOT / ".claude" / extends_ref
            if not resolved.exists():
                findings.append({
                    "rule": "R1",
                    "severity": "error",
                    "stage_focus": False,
                    "file": f".claude/agents/{name}",
                    "message": f"extends '{extends_ref}' does not resolve to an existing file",
                })
    return findings


def check_r2_action_in_stage_skills(
    workflows: dict[str, dict[str, Any]],
    stages: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    findings = []
    for wf_name, wf_info in workflows.items():
        for step in wf_info["data"].get("steps", []) or []:
            stage_id = step.get("id")
            action = step.get("action")
            if not stage_id or not action:
                continue
            stage = stages.get(stage_id)
            if not stage:
                continue
            stage_name = stage["data"].get("id", stage_id)
            required_skills = stage["data"].get("skills", {}).get("required", []) or []
            # Workflow actions map to either local skills (<action>) or namespaced skills.
            possible_ids = {action, f"lincoln:{action}"}
            if not any(skill in possible_ids for skill in required_skills):
                findings.append({
                    "rule": "R2",
                    "severity": "error",
                    "stage_focus": stage_name in PM_STAGES,
                    "file": f".claude/workflows/{wf_name}.yaml",
                    "message": (
                        f"step '{stage_id}' action '{action}' is not listed in "
                        f"stage '{stage_id}' skills.required: {required_skills}"
                    ),
                })
    return findings


PM_CANONICAL_WORKFLOW = "interview-to-knowledge"


def check_r3_workflow_artifacts_match_stage(
    workflows: dict[str, dict[str, Any]],
    stages: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    findings = []
    for wf_name, wf_info in workflows.items():
        # For PM stages, only the canonical workflow is held to strict artifact equality.
        # Other workflows may intentionally use a subset of PM stage artifacts.
        is_pm_canonical = wf_name == PM_CANONICAL_WORKFLOW
        for step in wf_info["data"].get("steps", []) or []:
            stage_id = step.get("id")
            if not stage_id:
                continue
            stage = stages.get(stage_id)
            if not stage:
                continue
            stage_name = stage["data"].get("id", stage_id)
            is_pm_stage = stage_name in PM_STAGES
            stage_required, stage_optional = artifact_paths(stage["data"])

            wf_required = {normalize_path(p) for p in step.get("artifacts", []) or []}
            wf_optional = {normalize_path(p) for p in step.get("optional_artifacts", []) or []}

            severity = "error" if (is_pm_stage and is_pm_canonical) else "warning"

            # Compare required sets modulo glob matching.
            for p in wf_required:
                if not path_in_set(p, stage_required):
                    findings.append({
                        "rule": "R3",
                        "severity": severity,
                        "stage_focus": is_pm_stage,
                        "file": f".claude/workflows/{wf_name}.yaml",
                        "message": f"step '{stage_id}' required artifact '{p}' missing from stage '{stage_id}' required artifacts",
                    })
            for p in stage_required:
                if not path_in_set(p, wf_required):
                    findings.append({
                        "rule": "R3",
                        "severity": severity,
                        "stage_focus": is_pm_stage,
                        "file": f".claude/stages/{stage_id}.yaml",
                        "message": f"stage '{stage_id}' required artifact '{p}' missing from workflow '{wf_name}' step artifacts",
                    })

            for p in wf_optional:
                if not (path_in_set(p, stage_optional) or path_in_set(p, stage_required)):
                    findings.append({
                        "rule": "R3",
                        "severity": "warning",
                        "stage_focus": is_pm_stage,
                        "file": f".claude/workflows/{wf_name}.yaml",
                        "message": f"step '{stage_id}' optional artifact '{p}' not declared in stage '{stage_id}' artifacts",
                    })
            for p in stage_optional:
                if not path_in_set(p, wf_optional):
                    findings.append({
                        "rule": "R3",
                        "severity": "warning",
                        "stage_focus": is_pm_stage,
                        "file": f".claude/stages/{stage_id}.yaml",
                        "message": f"stage '{stage_id}' optional artifact '{p}' missing from workflow '{wf_name}' optional_artifacts",
                    })
    return findings


def check_r4_skill_outputs_match_stage(
    workflows: dict[str, dict[str, Any]],
    stages: dict[str, dict[str, Any]],
    skills: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    findings = []
    for wf_name, wf_info in workflows.items():
        for step in wf_info["data"].get("steps", []) or []:
            stage_id = step.get("id")
            action = step.get("action")
            if not stage_id or not action:
                continue
            stage = stages.get(stage_id)
            if not stage:
                continue
            stage_name = stage["data"].get("id", stage_id)
            stage_required, stage_optional = artifact_paths(stage["data"])

            # Find the primary skill by action name.
            primary_skill = skills.get(action)
            if primary_skill is None:
                # Also try namespaced form.
                for key, val in skills.items():
                    if val["front"].get("name") == action or val["front"].get("name") == f"lincoln:{action}":
                        primary_skill = val
                        break
            if primary_skill is None:
                continue

            outputs = {normalize_path(p) for p in primary_skill["front"].get("outputs", []) or []}
            all_stage_artifacts = stage_required | stage_optional
            for p in outputs:
                if not path_in_set(p, all_stage_artifacts):
                    findings.append({
                        "rule": "R4",
                        "severity": "warning",
                        "stage_focus": stage_name in PM_STAGES,
                        "file": str(primary_skill["path"].relative_to(ROOT)),
                        "message": f"skill output '{p}' not declared in stage '{stage_id}' artifacts",
                    })
            for p in stage_required:
                if not path_in_set(p, outputs):
                    findings.append({
                        "rule": "R4",
                        "severity": "error",
                        "stage_focus": stage_name in PM_STAGES,
                        "file": f".claude/stages/{stage_id}.yaml",
                        "message": f"stage '{stage_id}' required artifact '{p}' missing from skill '{action}' outputs",
                    })
    return findings


def extract_output_sections(body: str) -> list[str]:
    """Return text blocks under output/artifact sections in agent markdown."""
    sections = []
    # Match headings like ## 产物规范, ## Outputs, ## 产物, ### `clarify` 阶段
    heading_re = re.compile(r"^(#{2,4}\s+(?:产物规范|Outputs|产物|Output).*)$", re.MULTILINE | re.IGNORECASE)
    for match in heading_re.finditer(body):
        start = match.end()
        # Find the next heading of same or higher level
        next_heading = re.search(r"^#{1,4}\s+", body[start:], re.MULTILINE)
        end = start + next_heading.start() if next_heading else len(body)
        sections.append(body[start:end])
    return sections


def extract_artifact_paths(body: str) -> set[str]:
    """Extract likely artifact output paths from agent markdown body.

    Only scans sections that describe outputs/artifacts to avoid flagging
    input references (e.g., handoff files read by designer).
    """
    paths: set[str] = set()
    sections = extract_output_sections(body)
    if not sections:
        sections = [body]
    for section in sections:
        for match in re.finditer(r"`(\{process_slug\}/[^`]+)`", section):
            candidate = match.group(1).strip("`")
            if "/" in candidate:
                paths.add(normalize_path(candidate))
        for match in re.finditer(r"(?:^|\s)(\{process_slug\}/[\w\-./{}*]+)", section):
            candidate = match.group(1).strip()
            if "/" in candidate and not candidate.endswith(":"):
                paths.add(normalize_path(candidate))
    return paths


def check_r5_agent_paths_in_stage_artifacts(
    agents: dict[str, dict[str, Any]],
    stages: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    findings = []
    for agent_name, info in agents.items():
        front = info["front"]
        agent_name_attr = front.get("name", agent_name)
        paths = extract_artifact_paths(info["body"])
        if not paths:
            continue

        # Find all stages where this agent is primary and collect their artifacts.
        agent_stage_ids = []
        all_stage_artifacts: set[str] = set()
        for stage_id, stage in stages.items():
            primary = stage["data"].get("agent", {}).get("primary", "")
            if primary != agent_name_attr:
                continue
            agent_stage_ids.append(stage_id)
            required, optional = artifact_paths(stage["data"])
            all_stage_artifacts |= required | optional

        if not agent_stage_ids:
            continue

        for p in paths:
            if not path_in_set(p, all_stage_artifacts):
                findings.append({
                    "rule": "R5",
                    "severity": "error",
                    "stage_focus": any(sid in PM_STAGES for sid in agent_stage_ids),
                    "file": f".claude/agents/{agent_name}",
                    "message": f"agent '{agent_name_attr}' references artifact '{p}' not declared in any of its primary stages ({', '.join(agent_stage_ids)}) artifacts",
                })
    return findings


def check_r6_skill_dependencies_declared(
    stages: dict[str, dict[str, Any]],
    declared: set[str],
    local_skills: set[str],
) -> list[dict[str, Any]]:
    findings = []
    for stage_id, stage in stages.items():
        skills_block = stage["data"].get("skills", {})
        all_refs = list(skills_block.get("required", []) or []) + list(skills_block.get("optional", []) or [])
        for ref in all_refs:
            if ":" not in ref:
                # Bare local skill name.
                if ref not in local_skills:
                    findings.append({
                        "rule": "R6",
                        "severity": "error",
                        "stage_focus": stage_id in PM_STAGES,
                        "file": f".claude/stages/{stage_id}.yaml",
                        "message": f"skill '{ref}' not declared in dependencies.yaml and not a local skill",
                    })
                continue
            namespace, skill_name = ref.split(":", 1)
            # Local inline namespace like lincoln:*.
            if namespace in local_skills or namespace == "lincoln":
                # lincoln:* names are mapped to local skill directory names.
                if namespace != "lincoln" and namespace in local_skills:
                    continue
                if skill_name in local_skills:
                    continue
                # Some lincoln skills use hyphenated names in dirs (e.g., lc-stage).
                if skill_name.replace("-", "_") in {s.replace("-", "_") for s in local_skills}:
                    continue
            if ref in declared:
                continue
            # Also accept namespace-only declaration for gsd/superpowers.
            if namespace in declared and f"{namespace}:{skill_name}" not in declared:
                continue
            findings.append({
                "rule": "R6",
                "severity": "error",
                "stage_focus": stage_id in PM_STAGES,
                "file": f".claude/stages/{stage_id}.yaml",
                "message": f"skill '{ref}' not declared in dependencies.yaml or local skills",
            })
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Lincoln prompt drift")
    parser.add_argument("--strict", action="store_true", help="Fail if any PM-stage drift is found")
    parser.add_argument("--focus", choices=["all", "pm"], default="all", help="Focus on PM stages only")
    args = parser.parse_args()

    agents = collect_agents()
    stages = collect_stages()
    workflows = collect_workflows()
    skills = collect_skills()
    declared = collect_dependencies()
    local_skills = collect_local_skill_names()

    findings: list[dict[str, Any]] = []
    findings.extend(check_r1_extends_resolve(agents))
    findings.extend(check_r2_action_in_stage_skills(workflows, stages))
    findings.extend(check_r3_workflow_artifacts_match_stage(workflows, stages))
    findings.extend(check_r4_skill_outputs_match_stage(workflows, stages, skills))
    findings.extend(check_r5_agent_paths_in_stage_artifacts(agents, stages))
    findings.extend(check_r6_skill_dependencies_declared(stages, declared, local_skills))

    # Deduplicate by (rule, file, message).
    seen = set()
    unique_findings = []
    for f in findings:
        key = (f["rule"], f["file"], f["message"])
        if key not in seen:
            seen.add(key)
            unique_findings.append(f)
    findings = unique_findings

    if args.focus == "pm":
        findings = [f for f in findings if f.get("stage_focus")]

    errors = [f for f in findings if f["severity"] == "error"]
    warnings = [f for f in findings if f["severity"] == "warning"]

    for f in findings:
        prefix = "ERROR" if f["severity"] == "error" else "WARN"
        focus = " [PM]" if f.get("stage_focus") else ""
        print(f"{prefix}{focus} {f['rule']} {f['file']}: {f['message']}")

    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")

    if args.strict:
        return 1 if errors else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
