"""Ensure skill/agent docs do not hard-code project-relative script paths."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAUDE_DIR = ROOT / ".claude"


def test_no_bare_python_scripts_refs():
    for path in CLAUDE_DIR.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in {".md", ".yaml", ".json", ".sh"}:
            continue
        text = path.read_text(encoding="utf-8")
        assert "python3 scripts/" not in text, f"{path} has bare script reference"
