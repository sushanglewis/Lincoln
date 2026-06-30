#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"

echo "==> Validate skill-dependencies.yaml"
"$PYTHON" -c "import yaml; yaml.safe_load(open('.claude/skill-dependencies.yaml'))"

echo "==> Check declared skills and CLIs"
"$PYTHON" - "$ROOT" <<'PY'
import sys
import shutil
from pathlib import Path
import yaml

root = Path(sys.argv[1])
manifest = yaml.safe_load((root / ".claude" / "skill-dependencies.yaml").read_text(encoding="utf-8"))

skill_root = Path.home() / ".claude" / "skills"
errors = []
warnings = []

for name, cfg in manifest.get("skills", {}).items():
    typ = cfg.get("type", "skill")
    is_required = cfg.get("required", True)
    if typ == "cli":
        binary = cfg.get("binary", name)
        if not shutil.which(binary):
            msg = f"CLI missing: {binary} (skill: {name})"
            if is_required:
                errors.append(msg)
            else:
                warnings.append(msg)
    else:
        path = cfg.get("path")
        if path:
            expected = root / path / "SKILL.md"
        else:
            expected = skill_root / name / "SKILL.md"
        if not expected.exists():
            msg = f"Skill missing: {name} (expected {expected})"
            if is_required:
                errors.append(msg)
            else:
                warnings.append(msg)

if warnings:
    print("Optional dependencies missing (warnings only):")
    for w in warnings:
        print(f"  - {w}")

if errors:
    print("Required dependencies missing:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)

print("All declared skills/CLIs are present.")
PY

echo "==> All skill dependencies satisfied"
