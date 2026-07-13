#!/usr/bin/env bash
# Harness drift check (CI-friendly, lightweight):
# 1. Regenerate codex/opencode artifacts into a temp dir — proves manifests
#    load and generation succeeds (catches broken sources / bad manifests).
# 2. If generated artifacts already exist in the project (someone ran
#    generate-harness locally), verify they have not drifted from .claude/.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ -d "$ROOT/.venv" ] && [ -x "$ROOT/.venv/bin/python3" ]; then
    PYTHON="$ROOT/.venv/bin/python3"
else
    PYTHON="python3"
fi

FAIL=0
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/project" "$TMP/home"

for HARNESS in codex opencode; do
    echo "==> Harness smoke generation: $HARNESS"
    if ! "$PYTHON" scripts/lincoln_harness_adapter.py \
        --harness "$HARNESS" --root "$ROOT" \
        --project-dir "$TMP/project" --home-dir "$TMP/home" > /dev/null; then
        echo "❌ generation failed for harness: $HARNESS"
        FAIL=1
        continue
    fi

    # Drift comparison only when artifacts were generated into the project.
    case "$HARNESS" in
        opencode) MARKER="$ROOT/.opencode" ;;
        codex)    MARKER="$ROOT/AGENTS.md" ;;
    esac
    if [ -e "$MARKER" ]; then
        echo "==> Drift check: $HARNESS (project artifacts present)"
        if ! "$PYTHON" scripts/lincoln_harness_adapter.py \
            --harness "$HARNESS" --root "$ROOT" \
            --project-dir "$ROOT" --home-dir "$HOME" --check; then
            FAIL=1
        fi
    fi
done

if [ "$FAIL" -eq 0 ]; then
    echo "✅ harness drift check passed"
fi
exit "$FAIL"
