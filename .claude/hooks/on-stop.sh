#!/usr/bin/env bash
set -euo pipefail

# On-stop hook for Lincoln workflow.
# Updates last_updated_at in the workflow stage file when a session ends.
#
# The state file is branch-scoped: .claude/workflow-stage.yaml
# (falls back to legacy .claude/workflow-state.yaml if present).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ -x "$ROOT/.venv/bin/python3" ]; then
    PYTHON="$ROOT/.venv/bin/python3"
elif [ -x "$ROOT/venv/bin/python3" ]; then
    PYTHON="$ROOT/venv/bin/python3"
else
    PYTHON="python3"
fi

STATE_FILE=$("$PYTHON" - "$ROOT" "${LINCOLN_STATE_FILE:-}" <<'PY'
import sys
from pathlib import Path
root = Path(sys.argv[1])
provided = sys.argv[2]
sys.path.insert(0, str(root))
from scripts.lincoln_paths import resolve_state_path
path = Path(provided) if provided else None
print(resolve_state_path(path, root))
PY
)

if [[ ! -f "$STATE_FILE" ]]; then
    exit 0
fi

"$PYTHON" - "$STATE_FILE" <<'PY'
import sys
from datetime import datetime, timezone
import yaml

path = sys.argv[1]
state = yaml.safe_load(open(path, encoding="utf-8"))
state["current_run"]["last_updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
with open(path, "w", encoding="utf-8") as f:
    yaml.dump(state, f, allow_unicode=True, sort_keys=False)
PY

CURRENT_STAGE=$("$PYTHON" - "$STATE_FILE" <<'PY' 2>/dev/null
import sys, yaml
state = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
print(state.get("current_run", {}).get("current_stage") or "")
PY
) || CURRENT_STAGE=""

STAGE_STATUS=$("$PYTHON" - "$STATE_FILE" <<'PY' 2>/dev/null
import sys, yaml
state = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
stage = state.get("current_run", {}).get("current_stage")
nodes = [n for n in state.get("nodes", []) if n.get("stage_id") == stage]
if nodes:
    print(nodes[-1].get("status") or state.get("current_run", {}).get("status") or "")
else:
    print(state.get("current_run", {}).get("status") or "")
PY
) || STAGE_STATUS=""

if [[ -n "$CURRENT_STAGE" && ( "$STAGE_STATUS" == "waiting_for_human" || "$STAGE_STATUS" == "validation_failed" ) ]]; then
    "$PYTHON" "$ROOT/scripts/stage_loader.py" \
        --state-file "$STATE_FILE" \
        --stage "$CURRENT_STAGE" \
        --action handoff-report \
        >/dev/null 2>&1 || true
fi

exit 0
