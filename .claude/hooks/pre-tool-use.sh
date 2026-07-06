#!/usr/bin/env bash
set -euo pipefail

# PreToolUse hook for Lincoln workflow.
# Blocks side-effect tools when the current stage has not passed entry checks
# or is paused/waiting_for_human/validation_failed.
#
# Usage (manual):
#   .claude/hooks/pre-tool-use.sh "Write" '{"file_path": "foo.md"}'
#
# Expected arguments:
#   $1: tool name (e.g. Bash, Write, Edit, mcp__pencil__batch_design)
#   $2: JSON-encoded tool arguments

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ -x "$ROOT/.venv/bin/python3" ]; then
    PYTHON="$ROOT/.venv/bin/python3"
elif [ -x "$ROOT/venv/bin/python3" ]; then
    PYTHON="$ROOT/venv/bin/python3"
else
    PYTHON="python3"
fi

TOOL_NAME="${1:-}"
TOOL_ARGS="${2:-}"
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

# If state file does not exist, allow everything (not a Lincoln project or not initialized)
if [[ ! -f "$STATE_FILE" ]]; then
    exit 0
fi

# Read current stage and status using Python for reliable YAML parsing
read_state() {
    "$PYTHON" - "$STATE_FILE" <<'PY'
import sys
import yaml
path = sys.argv[1]
state = yaml.safe_load(open(path, encoding="utf-8"))
current = state.get("current_run", {}).get("current_stage") or "not_started"
# New schema: derive status from the latest node for the current stage; legacy schema: from stages map.
nodes = state.get("nodes", [])
matching = [n for n in nodes if n.get("stage_id") == current]
if matching:
    stage_state = matching[-1]
elif "stages" in state and current in state["stages"]:
    stage_state = state["stages"][current]
else:
    stage_state = {}
status = stage_state.get("status") or state.get("current_run", {}).get("status") or "not_started"
print(current)
print(status)
PY
}

STATE_OUTPUT=$(read_state)
CURRENT_STAGE=$(echo "$STATE_OUTPUT" | sed -n '1p')
STAGE_STATUS=$(echo "$STATE_OUTPUT" | sed -n '2p')
PROCESS_SLUG=$("$PYTHON" - "$ROOT" "$STATE_FILE" <<'PY'
import sys, yaml
from pathlib import Path
root = Path(sys.argv[1])
state_file = Path(sys.argv[2])
sys.path.insert(0, str(root))
from scripts.lincoln_paths import get_process_slug
state = yaml.safe_load(open(state_file, encoding="utf-8"))
print(get_process_slug(state, state_file))
PY
)

TARGET_PATH=$("$PYTHON" - "$TOOL_ARGS" <<'PY'
import json, sys
try:
    data = json.loads(sys.argv[1] or "{}")
except Exception:
    data = {}
print(data.get("file_path") or data.get("path") or "")
PY
)

# Task-tool guard: prevent TaskCreate/TaskUpdate from being used as
# placeholders for user messages in dialogue stages, and cap consecutive
# task-tool calls everywhere else.  This is invoked for every tool so it can
# reset the burst counter on non-task actions.
"$PYTHON" "$ROOT/scripts/task_tool_guard.py" \
    --state-file "$STATE_FILE" \
    --tool-name "$TOOL_NAME" \
    --tool-args "$TOOL_ARGS"

# Define side-effect tools
SIDE_EFFECT_TOOLS=(
    "Bash"
    "Edit"
    "Write"
    "NotebookEdit"
    "mcp__pencil__batch_design"
    "mcp__pencil__export_nodes"
    "mcp__pencil__export_html"
    "mcp__plugin_ecc_github__create_issue"
    "mcp__plugin_ecc_github__create_pull_request"
    "mcp__plugin_ecc_github__merge_pull_request"
)

is_side_effect() {
    local tool="$1"
    for t in "${SIDE_EFFECT_TOOLS[@]}"; do
        if [[ "$tool" == "$t" ]]; then
            return 0
        fi
    done
    return 1
}

is_plain_file_tool() {
    case "$1" in
        Read|Write|Edit|NotebookEdit)
            return 0
            ;;
    esac
    return 1
}

