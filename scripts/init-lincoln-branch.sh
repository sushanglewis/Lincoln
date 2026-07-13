#!/usr/bin/env bash
set -euo pipefail

# Initialize a Lincoln issue work package on the current feature branch.
# The work package is scoped to the issue and lives on the feature branch only.
#
# Usage:
#   scripts/init-lincoln-branch.sh --issue-number <number> [--session-id <id>] [--design-id <id>] [--process-slug <slug>] [--push] [--no-commit] [--auto]
#
# Legacy usage (non-issue-driven):
#   scripts/init-lincoln-branch.sh <session-id> <design-id> [--process-slug <slug>] [--push]
#
# Example:
#   scripts/init-lincoln-branch.sh --issue-number 21 --session-id 2026-07-08-stakeholder --design-id checkout-redesign --push
#
# Flags:
#   --no-commit    Create the issue package and workflow-stage.yaml but do not git-add/commit.
#   --auto         Non-interactive mode used by hooks; skips prompts and tolerates a dirty working tree.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

ISSUE_NUMBER=""
SESSION_ID=""
DESIGN_ID=""
PUSH=""
PROCESS_SLUG=""
NO_COMMIT=""
AUTO=""

# Detect legacy positional invocation
if [[ "${1:-}" != --* && $# -ge 2 ]]; then
    SESSION_ID="${1:-}"
    DESIGN_ID="${2:-}"
    shift 2
fi

while [[ $# -gt 0 ]]; do
    case "$1" in
        --issue-number)
            ISSUE_NUMBER="${2:-}"
            if [[ -z "$ISSUE_NUMBER" ]]; then
                echo "ERROR: --issue-number requires a value"
                exit 1
            fi
            shift 2
            ;;
        --session-id)
            SESSION_ID="${2:-}"
            if [[ -z "$SESSION_ID" ]]; then
                echo "ERROR: --session-id requires a value"
                exit 1
            fi
            shift 2
            ;;
        --design-id)
            DESIGN_ID="${2:-}"
            if [[ -z "$DESIGN_ID" ]]; then
                echo "ERROR: --design-id requires a value"
                exit 1
            fi
            shift 2
            ;;
        --push)
            PUSH="--push"
            shift
            ;;
        --no-commit)
            NO_COMMIT="1"
            shift
            ;;
        --auto)
            AUTO="1"
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
            echo "Usage: $(basename "$0") --issue-number <number> [--session-id <id>] [--design-id <id>] [--process-slug <slug>] [--push] [--no-commit] [--auto]"
            exit 1
            ;;
    esac
done

# Validate issue number is numeric
if [[ -n "$ISSUE_NUMBER" && ! "$ISSUE_NUMBER" =~ ^[0-9]+$ ]]; then
    echo "ERROR: --issue-number must be a positive integer: $ISSUE_NUMBER"
    exit 1
fi

# Require issue number for issue-driven initialization
if [[ -z "$ISSUE_NUMBER" && ( -z "$SESSION_ID" || -z "$DESIGN_ID" ) ]]; then
    echo "Usage: $(basename "$0") --issue-number <number> [--session-id <id>] [--design-id <id>] [--process-slug <slug>] [--push] [--no-commit] [--auto]"
    exit 1
fi

# Derive defaults for session/design from issue number
if [[ -n "$ISSUE_NUMBER" ]]; then
    TODAY="$(date -u +%Y-%m-%d)"
    SESSION_ID="${SESSION_ID:-$TODAY-issue-$ISSUE_NUMBER}"
    DESIGN_ID="${DESIGN_ID:-issue-$ISSUE_NUMBER}"
fi

