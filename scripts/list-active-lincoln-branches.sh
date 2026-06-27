#!/usr/bin/env bash
set -euo pipefail

# List all active Lincoln feature branches and their current stage state.
#
# Usage:
#   scripts/list-active-lincoln-branches.sh
#
# Output:
#   BRANCH                                           CURRENT_STAGE          STATUS              WAITING_FOR
#   lincoln/2026-06-27-stakeholder-checkout-redesign clarify                waiting_for_human   pm

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

REMOTE="${1:-origin}"

echo "==> Fetching remote branches from $REMOTE"
git fetch "$REMOTE" 'lincoln/*:refs/remotes/'"$REMOTE"'/lincoln/*' 2>/dev/null || true

BRANCHES=$(git branch -r --list "$REMOTE/lincoln/*" 2>/dev/null || true)

if [[ -z "$BRANCHES" ]]; then
    echo "No active Lincoln branches found."
    exit 0
fi

printf "%-50s %-22s %-20s %-15s\n" "BRANCH" "CURRENT_STAGE" "STATUS" "WAITING_FOR"
printf "%-50s %-22s %-20s %-15s\n" "----" "-----------" "------" "-----------"

for ref in $BRANCHES; do
    # Extract branch name without remote prefix
    branch="${ref#$REMOTE/}"

    # Try to read workflow state from the remote branch
    state_yaml=$(git show "$ref:.claude/workflow-state.yaml" 2>/dev/null || true)

    if [[ -z "$state_yaml" ]]; then
        printf "%-50s %-22s %-20s %-15s\n" "$branch" "unknown" "no-state-file" ""
        continue
    fi

    # Parse state using Python (more reliable than shell YAML parsing)
    python3 - "$branch" "$state_yaml" <<'PY'
import sys
import yaml

branch, raw = sys.argv[1:3]
state = yaml.safe_load(raw)
run = state.get("current_run", {})
stage_id = run.get("current_stage") or "unknown"
status = run.get("status") or "unknown"

stage_state = state.get("stages", {}).get(stage_id, {}) if stage_id != "unknown" else {}
stage_status = stage_state.get("status") or status

waiting_for = ""
if stage_status == "waiting_for_human":
    waiting_for = "pm"
elif stage_status == "validation_failed":
    waiting_for = "agent-fix"
elif stage_status == "in_progress":
    waiting_for = "agent"
elif stage_status == "completed":
    waiting_for = "next-role"

print(f"{branch:50} {stage_id:22} {stage_status:20} {waiting_for:15}")
PY
done