if [[ -n "$TARGET_PATH" ]]; then
    NORMALIZED_TARGET="${TARGET_PATH#$ROOT/}"

    if [[ "$NORMALIZED_TARGET" == *.pen ]] && is_plain_file_tool "$TOOL_NAME"; then
        echo "BLOCKED: .pen files must be handled through Pencil tools, not $TOOL_NAME." >&2
        exit 1
    fi

    if [[ "$NORMALIZED_TARGET" == "$PROCESS_SLUG/workflow-stage.yaml" ]] && is_side_effect "$TOOL_NAME"; then
        echo "BLOCKED: workflow state must be updated through stage_loader, not $TOOL_NAME." >&2
        exit 1
    fi

    if [[ "$NORMALIZED_TARGET" == "$PROCESS_SLUG/recordings/"* ]] && is_side_effect "$TOOL_NAME"; then
        echo "BLOCKED: recordings are read-only process inputs." >&2
        exit 1
    fi

    if is_side_effect "$TOOL_NAME"; then
        if [[ -n "$PROCESS_SLUG" ]]; then
            case "$NORMALIZED_TARGET" in
                recordings/*|*/recordings/*|interviews/*|*/interviews/*|requirements/*|*/requirements/*|designs/*|*/designs/*|openspec/changes/*|*/openspec/changes/*|docs/research/*|*/docs/research/*)
                    if [[ "$NORMALIZED_TARGET" != "$PROCESS_SLUG/"* ]]; then
                        echo "BLOCKED: process artifacts must be written under '$PROCESS_SLUG/'." >&2
                        exit 1
                    fi
                    ;;
            esac
        else
            case "$NORMALIZED_TARGET" in
                recordings/*|*/recordings/*|interviews/*|*/interviews/*|requirements/*|*/requirements/*|designs/*|*/designs/*|openspec/changes/*|*/openspec/changes/*|docs/research/*|*/docs/research/*)
                    echo "BLOCKED: process artifacts must be written under an initialized <process_slug>/." >&2
                    exit 1
                    ;;
            esac
        fi
    fi
fi

# Block side-effect tools when entry checks have not passed
if [[ "$STAGE_STATUS" == "not_started" || "$STAGE_STATUS" == "entry_validating" ]]; then
    if is_side_effect "$TOOL_NAME"; then
        echo "BLOCKED: Entry checks for stage '$CURRENT_STAGE' have not passed yet." >&2
        echo "Run: python scripts/stage_loader.py --stage $CURRENT_STAGE --action validate-entry" >&2
        exit 1
    fi
fi

# When paused/waiting_for_human/validation_failed, only allow read-only tools
if [[ "$STAGE_STATUS" == "paused" || "$STAGE_STATUS" == "waiting_for_human" || "$STAGE_STATUS" == "validation_failed" ]]; then
    if [[ "$TOOL_NAME" != "Read" && "$TOOL_NAME" != "Grep" && "$TOOL_NAME" != "Glob" ]]; then
        echo "BLOCKED: Stage '$CURRENT_STAGE' is $STAGE_STATUS. Only Read/Grep/Glob allowed." >&2
        echo "To resume: run the stage's skill command or call workflow-continue." >&2
        exit 1
    fi
fi

# Exit gate check: block side-effect tools that would advance to the next stage
# if the current stage's exit gate has not been approved.
if is_side_effect "$TOOL_NAME"; then
    GATE_STATUS=$("$PYTHON" "$ROOT/scripts/stage_loader.py" \
        --stage "$CURRENT_STAGE" \
        --action validate-exit \
        2>/dev/null | grep -c "^PASS:" || echo "0")
    # For now, only warn rather than block to avoid breaking legitimate edits.
    if [[ "$GATE_STATUS" == "0" && "$TOOL_NAME" != "Read" ]]; then
        echo "[Lincoln] Warning: exit gate for '$CURRENT_STAGE' is not yet approved." >&2
        echo "[Lincoln] Run 'python scripts/stage_loader.py --stage $CURRENT_STAGE --action validate-exit' to check." >&2
    fi
fi

exit 0
