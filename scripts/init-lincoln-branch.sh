#!/usr/bin/env bash
set -euo pipefail

# Initialize a new Lincoln feature branch with branch-scoped workflow state.
# Process documents live on the feature branch and are not merged to main.
#
# Usage:
#   scripts/init-lincoln-branch.sh <session-id> <design-id> [--process-slug <slug>] [--push]
#
# Example:
#   scripts/init-lincoln-branch.sh 2026-06-27-stakeholder checkout-redesign --process-slug lincoln-v1 --push

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

SESSION_ID="${1:-}"
DESIGN_ID="${2:-}"
PUSH=""
PROCESS_SLUG=""

if [[ -z "$SESSION_ID" || -z "$DESIGN_ID" ]]; then
    echo "Usage: $(basename "$0") <session-id> <design-id> [--process-slug <slug>] [--push]"
    exit 1
fi

shift 2
while [[ $# -gt 0 ]]; do
    case "$1" in
        --push)
            PUSH="--push"
            shift
            ;;
        --process-slug)
            PROCESS_SLUG="${2:-}"
            if [[ -z "$PROCESS_SLUG" ]]; then
                echo "ERROR: --process-slug requires a value"
                exit 1
            fi
            shift 2
            ;;
        *)
            echo "ERROR: unknown argument: $1"
            echo "Usage: $(basename "$0") <session-id> <design-id> [--process-slug <slug>] [--push]"
            exit 1
            ;;
    esac
done

BRANCH_NAME="lincoln/${SESSION_ID}-${DESIGN_ID}"
RUN_ID="$(date -u +%Y%m%d%H%M%S)-$(openssl rand -hex 4 2>/dev/null || echo $$)"

if [[ -z "$PROCESS_SLUG" ]]; then
    if [[ -n "${LINCOLN_PROCESS_SLUG:-}" ]]; then
        PROCESS_SLUG="$LINCOLN_PROCESS_SLUG"
    elif [[ -n "${CONDUCTOR_WORKSPACE_NAME:-}" ]]; then
        PROCESS_SLUG="$CONDUCTOR_WORKSPACE_NAME"
    elif [[ "$(basename "$(dirname "$ROOT")")" == "workspaces" ]]; then
        PROCESS_SLUG="$(basename "$ROOT")"
    elif [[ "$(basename "$(dirname "$(dirname "$ROOT")")")" == "workspaces" ]]; then
        PROCESS_SLUG="$(basename "$(dirname "$ROOT")")"
    else
        PROCESS_SLUG="${SESSION_ID}-${DESIGN_ID}"
    fi
fi

# Validate design_id (kebab-case, same as validator)
if ! [[ "$DESIGN_ID" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
    echo "ERROR: design_id must be kebab-case lowercase: $DESIGN_ID"
    exit 1
fi

if ! [[ "$PROCESS_SLUG" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
    echo "ERROR: process_slug must be kebab-case lowercase: $PROCESS_SLUG"
    exit 1
fi

# Validate session_id pattern (YYYY-MM-DD-descriptive-name)
if ! [[ "$SESSION_ID" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9-]+$ ]]; then
    echo "ERROR: session_id should match YYYY-MM-DD-descriptive-name: $SESSION_ID"
    exit 1
fi

# Ensure we are on main and it is clean
CURRENT_BRANCH="$(git branch --show-current 2>/dev/null || true)"
if [[ "$CURRENT_BRANCH" != "main" ]]; then
    echo "ERROR: must be on main to create a Lincoln branch. Current: ${CURRENT_BRANCH:-detached}"
    exit 1
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "ERROR: working tree or index is not clean. Commit or stash changes first."
    exit 1
fi

echo "==> Creating Lincoln branch: $BRANCH_NAME"
git checkout -b "$BRANCH_NAME"

PROCESS_ROOT="$PROCESS_SLUG"

# Create branch-scoped process package directories.
echo "==> Creating Lincoln process package: $PROCESS_ROOT/"
mkdir -p "$PROCESS_ROOT/designs/$DESIGN_ID"
mkdir -p "$PROCESS_ROOT/docs/research"
mkdir -p "$PROCESS_ROOT/handoffs"
mkdir -p "$PROCESS_ROOT/interviews/$SESSION_ID"
mkdir -p "$PROCESS_ROOT/openspec/changes"
mkdir -p "$PROCESS_ROOT/recordings"
mkdir -p "$PROCESS_ROOT/requirements/$SESSION_ID"
mkdir -p ".github/lincoln-sync-queue"

# Initialize workflow-stage.yaml for this branch
echo "==> Initializing $PROCESS_ROOT/workflow-stage.yaml"
python3 - "$SESSION_ID" "$DESIGN_ID" "$BRANCH_NAME" "$RUN_ID" "$ROOT" "$PROCESS_SLUG" <<'PY'
import sys
from pathlib import Path
import yaml

session_id, design_id, branch_name, run_id, root_path, process_slug = sys.argv[1:7]
root = Path(root_path)
state_path = root / process_slug / "workflow-stage.yaml"

template_path = root / ".claude" / "templates" / "issue-package" / ".claude" / "workflow-stage.yaml"
state = yaml.safe_load(template_path.read_text(encoding="utf-8"))
state["current_run"]["run_id"] = run_id
state["current_run"]["branch"] = branch_name
state["current_run"]["started_at"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
state["current_run"]["last_updated_at"] = state["current_run"]["started_at"]
state["current_run"]["current_stage"] = "ingest"
state["current_run"]["status"] = "in_progress"
state["current_run"]["variables"]["session_id"] = session_id
state["current_run"]["variables"]["design_id"] = design_id
state["current_run"]["variables"]["process_slug"] = process_slug
state["recovery"]["can_resume_from"] = "ingest"

state_path.parent.mkdir(parents=True, exist_ok=True)
state_path.write_text(yaml.dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
print(f"Initialized workflow-stage.yaml for branch {branch_name}")
PY

# Add gitkeep files for empty directories to ensure they are tracked
for dir in ".context" "$PROCESS_ROOT/designs/$DESIGN_ID" "$PROCESS_ROOT/docs/research" "$PROCESS_ROOT/handoffs" "$PROCESS_ROOT/interviews/$SESSION_ID" "$PROCESS_ROOT/openspec/changes" "$PROCESS_ROOT/recordings" "$PROCESS_ROOT/requirements/$SESSION_ID" ".github/lincoln-sync-queue"; do
    touch "$dir/.gitkeep"
done

# Stage and commit initial state
echo "==> Committing initial branch state"
git add .
git commit -m "chore: initialize Lincoln branch $BRANCH_NAME

- session_id: $SESSION_ID
- design_id: $DESIGN_ID
- process_slug: $PROCESS_SLUG
- run_id: $RUN_ID

Process documents are branch-scoped and will not be merged to main."

if [[ "$PUSH" == "--push" ]]; then
    echo "==> Pushing branch to remote"
    git push -u origin "$BRANCH_NAME"
fi

echo ""
echo "Lincoln branch created: $BRANCH_NAME"
echo "Process package: $PROCESS_ROOT/"
echo "Next step: place the recording in $PROCESS_ROOT/recordings/ and say:"
echo "  '处理一下这个访谈录音 $PROCESS_ROOT/recordings/<recording-file>'"
