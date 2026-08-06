#!/usr/bin/env bash
set -euo pipefail

# on-pr-event.sh
# Helper invoked by post-tool-use.sh or Stop hook when a PR/branch sync event is detected.
# Updates <process_slug>/workflow-stage.yaml with append-only node record.
#
# Usage:
#   .claude/hooks/on-pr-event.sh <event> [<node-id>] [<status>]

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

if [ -x "$FRAMEWORK_ROOT/.venv/bin/python3" ]; then
    PYTHON="$FRAMEWORK_ROOT/.venv/bin/python3"
elif [ -x "$FRAMEWORK_ROOT/venv/bin/python3" ]; then
    PYTHON="$FRAMEWORK_ROOT/venv/bin/python3"
elif [ -x "$HOME/.lincoln/venv/bin/python3" ]; then
    PYTHON="$HOME/.lincoln/venv/bin/python3"
else
    PYTHON="python3"
fi

EVENT="${1:-}"
NODE_ID="${2:-implement}"
STATUS="${3:-pr_submitted}"

if [[ -z "$EVENT" ]]; then
    exit 0
fi

"$PYTHON" "$FRAMEWORK_ROOT/scripts/stage_loader.py" \
    --action append-node \
    --node-id "$NODE_ID" \
    --status "$STATUS" \
    2>/dev/null || true

exit 0
