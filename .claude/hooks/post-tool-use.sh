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
LOCAL_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PROJECT_ROOT="$(pwd)"

FRAMEWORK_ROOT="${CLAUDE_PLUGIN_ROOT:-${LINCOLN_HOME:-}}"
if [[ -z "$FRAMEWORK_ROOT" ]]; then
  # If this hook file lives inside a vendored project framework, prefer that.
  if [[ "$SCRIPT_DIR" == "$LOCAL_ROOT/.claude/hooks"* && -d "$LOCAL_ROOT/.claude/stages" ]]; then
    FRAMEWORK_ROOT="$LOCAL_ROOT"
  elif [[ -d "$HOME/.lincoln/current" ]]; then
    FRAMEWORK_ROOT="$HOME/.lincoln/current"
  else
    FRAMEWORK_ROOT="$LOCAL_ROOT"
  fi
fi

if [[ "$FRAMEWORK_ROOT" != "$LOCAL_ROOT" ]]; then
  MARKER_FOUND="false"
  SEARCH_DIR="$PROJECT_ROOT"
  while [[ "$SEARCH_DIR" != "/" ]]; do
    if [[ -f "$SEARCH_DIR/.lincoln.yaml" || -f "$SEARCH_DIR/.claude/workflow-state.yaml" ]]; then
      MARKER_FOUND="true"
      break
    fi
    SEARCH_DIR="$(dirname "$SEARCH_DIR")"
  done
  if [[ "$MARKER_FOUND" != "true" && -z "${LINCOLN_ALWAYS_ON:-}" ]]; then
    echo "Lincoln inactive: no .lincoln.yaml in $PROJECT_ROOT"
    exit 0
  fi
fi

ROOT="$PROJECT_ROOT"

mkdir -p "$ROOT/.context"

if [ -x "$FRAMEWORK_ROOT/.venv/bin/python3" ]; then
    PYTHON="$FRAMEWORK_ROOT/.venv/bin/python3"
elif [ -x "$FRAMEWORK_ROOT/venv/bin/python3" ]; then
    PYTHON="$FRAMEWORK_ROOT/venv/bin/python3"
elif [ -x "$HOME/.lincoln/venv/bin/python3" ]; then
    PYTHON="$HOME/.lincoln/venv/bin/python3"
else
    PYTHON="python3"
fi

TOOL_NAME="${1:-}"
TOOL_ARGS="${2:-}"
EXIT_CODE="${3:-0}"
STATE_FILE=$("$PYTHON" - "$FRAMEWORK_ROOT" "$ROOT" "${LINCOLN_STATE_FILE:-}" <<'PY'
import sys
from pathlib import Path
framework_root = Path(sys.argv[1])
project_root = Path(sys.argv[2])
provided = sys.argv[3]
sys.path.insert(0, str(framework_root))
from scripts.lincoln_paths import resolve_state_path
path = Path(provided) if provided else None
print(resolve_state_path(path, project_root))
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
        LINCOLN_SKIP_TRACE=1 "$PYTHON" "$FRAMEWORK_ROOT/scripts/lincoln_trace.py" \
            --state-file "$STATE_FILE" \
            --tool "$TOOL_NAME" \
            --args-json "$TOOL_ARGS" \
            --exit-code "$EXIT_CODE" \
            2>>"$ROOT/.context/lc-trace-errors.log" || true
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
    "$PYTHON" "$FRAMEWORK_ROOT/scripts/track-artifacts.py" \
        --state-file "$STATE_FILE" \
        --tool "$TOOL_NAME" \
        --args "$TOOL_ARGS" \
        --project-root "$ROOT" \
        2>/dev/null || true
fi

# Determine the current stage so PR lifecycle nodes are attached to the stage
# that actually produced the PR, instead of hardcoding "implement".
CURRENT_STAGE=$("$PYTHON" - "$STATE_FILE" <<'PY' 2>/dev/null
import sys, yaml
state = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
print(state.get("current_run", {}).get("current_stage") or "implement")
PY
) || CURRENT_STAGE="implement"

# Detect PR/branch sync events, append a node record, and queue the matching
# benchmark trigger in a single mapping to avoid duplicated logic.
BENCHMARK_TRIGGER=""
EVENT_STATUS=""
if [[ "$TOOL_NAME" == "mcp__plugin_ecc_github__create_pull_request" ]]; then
    BENCHMARK_TRIGGER="pr_created"
    EVENT_STATUS="pr_submitted"
elif [[ "$TOOL_NAME" == "mcp__plugin_ecc_github__merge_pull_request" ]]; then
    BENCHMARK_TRIGGER="pr_merged"
    EVENT_STATUS="merged"
fi

if [[ -n "$BENCHMARK_TRIGGER" ]]; then
    EVENT_NODE="${CURRENT_STAGE:-implement}"
    "$PYTHON" "$FRAMEWORK_ROOT/scripts/stage_loader.py" \
        --state-file "$STATE_FILE" \
        --action append-node \
        --node-id "$EVENT_NODE" \
        --status "$EVENT_STATUS" \
        2>/dev/null || true
fi

exit 0
