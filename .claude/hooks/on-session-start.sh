#!/usr/bin/env bash
set -euo pipefail

# On-session-start hook for Lincoln workflow.
# Loads stage context, checks dependencies, parses <process_slug>/workflow-stage.yaml,
# reads previous node handoff, and injects current node driving context.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ -x "$ROOT/.venv/bin/python3" ]; then
    PYTHON="$ROOT/.venv/bin/python3"
elif [ -x "$ROOT/venv/bin/python3" ]; then
    PYTHON="$ROOT/venv/bin/python3"
else
    PYTHON="python3"
fi

STATE_FILE="${LINCOLN_STATE_FILE:-}"
LEGACY_STATE_FILE="$ROOT/.claude/workflow-state.yaml"

# Runtime state captured for optional machine-readable JSON output
# (LINCOLN_SESSION_START_JSON=1). Updated at key decision points.
_LINCOLN_SETUP_COMPLETE="false"
_LINCOLN_HAS_STATE="false"
_LINCOLN_GUIDANCE_INJECTED="false"
_LINCOLN_CURRENT_STAGE="not_started"
_LINCOLN_STATUS="not_started"
_LINCOLN_WORKFLOW_TEMPLATE="unknown"
_LINCOLN_PROCESS_SLUG=""

emit_session_start_json() {
    if [[ "${LINCOLN_SESSION_START_JSON:-}" != "1" ]]; then
        return 0
    fi
    "$PYTHON" - "$_LINCOLN_SETUP_COMPLETE" "$_LINCOLN_HAS_STATE" "$_LINCOLN_GUIDANCE_INJECTED" "$_LINCOLN_CURRENT_STAGE" "$_LINCOLN_STATUS" "$_LINCOLN_WORKFLOW_TEMPLATE" "$_LINCOLN_PROCESS_SLUG" <<'PY'
import sys, json
setup_complete = sys.argv[1] == "true"
has_state = sys.argv[2] == "true"
guidance_injected = sys.argv[3] == "true"
current_stage = sys.argv[4]
status = sys.argv[5]
workflow_template = sys.argv[6]
process_slug = sys.argv[7]
print(json.dumps({
    "schema_version": "1.0.0",
    "has_state": has_state,
    "guidance_injected": guidance_injected,
    "setup_complete": setup_complete,
    "current_stage": current_stage,
    "status": status,
    "workflow_template": workflow_template,
    "process_slug": process_slug,
}))
PY
}

# Reset any stale task-tool burst counter from a previous session
rm -f "$ROOT/.context/task-tool-burst.json"

echo ""
echo "=== Lincoln Session Start ==="
echo ""

# 1. Dependency check + first-run prompt (LINCOLN_SKIP_DEP_CHECK=1 seals this off for tests)
if [[ "${LINCOLN_SKIP_DEP_CHECK:-}" != "1" && -f "$ROOT/.claude/skills/dependencies.yaml" ]]; then
    echo "[Lincoln] Checking dependencies..."
    if ! "$PYTHON" "$ROOT/scripts/lincoln-setup.py" check --root "$ROOT" > /dev/null 2>&1; then
        SETUP_COMPLETE="false"
        if [[ -f "$ROOT/.context/lc-setup-state.yaml" ]]; then
            if "$PYTHON" "$ROOT/scripts/lincoln-setup.py" is-setup-complete --root "$ROOT" > /dev/null 2>&1; then
                SETUP_COMPLETE="true"
                _LINCOLN_SETUP_COMPLETE="true"
            fi
        fi
        if [[ "$SETUP_COMPLETE" != "true" ]]; then
            echo ""
            echo "=== Lincoln 依赖缺失 ==="
            echo ""
            echo "Lincoln 依赖未就绪。请调用 lc-setup 技能完成一次性安装（安装全局工具或写配置前先向用户确认），"
            echo "安装完成前不要进行其他 Lincoln 工作流操作。"
            echo ""
            echo "=== End Lincoln 依赖缺失 ==="
            echo ""
            emit_session_start_json
            exit 0
        fi
    else
        _LINCOLN_SETUP_COMPLETE="true"
    fi
    echo ""
else
    # Even when dependency check is skipped, surface setup completeness in the JSON shape.
    if [[ -f "$ROOT/.context/lc-setup-state.yaml" ]]; then
        if "$PYTHON" "$ROOT/scripts/lincoln-setup.py" is-setup-complete --root "$ROOT" > /dev/null 2>&1; then
            _LINCOLN_SETUP_COMPLETE="true"
        fi
    fi
fi

