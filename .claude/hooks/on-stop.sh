#!/usr/bin/env bash
set -euo pipefail

# On-stop hook for Lincoln workflow.
# Updates last_updated_at in the workflow stage file when a session ends.
#
# The operational state file is branch-scoped: <process_slug>/workflow-stage.yaml
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

# Update last_updated_at through the canonical state mutation layer.
"$PYTHON" "$ROOT/scripts/stage_loader.py" \
    --state-file "$STATE_FILE" \
    --action update-last-updated \
    2>/dev/null || true

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

# Generate a session-stop benchmark report directly from the hook.
# lincoln_benchmark.py handles its own 5-second deduplication.
LINCOLN_SKIP_TRACE=1 "$PYTHON" "$ROOT/scripts/lincoln_benchmark.py" \
    --state-file "$STATE_FILE" \
    --trigger session_stop \
    >/dev/null 2>&1 || true

exit 0
