#!/usr/bin/env bash
set -euo pipefail

# PostToolUse hook for Lincoln workflow.
# Tracks artifacts produced by side-effect tools and detects PR/branch sync events.
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

# Trace logging: record (nearly) every tool invocation to the session trace.
# This runs before the early success-only exit so failures are captured too.
# Skip no-op/recursive tools and any call already flagged with LINCOLN_SKIP_TRACE=1.
if [[ "${LINCOLN_SKIP_TRACE:-}" != "1" ]]; then
    if [[ "$TOOL_NAME" != "Read" && "$TOOL_NAME" != "Grep" && "$TOOL_NAME" != "Glob" ]]; then
        LINCOLN_SKIP_TRACE=1 "$PYTHON" "$ROOT/scripts/lincoln_trace.py" \
            --state-file "$STATE_FILE" \
            --tool "$TOOL_NAME" \
            --args-json "$TOOL_ARGS" \
            --exit-code "$EXIT_CODE" \
            2>/dev/null || true
    fi
fi

# Only track successful side-effect tool uses
if [[ "$EXIT_CODE" != "0" ]]; then
    exit 0
fi

SIDE_EFFECT_TOOLS=(
    "Bash"
    "Edit"
    "Write"
    "mcp__pencil__batch_design"
    "mcp__pencil__export_nodes"
    "mcp__pencil__export_html"
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

if is_side_effect "$TOOL_NAME"; then
    "$PYTHON" "$ROOT/scripts/track-artifacts.py" \
        --state-file "$STATE_FILE" \
        --tool "$TOOL_NAME" \
        --args "$TOOL_ARGS" \
        --project-root "$ROOT" \
        2>/dev/null || true
fi

# Detect PR/branch sync events and append node record
PR_EVENT=false
EVENT_NODE=""
EVENT_STATUS=""
if [[ "$TOOL_NAME" == "mcp__plugin_ecc_github__create_pull_request" ]]; then
    PR_EVENT=true
    EVENT_NODE="implement"
    EVENT_STATUS="pr_submitted"
elif [[ "$TOOL_NAME" == "mcp__plugin_ecc_github__merge_pull_request" ]]; then
    PR_EVENT=true
    EVENT_NODE="implement"
    EVENT_STATUS="merged"
fi

if [[ "$PR_EVENT" == true ]]; then
    "$PYTHON" "$ROOT/scripts/stage_loader.py" \
        --state-file "$STATE_FILE" \
        --action append-node \
        --node-id "$EVENT_NODE" \
        --status "$EVENT_STATUS" \
        2>/dev/null || true
fi

# Trigger benchmark reports for handoff/PR lifecycle events.
BENCHMARK_TRIGGER=""
if [[ "$TOOL_NAME" == "mcp__plugin_ecc_github__create_pull_request" ]]; then
    BENCHMARK_TRIGGER="pr_created"
elif [[ "$TOOL_NAME" == "mcp__plugin_ecc_github__merge_pull_request" ]]; then
    BENCHMARK_TRIGGER="pr_merged"
elif [[ "$TOOL_NAME" == "Bash" ]]; then
    BASH_COMMAND=$(echo "$TOOL_ARGS" | "$PYTHON" -c "import sys,json; print(json.load(sys.stdin).get('command',''))" 2>/dev/null || echo "")
    if [[ "$BASH_COMMAND" == *"--action handoff-report"* ]]; then
        BENCHMARK_TRIGGER="handoff"
    fi
fi

if [[ -n "$BENCHMARK_TRIGGER" ]]; then
    BENCHMARK_ROOT="${LINCOLN_BENCHMARK_PROJECT_ROOT:-$ROOT}"
    LINCOLN_SKIP_TRACE=1 "$PYTHON" "$ROOT/scripts/lincoln_benchmark.py" \
        --state-file "$STATE_FILE" \
        --trigger "$BENCHMARK_TRIGGER" \
        --project-root "$BENCHMARK_ROOT" \
        >/dev/null 2>&1 || true
fi

exit 0