# Print the cold-start opening guidance block (fresh repo / unclear issue branch).
print_opening_guidance() {
    _LINCOLN_GUIDANCE_INJECTED="true"
    echo ""
    echo "=== Lincoln 开场引导 ==="
    echo ""
    echo "Lincoln 当前没有可驱动的工作状态。请立即执行开场引导流程，再开始任何工作："
    echo ""
    echo "1. 摸排：概览级侦察（顶层结构 / README 前 100 行 / knowledge 索引 / 开放 issues / 用户首条消息），"
    echo "   只读操作 ≤ 8 次，不读源码实现，不做深度扫描（禁用 lc-build-codebase-knowledge）。"
    echo "2. 判断：输出处境评估（角色 / 流程位置 / 问题 / 目标 / Johari 象限初判 + 置信度）。"
    echo "3. 询问和确认：展示判断，按认知象限设计确认动作，每轮 ≤ 3 个问题。"
    echo "4. 有策略的开展：每个目标有明确验收标准、执行路径确定后，再路由到对应工作流。"
    echo ""
    echo "完整流程: .claude/skills/lc-workflow-router/prompts/intake-prompt.md"
    echo "确认完成前不做实现性工作；如需初始化 issue 工作包，由你（Agent）代为执行脚本，不让用户敲命令。"
    echo ""
    echo "=== End Lincoln 开场引导 ==="
    echo ""
}