# Validate design_id (kebab-case)
if ! [[ "$DESIGN_ID" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
    echo "ERROR: design_id must be kebab-case lowercase: $DESIGN_ID"
    exit 1
fi

# Validate session_id pattern (YYYY-MM-DD-descriptive-name)
if ! [[ "$SESSION_ID" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9-]+$ ]]; then
    echo "ERROR: session_id should match YYYY-MM-DD-descriptive-name: $SESSION_ID"
    exit 1
fi

RUN_ID="$(date -u +%Y%m%d%H%M%S)-$(openssl rand -hex 4 2>/dev/null || echo $$)"

if [[ -z "$PROCESS_SLUG" ]]; then
    if [[ -n "$ISSUE_NUMBER" ]]; then
        PROCESS_SLUG="issue-$ISSUE_NUMBER"
    elif [[ -n "${LINCOLN_PROCESS_SLUG:-}" ]]; then
        PROCESS_SLUG="$LINCOLN_PROCESS_SLUG"
    elif [[ -n "${CONDUCTOR_WORKSPACE_NAME:-}" ]]; then
        PROCESS_SLUG="$CONDUCTOR_WORKSPACE_NAME"
    else
        PROCESS_SLUG="${SESSION_ID}-${DESIGN_ID}"
    fi
fi

if ! [[ "$PROCESS_SLUG" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
    echo "ERROR: process_slug must be kebab-case lowercase: $PROCESS_SLUG"
    exit 1
fi

# Determine current branch / create feature branch if on main
CURRENT_BRANCH="$(git branch --show-current 2>/dev/null || true)"
if [[ -z "$CURRENT_BRANCH" ]]; then
    echo "ERROR: not on a git branch"
    exit 1
fi

if [[ "$CURRENT_BRANCH" == "main" ]]; then
    if [[ -z "$ISSUE_NUMBER" ]]; then
        echo "ERROR: must provide --issue-number to create a feature branch from main"
        exit 1
    fi
    BRANCH_NAME="issue-$ISSUE_NUMBER"
    echo "==> Creating issue branch: $BRANCH_NAME"
    git checkout -b "$BRANCH_NAME"
    CURRENT_BRANCH="$BRANCH_NAME"
elif [[ -n "$ISSUE_NUMBER" && "$CURRENT_BRANCH" != "issue-$ISSUE_NUMBER" && "$CURRENT_BRANCH" != issue-$ISSUE_NUMBER-* ]]; then
    echo "WARNING: current branch '$CURRENT_BRANCH' does not match the 'issue-$ISSUE_NUMBER' naming convention"
    echo "         (see README.md 分支级工作流与阶段状态: issue ↔ branch ↔ PR must correspond end-to-end)."
    echo "         Continuing anyway; ensure this is the intended feature branch."
fi

# Ensure working tree is clean before initializing package (skip in --auto mode)
if [[ -z "$AUTO" ]] && { ! git diff --quiet || ! git diff --cached --quiet; }; then
    echo "ERROR: working tree or index is not clean. Commit or stash changes first."
    exit 1
fi

BRANCH_NAME="$CURRENT_BRANCH"
PROCESS_ROOT="$PROCESS_SLUG"
TEMPLATE_ROOT="$ROOT/.claude/templates/issue-package"

# Create branch-scoped process package directories from template.
echo "==> Creating Lincoln issue work package: $PROCESS_ROOT/"
mkdir -p "$PROCESS_ROOT"

# Copy template tree, preserving directory structure
cp -R "$TEMPLATE_ROOT/"* "$PROCESS_ROOT/"

# Initialize workflow-stage.yaml for this issue
python3 - "$ISSUE_NUMBER" "$SESSION_ID" "$DESIGN_ID" "$BRANCH_NAME" "$RUN_ID" "$ROOT" "$PROCESS_SLUG" <<'PY'
import sys
from pathlib import Path
import yaml

issue_number, session_id, design_id, branch_name, run_id, root_path, process_slug = sys.argv[1:8]
root = Path(root_path)
state_path = root / process_slug / "workflow-stage.yaml"

template_path = root / ".claude" / "templates" / "issue-package" / "workflow-stage.yaml"
state = yaml.safe_load(template_path.read_text(encoding="utf-8"))
state["current_run"]["run_id"] = run_id
state["current_run"]["branch"] = branch_name
state["current_run"]["started_at"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
state["current_run"]["last_updated_at"] = state["current_run"]["started_at"]
state["current_run"]["current_stage"] = "ingest"
state["current_run"]["status"] = "in_progress"
state["current_run"]["issue_number"] = issue_number
state["current_run"]["variables"]["session_id"] = session_id
state["current_run"]["variables"]["design_id"] = design_id
state["current_run"]["variables"]["issue_number"] = issue_number
state["current_run"]["variables"]["process_slug"] = process_slug
state["recovery"]["can_resume_from"] = "ingest"

state_path.write_text(yaml.dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
print(f"Initialized workflow-stage.yaml for issue #{issue_number} on branch {branch_name}")
PY

# Add gitkeep files for empty directories to ensure they are tracked
for dir in "$PROCESS_ROOT/designs/$DESIGN_ID" "$PROCESS_ROOT/docs/research" "$PROCESS_ROOT/handoffs" "$PROCESS_ROOT/interviews/$SESSION_ID" "$PROCESS_ROOT/openspec/changes" "$PROCESS_ROOT/openspec/specs" "$PROCESS_ROOT/recordings" "$PROCESS_ROOT/requirements/$SESSION_ID" ".github/lincoln-sync-queue"; do
    mkdir -p "$dir"
    touch "$dir/.gitkeep"
done

if [[ -n "$NO_COMMIT" ]]; then
    echo "==> Skipping git commit (--no-commit requested)"
else
    # Stage and commit initial state
    echo "==> Committing initial issue work package"
    git add .
    git commit -m "chore: initialize Lincoln issue work package for #$ISSUE_NUMBER

- branch: $BRANCH_NAME
- process_slug: $PROCESS_SLUG
- session_id: $SESSION_ID
- design_id: $DESIGN_ID
- run_id: $RUN_ID

Issue work package is branch-scoped and will not be merged to main."
fi

if [[ "$PUSH" == "--push" ]]; then
    echo "==> Pushing branch to remote"
    git push -u origin "$BRANCH_NAME"
fi

echo ""
echo "Lincoln issue work package created for issue #$ISSUE_NUMBER"
echo "Branch: $BRANCH_NAME"
echo "Process package: $PROCESS_ROOT/"
echo "Next step: place the recording in $PROCESS_ROOT/recordings/ and say:"
echo "  '处理一下这个访谈录音 $PROCESS_ROOT/recordings/<recording-file>'"
