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

echo "==> Validate workflow-state.yaml schema"
"$PYTHON" - "$ROOT" <<'PY'
import sys
from pathlib import Path
import yaml

root = Path(sys.argv[1])
state_file = root / ".claude" / "workflow-state.yaml"
if not state_file.exists():
    print("workflow-state.yaml not found; skipping")
    sys.exit(0)

state = yaml.safe_load(state_file.read_text(encoding="utf-8"))
required_top = ["schema_version", "workflow", "current_run", "stages", "variables", "recovery"]
missing = [k for k in required_top if k not in state]
if missing:
    print(f"Missing top-level keys: {', '.join(missing)}")
    sys.exit(1)

workflow = yaml.safe_load((root / ".claude" / "workflows" / "interview-to-knowledge.yaml").read_text(encoding="utf-8"))
expected_stages = {s["id"] for s in workflow["workflow"]["steps"]}
actual_stages = set(state.get("stages", {}).keys())
if expected_stages != actual_stages:
    print(f"Stage mismatch: expected {expected_stages}, got {actual_stages}")
    sys.exit(1)

print("workflow-state.yaml schema valid.")
PY

echo "==> Validate stage directories are complete"
"$PYTHON" - "$ROOT" <<'PY'
import sys
from pathlib import Path
import yaml

root = Path(sys.argv[1])
workflow = yaml.safe_load((root / ".claude" / "workflows" / "interview-to-knowledge.yaml").read_text(encoding="utf-8"))

missing = []
for step in workflow["workflow"]["steps"]:
    stage_dir = root / ".claude" / "stages" / step["id"]
    if not stage_dir.exists():
        missing.append(f"Missing directory: {stage_dir}")
        continue
    for file in ["AGENTS.md", "CHECKLIST.md", "SKILLS.md"]:
        if not (stage_dir / file).exists():
            missing.append(f"Missing {file} in {stage_dir}")

if missing:
    print("Incomplete stage directories:")
    for m in missing:
        print(f"  - {m}")
    sys.exit(1)
print("All stage directories complete.")
PY

echo "==> Validate hook scripts are executable"
for hook in "$ROOT/.claude/hooks/"*.sh; do
    if [ -f "$hook" ] && [ ! -x "$hook" ]; then
        echo "Hook not executable: $hook"
        exit 1
    fi
done
echo "All hooks executable."

echo "==> Validate Python syntax for new scripts"
"$PYTHON" -m py_compile scripts/stage_loader.py
"$PYTHON" -m py_compile scripts/track-artifacts.py
"$PYTHON" -m py_compile scripts/task_tool_guard.py

echo "==> Validate bash syntax for new scripts"
bash -n scripts/init-lincoln-branch.sh
bash -n scripts/list-active-lincoln-branches.sh
for hook in "$ROOT/.claude/hooks/"*.sh; do
    bash -n "$hook"
done

echo "==> Run pytest"
"$PYTHON" -m pytest tests/ -v

echo "==> All static checks passed"