# 2. Determine state file (process package preferred, legacy fallback)
STATE_FILE=$("$PYTHON" - "$ROOT" "$STATE_FILE" <<'PY'
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

CURRENT_BRANCH="$(git branch --show-current 2>/dev/null || true)"

if [[ ! -f "$STATE_FILE" ]]; then
    echo "No Lincoln state file found ($STATE_FILE)."
    if [[ "$CURRENT_BRANCH" == issue-* ]]; then
        ISSUE_NUMBER="${CURRENT_BRANCH#issue-}"
        # Strip any suffix after the issue number (e.g. issue-33-follow-up -> 33)
        ISSUE_NUMBER="${ISSUE_NUMBER%%-*}"
        if [[ "$ISSUE_NUMBER" =~ ^[0-9]+$ ]]; then
            echo "Auto-initializing issue work package for branch $CURRENT_BRANCH..."
            "$ROOT/scripts/init-lincoln-branch.sh" --issue-number "$ISSUE_NUMBER" --no-commit --auto || {
                echo "Failed to auto-initialize issue work package. Run manually:"
                echo "  scripts/init-lincoln-branch.sh --issue-number $ISSUE_NUMBER"
                echo "=== End Lincoln Session Start ==="
                echo ""
                emit_session_start_json
                exit 0
            }
            # Re-resolve state file after initialization
            STATE_FILE=$("$PYTHON" - "$ROOT" "" <<'PY'
import sys
from pathlib import Path
root = Path(sys.argv[1])
sys.path.insert(0, str(root))
from scripts.lincoln_paths import resolve_state_path
print(resolve_state_path(None, root))
PY
)
        else
            echo "Current branch looks like an issue branch but issue number is unclear."
            print_opening_guidance
            echo "=== End Lincoln Session Start ==="
            echo ""
            emit_session_start_json
            exit 0
        fi
    else
        print_opening_guidance
        echo "=== End Lincoln Session Start ==="
        echo ""
        emit_session_start_json
        exit 0
    fi
fi

_LINCOLN_HAS_STATE="true"

# 3. Read current stage and node info
STATE_JSON=$("$PYTHON" - "$STATE_FILE" <<'PY'
import sys, yaml, json
state = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
current = state.get("current_run", {}).get("current_stage") or "not_started"
status = state.get("current_run", {}).get("status") or "not_started"
workflow_name = state.get("workflow", {}).get("name") or "unknown"
workflow_template = state.get("workflow", {}).get("template") or workflow_name
nodes = state.get("nodes", [])
last_node = nodes[-1] if nodes else {}
waiting_for = last_node.get("status") if last_node else None
if waiting_for in ("completed", "merged"):
    waiting_for = "next_stage"
variables = state.get("current_run", {}).get("variables", {})
process_slug = variables.get("process_slug", "")
if not process_slug and sys.argv[1].endswith("/workflow-stage.yaml"):
    process_slug = __import__("pathlib").Path(sys.argv[1]).parent.name
print(json.dumps({
    "current_stage": current,
    "status": status,
    "workflow_name": workflow_name,
    "workflow_template": workflow_template,
    "last_node": last_node,
    "waiting_for": waiting_for,
    "session_id": variables.get("session_id", ""),
    "design_id": variables.get("design_id", ""),
    "process_slug": process_slug,
}))
PY
)

CURRENT_STAGE=$(echo "$STATE_JSON" | "$PYTHON" -c "import sys,json; print(json.load(sys.stdin)['current_stage'])")
STATUS=$(echo "$STATE_JSON" | "$PYTHON" -c "import sys,json; print(json.load(sys.stdin)['status'])")
WORKFLOW_NAME=$(echo "$STATE_JSON" | "$PYTHON" -c "import sys,json; print(json.load(sys.stdin)['workflow_name'])")
WORKFLOW_TEMPLATE=$(echo "$STATE_JSON" | "$PYTHON" -c "import sys,json; print(json.load(sys.stdin)['workflow_template'])")
LAST_NODE=$(echo "$STATE_JSON" | "$PYTHON" -c "import sys,json; print(json.dumps(json.load(sys.stdin)['last_node']))")
WAITING_FOR=$(echo "$STATE_JSON" | "$PYTHON" -c "import sys,json; print(json.load(sys.stdin)['waiting_for'] or 'none')")
SESSION_ID=$(echo "$STATE_JSON" | "$PYTHON" -c "import sys,json; print(json.load(sys.stdin)['session_id'])")
DESIGN_ID=$(echo "$STATE_JSON" | "$PYTHON" -c "import sys,json; print(json.load(sys.stdin)['design_id'])")
PROCESS_SLUG=$(echo "$STATE_JSON" | "$PYTHON" -c "import sys,json; print(json.load(sys.stdin)['process_slug'])")

_LINCOLN_CURRENT_STAGE="$CURRENT_STAGE"
_LINCOLN_STATUS="$STATUS"
_LINCOLN_WORKFLOW_TEMPLATE="$WORKFLOW_TEMPLATE"
_LINCOLN_PROCESS_SLUG="$PROCESS_SLUG"

echo "Workflow: $WORKFLOW_NAME ($WORKFLOW_TEMPLATE)"
echo "Process package: ${PROCESS_SLUG:-(unset)}"
echo "State file: ${STATE_FILE#$ROOT/}"
echo "Current stage: $CURRENT_STAGE"
echo "Stage status: $STATUS"
echo "Session ID: ${SESSION_ID:-(unset)}"
echo "Design ID: ${DESIGN_ID:-(unset)}"
echo "Waiting for: $WAITING_FOR"
echo ""

# 4. Load stage context, agent role, and workflow template
if [[ "$CURRENT_STAGE" != "not_started" ]]; then
    STAGE_YAML="$ROOT/.claude/stages/$CURRENT_STAGE.yaml"
    if [[ -f "$STAGE_YAML" ]]; then
        echo "=== Lincoln Stage Context ==="
        echo ""
        echo "Stage YAML: ${STAGE_YAML#$ROOT/}"
        echo ""
        # Print the context block if we can extract it; otherwise print the whole file
        "$PYTHON" - "$STAGE_YAML" <<'PY' 2>/dev/null || cat "$STAGE_YAML"
import sys, yaml
data = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
ctx = data.get("context", {})
for key in ["goal", "entry", "execution", "exit", "constraints"]:
    value = ctx.get(key)
    if value:
        print(f"## {key.capitalize()}")
        print(value)
        print("")
PY
        echo ""
        echo "=== End Lincoln Stage Context ==="
        echo ""
    fi

    # Load primary agent role file if declared
    PRIMARY_AGENT=$("$PYTHON" - "$STAGE_YAML" <<'PY' 2>/dev/null || true
import sys, yaml
data = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
print(data.get("agent", {}).get("primary", ""))
PY
)
    if [[ -n "$PRIMARY_AGENT" && -f "$ROOT/.claude/agents/$PRIMARY_AGENT.md" ]]; then
        echo "=== Agent Context ($PRIMARY_AGENT) ==="
        cat "$ROOT/.claude/agents/$PRIMARY_AGENT.md"
        echo ""
        echo "=== End Agent Context ==="
        echo ""
    fi

    # Load default agent contract
    if [[ -f "$ROOT/.claude/agents/default.md" ]]; then
        echo "=== Lincoln Agent Contract ==="
        cat "$ROOT/.claude/agents/default.md"
        echo ""
        echo "=== End Agent Context ==="
        echo ""
    fi

    # Load workflow template summary
    WORKFLOW_FILE="$ROOT/.claude/workflows/${WORKFLOW_TEMPLATE}.yaml"
    if [[ -f "$WORKFLOW_FILE" ]]; then
        echo "=== Workflow Template ($WORKFLOW_TEMPLATE) ==="
        echo "File: ${WORKFLOW_FILE#$ROOT/}"
        "$PYTHON" - "$WORKFLOW_FILE" <<'PY'
import sys, yaml
data = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
wf = data.get("workflow", data)
print("Name:", wf.get("name", "unknown"))
print("Description:", wf.get("description", ""))
print("Steps:")
for step in wf.get("steps", []):
    print(f"  - {step.get('id', 'unknown')}: {step.get('name', '')}")
PY
        echo ""
        echo "=== End Workflow Template ==="
        echo ""
    fi
else
    NEEDS_OPENING_GUIDANCE="true"
fi

# 5. Load Conductor / OMC context
if [[ -d "$ROOT/.context" || -d "$ROOT/.omc" ]]; then
    echo "=== Conductor / OMC Context ==="
    for dir in "$ROOT/.context" "$ROOT/.omc"; do
        if [[ -d "$dir" ]]; then
            for f in $(find "$dir" -maxdepth 2 -type f \( -name '*.md' -o -name '*.yaml' -o -name '*.json' -o -name '*.txt' \) 2>/dev/null | sort); do
                size=$(stat -f%z "$f" 2>/dev/null || stat -c%s "$f" 2>/dev/null || echo 0)
                if [[ "$size" -lt 8192 ]]; then
                    echo ""
                    echo "--- ${f#$ROOT/} ---"
                    cat "$f"
                else
                    echo ""
                    echo "--- ${f#$ROOT/} (too large to print: $size bytes) ---"
                fi
            done
        fi
    done
    echo ""
    echo "=== End Conductor / OMC Context ==="
    echo ""
fi

# 6. Read last node handoff
HANDOFF_FILE=""
if [[ "$LAST_NODE" != "{}" ]]; then
    HANDOFF_FILE=$(echo "$LAST_NODE" | "$PYTHON" -c "import sys,json; print(json.load(sys.stdin).get('handoff_file',''))" 2>/dev/null || echo "")
fi

if [[ -n "$HANDOFF_FILE" && -f "$ROOT/$HANDOFF_FILE" ]]; then
    echo "=== Last Node Handoff ==="
    cat "$ROOT/$HANDOFF_FILE"
    echo ""
    echo "=== End Handoff ==="
    echo ""
fi

if [[ -n "$PROCESS_SLUG" && -d "$ROOT/$PROCESS_SLUG/handoffs" ]]; then
    LATEST_HANDOFF=$(ls -t "$ROOT/$PROCESS_SLUG/handoffs"/*.md 2>/dev/null | head -1 || true)
    if [[ -n "$LATEST_HANDOFF" ]]; then
        echo "=== Latest Process Handoff ==="
        cat "$LATEST_HANDOFF"
        echo ""
        echo "=== End Latest Process Handoff ==="
        echo ""
    fi
fi

# 7. Run status summary
STATUS_OUTPUT=$("$PYTHON" "$ROOT/scripts/lincoln-status.py" --format markdown --state-file "$STATE_FILE" 2>/dev/null) || STATUS_OUTPUT=""
if [[ -n "$STATUS_OUTPUT" ]]; then
    echo "=== Lincoln Status Summary ==="
    echo "$STATUS_OUTPUT"
    echo "=== End Lincoln Status Summary ==="
    echo ""
fi

# 8. Opening guidance for a work package that has not started yet
if [[ "${NEEDS_OPENING_GUIDANCE:-}" == "true" ]]; then
    _LINCOLN_GUIDANCE_INJECTED="true"
    echo "=== Lincoln 开场引导 ==="
    echo ""
    echo "工作包已就绪但尚未启动（current_stage: not_started）。请先完成开场确认，再进入第一阶段："
    echo ""
    echo "1. 摸排：轻量侦察（README 前 100 行 / ${PROCESS_SLUG:-工作包}/documents.yaml / 开放 issues / 用户首条消息），"
    echo "   只读操作 ≤ 8 次，不读源码实现，不做深度扫描。"
    echo "2. 判断：展示处境评估（角色 / 流程位置 / 问题 / 目标 / Johari 象限初判 + 置信度）。"
    echo "3. 询问和确认：按认知象限设计确认动作，每轮 ≤ 3 个问题。"
    echo "4. 确认目标与验收标准后，由你（Agent）代为运行 validate-entry 进入第一阶段："
    echo "   python3 scripts/stage_loader.py --stage <第一阶段> --action validate-entry"
    echo ""
    echo "完整流程: .claude/skills/lc-workflow-router/prompts/intake-prompt.md"
    echo ""
    echo "=== End Lincoln 开场引导 ==="
    echo ""
fi

echo "=== End Lincoln Session Start ==="
echo ""

emit_session_start_json
exit 0
