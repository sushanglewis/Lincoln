#!/usr/bin/env bash
set -euo pipefail

# PostToolUse hook for Lincoln workflow.
# Tracks artifacts produced by side-effect tools in the workflow state file.
#
# Usage (manual):
#   .claude/hooks/post-tool-use.sh "Write" '{"file_path": "foo.md"}' 0
#
# Expected arguments:
#   $1: tool name
#   $2: JSON-encoded tool arguments
#   $3: tool exit code

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
EXIT_CODE="${3:-0}"
STATE_FILE="${LINCOLN_STATE_FILE:-$ROOT/.claude/workflow-state.yaml}"

# Only track successful side-effect tool uses
if [[ "$EXIT_CODE" != "0" ]]; then
    exit 0
fi

if [[ ! -f "$STATE_FILE" ]]; then
    exit 0
fi

SIDE_EFFECT_TOOLS=(
    "Bash"
    "Edit"
    "Write"
    "mcp__pencil__batch_design"
    "mcp__pencil__export_nodes"
    "mcp__pencil__export_html"
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

if ! is_side_effect "$TOOL_NAME"; then
    exit 0
fi

"$PYTHON" "$ROOT/scripts/track-artifacts.py" \
    --state-file "$STATE_FILE" \
    --tool "$TOOL_NAME" \
    --args "$TOOL_ARGS" \
    --project-root "$ROOT" \
    2>/dev/null || true

exit 0
