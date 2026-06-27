#!/usr/bin/env bash
set -euo pipefail

# On-session-start hook for Lincoln workflow.
# Loads and prints the current stage context so the Agent sees it immediately.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ -x "$ROOT/.venv/bin/python3" ]; then
    PYTHON="$ROOT/.venv/bin/python3"
elif [ -x "$ROOT/venv/bin/python3" ]; then
    PYTHON="$ROOT/venv/bin/python3"
else
    PYTHON="python3"
fi

STATE_FILE="${LINCOLN_STATE_FILE:-$ROOT/.claude/workflow-state.yaml}"

if [[ ! -f "$STATE_FILE" ]]; then
    exit 0
fi

# Read current stage
CURRENT_STAGE=$("$PYTHON" - "$STATE_FILE" <<'PY'
import sys
import yaml
path = sys.argv[1]
state = yaml.safe_load(open(path, encoding="utf-8"))
print(state.get("current_run", {}).get("current_stage") or "not_started")
PY
)

echo ""
echo "=== Lincoln Stage Context ==="
echo "Current stage: $CURRENT_STAGE"
echo ""

if [[ "$CURRENT_STAGE" != "not_started" ]]; then
    "$PYTHON" "$ROOT/scripts/stage_loader.py" \
        --stage "$CURRENT_STAGE" \
        --action load \
        --state-file "$STATE_FILE" \
        2>/dev/null || echo "[Could not load stage context for $CURRENT_STAGE]"
fi

echo "=== End Stage Context ==="
echo ""

exit 0
