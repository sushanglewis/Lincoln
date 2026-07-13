#!/usr/bin/env bash
set -euo pipefail

# Sync external agent definitions declared by .claude/agents/external/*.manifest.yaml.
# Usage:
#   scripts/sync-external-agents.sh
#   scripts/sync-external-agents.sh --dry-run

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
fi

AGENTS_DIR="$ROOT/.claude/agents/external"
mkdir -p "$AGENTS_DIR"

"$ROOT/.venv/bin/python3" - "$AGENTS_DIR" "$DRY_RUN" <<'PY'
import sys
from pathlib import Path
import re
import shutil
import subprocess
import yaml

agents_dir = Path(sys.argv[1])
dry_run = sys.argv[2].lower() == "true"

KNOWN_FIELDS = {"name", "description", "extends", "model", "tools", "disallowed_tools"}
PERMISSIVE_LICENSES = {"mit", "apache-2.0", "bsd-3-clause", "bsd-2-clause", "isc"}


def slugify(value: str) -> str:
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(r"[-\s]+", "-", value)


def normalize_frontmatter(text: str, prefix: str, source: str, ref: str, license_key: str, original_name: str) -> str:
    if not text.startswith("---"):
        return text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return text
    try:
        front = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return text

    if not isinstance(front, dict):
        front = {}

    normalized = {k: v for k, v in front.items() if k in KNOWN_FIELDS}

    # Prefix the agent name to avoid collisions.
    normalized["name"] = f"{prefix}-{slugify(original_name)}"
    normalized["original_name"] = original_name
    normalized["source"] = source
    normalized["ref"] = ref
    normalized["license"] = license_key

    # Map camelCase / legacy fields.
    if "disallowedTools" in front and "disallowed_tools" not in normalized:
        normalized["disallowed_tools"] = front["disallowedTools"]

    # Resolve inherited models.
    model = normalized.get("model")
    if isinstance(model, str):
        model = model.lower().strip()
        if model in {"inherit", "default", "auto"}:
            normalized["model"] = "sonnet"
    if "model" not in normalized:
        normalized["model"] = "sonnet"

    # Remove extends from imported standalone agents; Lincoln wrappers handle composition.
    normalized.pop("extends", None)

    normalized_yaml = yaml.safe_dump(normalized, sort_keys=False, allow_unicode=True)
    attribution = (
        f"<!-- Imported from {source} @ {ref}, licensed under {license_key}. "
        f"Original name: {original_name}. -->"
    )
    body = parts[2].lstrip("\n")
    return f"---\n{normalized_yaml}---\n\n{attribution}\n\n{body}"


def parse_manifest(manifest_path: Path) -> dict | None:
    docs = list(yaml.safe_load_all(manifest_path.read_text(encoding="utf-8")))
    data = docs[0] if docs else None
    if not isinstance(data, dict):
        print(f"Skipping {manifest_path.name}: invalid manifest")
        return None
    return data


def agent_source_path(agents_subdir: str, imported: str) -> str:
    if imported.endswith(".md"):
        return f"{agents_subdir}/{imported}"
    return f"{agents_subdir}/{imported}.md"


def agent_basename(imported: str) -> str:
    name = imported[:-3] if imported.endswith(".md") else imported
    return Path(name).name


notices = []
notices.append("# 外部 Agent 来源声明\n")
notices.append("本文件由 `scripts/sync-external-agents.sh` 自动生成，请勿手动修改。\n")
notices.append("| Lincoln 文件名 | 原始名称 | 来源仓库 | 引用 | 许可证 |")
notices.append("|---|---|---|---|---|")

for manifest_path in sorted(agents_dir.glob("*.manifest.yaml")):
    data = parse_manifest(manifest_path)
    if data is None:
        continue

    framework = manifest_path.stem.replace(".manifest", "")
    source = data.get("source", "")
    ref = data.get("ref", "main") or "main"
    license_key = (data.get("license", "") or "").lower()
    prefix = data.get("prefix", framework)
    agents_subdir = data.get("paths", {}).get("agents", ".claude/agents")
    imported_agents = data.get("imported_agents", [])

    if not source:
        print(f"Skipping {manifest_path.name}: no source declared")
        continue
    if license_key not in PERMISSIVE_LICENSES:
        print(f"Skipping {manifest_path.name}: license '{license_key}' is not permissive")
        continue
    if not imported_agents:
        print(f"Skipping {manifest_path.name}: no imported_agents")
        continue

    target_dir = agents_dir / framework / "agents"
    print(f"Syncing {framework} from {source} @ {ref}")

    if dry_run:
        print(f"  [dry-run] Would clone/sparse-checkout into {agents_dir / framework}")
        for imported in imported_agents:
            print(f"  [dry-run] Would import {imported} as {prefix}-{slugify(agent_basename(imported))}")
        continue

    if target_dir.exists():
        shutil.rmtree(target_dir.parent)
    target_dir.mkdir(parents=True, exist_ok=True)

    repo_dir = agents_dir / framework / ".repo"
    if repo_dir.exists():
        shutil.rmtree(repo_dir)
    repo_dir.mkdir(parents=True, exist_ok=True)

    sparse_paths = [agent_source_path(agents_subdir, imp) for imp in imported_agents]

    try:
        subprocess.run(
            [
                "git", "clone", "--depth", "1", "--branch", ref,
                "--filter=blob:none", "--sparse", source, str(repo_dir),
            ],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "sparse-checkout", "set", "--no-cone", *sparse_paths],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        print(f"  Failed to sync {framework}: {exc}")
        if exc.stderr:
            print(exc.stderr.decode("utf-8", errors="replace"))
        continue

    # Copy and normalize each imported agent.
    for imported in imported_agents:
        src_rel = agent_source_path(agents_subdir, imported)
        src_file = repo_dir / src_rel
        original_name = agent_basename(imported)
        normalized_name = f"{prefix}-{slugify(original_name)}"
        dest_file = target_dir / f"{normalized_name}.md"

        if not src_file.exists():
            print(f"  Warning: expected agent file not found: {src_rel}")
            continue

        raw_text = src_file.read_text(encoding="utf-8")
        normalized_text = normalize_frontmatter(
            raw_text, prefix, source, ref, license_key, original_name
        )
        dest_file.write_text(normalized_text, encoding="utf-8")
        notices.append(
            f"| {normalized_name}.md | {original_name} | {source} | {ref} | {license_key.upper()} |"
        )
        print(f"  Imported {normalized_name}")

    # Clean up the temporary clone.
    shutil.rmtree(repo_dir)

# Write NOTICES.md
notices_path = agents_dir / "NOTICES.md"
notices_path.write_text("\n".join(notices) + "\n", encoding="utf-8")
print(f"Wrote {notices_path}")

print("External agent sync complete.")
PY
