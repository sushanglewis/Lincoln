#!/usr/bin/env bash
set -euo pipefail

# On-stop hook for Lincoln workflow.
# Updates last_updated_at in the workflow stage file when a session ends.
#
# The operational state file is branch-scoped: <process_slug>/workflow-stage.yaml
# (falls back to legacy .claude/workflow-state.yaml if present).

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

# Update last_updated_at through the canonical state mutation layer.
"$PYTHON" "$FRAMEWORK_ROOT/scripts/stage_loader.py" \
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
    "$PYTHON" "$FRAMEWORK_ROOT/scripts/stage_loader.py" \
        --state-file "$STATE_FILE" \
        --stage "$CURRENT_STAGE" \
        --action handoff-report \
        >/dev/null 2>&1 || true
fi

exit 0
