#!/usr/bin/env bash
set -euo pipefail

# Lincoln Project Initialization Script
# Run this after creating a new project from the Lincoln GitHub template.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -x "$PROJECT_ROOT/.venv/bin/python3" ]; then
  PYTHON="$PROJECT_ROOT/.venv/bin/python3"
elif [ -x "$PROJECT_ROOT/venv/bin/python3" ]; then
  PYTHON="$PROJECT_ROOT/venv/bin/python3"
else
  PYTHON="python3"
fi

cd "$PROJECT_ROOT"

echo "🚀 Initializing Lincoln project at $PROJECT_ROOT"

# ---------------------------------------------------------------------------
# 1. Verify git repository
# ---------------------------------------------------------------------------
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "❌ Error: not a git repository. Please run 'git init' first."
  exit 1
fi

INITIAL_STATUS="$(git status --porcelain)"

# ---------------------------------------------------------------------------
# 2. Ensure placeholder files exist for durable tracked directories
# ---------------------------------------------------------------------------
mkdir -p products oss/clones knowledge/assets knowledge/01-interviews knowledge/02-requirements knowledge/03-features knowledge/04-decisions knowledge/06-references .context

[ -f products/.gitkeep ] || touch products/.gitkeep
[ -f oss/clones/.gitkeep ] || touch oss/clones/.gitkeep
[ -f knowledge/assets/.gitkeep ] || touch knowledge/assets/.gitkeep
[ -f knowledge/01-interviews/.gitkeep ] || touch knowledge/01-interviews/.gitkeep
[ -f knowledge/02-requirements/.gitkeep ] || touch knowledge/02-requirements/.gitkeep
[ -f knowledge/03-features/.gitkeep ] || touch knowledge/03-features/.gitkeep
[ -f knowledge/04-decisions/.gitkeep ] || touch knowledge/04-decisions/.gitkeep
[ -f knowledge/06-references/.gitkeep ] || touch knowledge/06-references/.gitkeep

if [ ! -f products/README.md ]; then
  cat > products/README.md <<'EOF'
# Products

Put first-party product code under `products/<product-slug>/`.

Lincoln process artifacts live in feature-branch process packages, not here.
EOF
fi

if [ ! -f oss/README.md ]; then
  cat > oss/README.md <<'EOF'
# OSS

Track third-party open-source candidates in `oss/projects.yaml`.

Local clones belong under `oss/clones/` and are gitignored.
EOF
fi

if [ ! -f oss/projects.yaml ]; then
  cat > oss/projects.yaml <<'EOF'
projects: []
EOF
fi

# ---------------------------------------------------------------------------
# 3. Check dependencies (warn only; bootstrap should have installed them)
# ---------------------------------------------------------------------------
if [ -f "$PROJECT_ROOT/.claude/skills/dependencies.yaml" ]; then
  if ! "$PYTHON" "$PROJECT_ROOT/scripts/lincoln-setup.py" check --root "$PROJECT_ROOT" > /dev/null 2>&1; then
    echo "⚠️  Lincoln dependency check found missing items."
    echo "   Ask Claude to finish the bootstrap before creating issue work packages."
  else
    echo "✅ Lincoln dependency check passed"
  fi
fi

# ---------------------------------------------------------------------------
# 4. Ensure OpenSpec config is configured
# ---------------------------------------------------------------------------
CONFIG_FILE=".github/openspec-config.yml"
NEEDS_INIT=false

if [ ! -f "$CONFIG_FILE" ]; then
  NEEDS_INIT=true
else
  if grep -qE "owner:\s*your-org" "$CONFIG_FILE" || grep -qE "name:\s*your-product-repo" "$CONFIG_FILE"; then
    NEEDS_INIT=true
  fi
fi

if [ "$NEEDS_INIT" = true ]; then
  echo ""
  echo "📝 $CONFIG_FILE needs the real GitHub owner and repo name."
  OWNER="${LINCOLN_REPO_OWNER:-}"
  NAME="${LINCOLN_REPO_NAME:-}"

  if [ -z "$OWNER" ] || [ -z "$NAME" ]; then
    REMOTE_URL="$(git remote get-url origin 2>/dev/null || true)"
    if [[ "$REMOTE_URL" =~ github\.com[:/]([^/]+)/([^/]+?)(\.git)?$ ]]; then
      OWNER="${BASH_REMATCH[1]}"
      NAME="${BASH_REMATCH[2]}"
    fi
  fi

  if [ -n "$OWNER" ] && [ -n "$NAME" ]; then
    "$PYTHON" "$PROJECT_ROOT/scripts/lincoln-setup.py" init-repo-config \
      --root "$PROJECT_ROOT" --owner "$OWNER" --name "$NAME"
  else
    echo "   Please ask Claude to run:"
    echo "     python scripts/lincoln-setup.py init-repo-config --owner <owner> --name <repo>"
    echo "   Or set LINCOLN_REPO_OWNER and LINCOLN_REPO_NAME and re-run."
  fi
else
  echo "✅ OpenSpec config already contains real values"
fi

# ---------------------------------------------------------------------------
# 5. Make validator executable
# ---------------------------------------------------------------------------
VALIDATOR="scripts/validate_stage.py"
if [ -f "$VALIDATOR" ]; then
  chmod +x "$VALIDATOR"
  echo "✅ Validator made executable"
fi

# ---------------------------------------------------------------------------
# 6. GitHub CLI auth check
# ---------------------------------------------------------------------------
if command -v gh > /dev/null 2>&1; then
  if ! gh auth status > /dev/null 2>&1; then
    echo "⚠️  GitHub CLI is installed but not authenticated. Ask Claude to run 'gh auth login' before using split-to-github."
  else
    echo "✅ GitHub CLI authenticated"
  fi
else
  echo "⚠️  GitHub CLI not found. Ask Claude to install it during bootstrap."
fi

# ---------------------------------------------------------------------------
# 7. Initial commit for files created by this script
# ---------------------------------------------------------------------------
if [ -z "$(git status --porcelain)" ]; then
  echo "ℹ️  No changes to commit"
elif [ -n "$INITIAL_STATUS" ]; then
  echo "⚠️  Existing local changes detected before initialization; skipping automatic commit."
  echo "   Review and commit the changes manually when ready."
else
  git add \
    products/.gitkeep \
    products/README.md \
    oss/README.md \
    oss/projects.yaml \
    knowledge/assets/.gitkeep \
    knowledge/01-interviews/.gitkeep \
    knowledge/02-requirements/.gitkeep \
    knowledge/03-features/.gitkeep \
    knowledge/04-decisions/.gitkeep \
    knowledge/06-references/.gitkeep
  if git diff --cached --quiet; then
    echo "ℹ️  No tracked initialization changes to commit"
  else
    git commit -m "chore: init project with Lincoln workflow"
    echo "✅ Initial commit created"
  fi
fi

# Record that project initialization is complete.
"$PYTHON" "$PROJECT_ROOT/scripts/lincoln-setup.py" mark-step \
  --root "$PROJECT_ROOT" --step init_project --status completed

echo ""
echo "🎉 Lincoln project initialized successfully!"
echo ""
echo "Next steps:"
echo "  1. Create a feature process branch: scripts/init-lincoln-branch.sh --issue-number <number> --session-id <session-id> --design-id <design-id> --process-slug <feature-slug> --push"
echo "  2. Place interview recordings in <feature-slug>/recordings/"
echo "  3. Say to Claude Code: '处理一下这个访谈录音 <feature-slug>/recordings/<file>'"
