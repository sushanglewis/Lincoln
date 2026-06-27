#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Prefer project venv if available; otherwise rely on system python3 having pytest/pyyaml.
if [ -d "$ROOT/.venv" ] && [ -x "$ROOT/.venv/bin/python3" ]; then
    PYTHON="$ROOT/.venv/bin/python3"
elif [ -d "$ROOT/venv" ] && [ -x "$ROOT/venv/bin/python3" ]; then
    PYTHON="$ROOT/venv/bin/python3"
else
    PYTHON="python3"
fi

echo "==> Validate workflow YAML"
"$PYTHON" -c "import yaml; yaml.safe_load(open('.claude/workflows/interview-to-knowledge.yaml'))"

echo "==> Validate skill YAML"
"$PYTHON" -c "import yaml; yaml.safe_load(open('.claude/skills/interview-workflow/skill.yaml'))"

echo "==> Validate Python syntax"
"$PYTHON" -m py_compile .claude/skills/interview-workflow/validators/validate.py

echo "==> Validate prompt paths in skill.yaml"
"$PYTHON" - "$ROOT" <<'PY'
import sys
import yaml
from pathlib import Path

root = Path(sys.argv[1])
skill = yaml.safe_load((root / ".claude/skills/interview-workflow/skill.yaml").read_text(encoding="utf-8"))
base = root / ".claude/skills/interview-workflow"
missing = []
for name, cmd in skill.get("commands", {}).items():
    prompt = cmd.get("prompt")
    if prompt:
        path = base / prompt
        if not path.exists():
            missing.append(f"command '{name}': {path}")
if missing:
    print("Missing prompts:")
    for m in missing:
        print(f"  - {m}")
    sys.exit(1)
print("All prompt paths resolved.")
PY

echo "==> Run pytest"
"$PYTHON" -m pytest tests/ -v

echo "==> All static checks passed"
