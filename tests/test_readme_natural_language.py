"""README natural-language rules: no terminal-command teaching in user-facing docs."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README_ZH = ROOT / "README.md"
README_EN = ROOT / "README.en.md"

COMMAND_PATTERN = re.compile(r"python3?\s+scripts/|bash\s+scripts/|scripts/[\w.-]+\.(?:sh|py)")

USER_FACING_SECTIONS = {
    README_ZH: ["快速开始", "工作状态与交接", "多 harness 支持"],
    README_EN: ["Quick Start", "Workflow Status & Handoff", "Multi-harness support"],
}


def _fenced_bodies(text):
    """Return the content lines of every ``` fence (including indented ones)."""
    bodies = []
    inside = False
    current = []
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            if inside:
                bodies.append("\n".join(current))
                current = []
            inside = not inside
            continue
        if inside:
            current.append(line)
    return bodies


def _section_body(text, heading_prefix):
    """Extract the body of a `## <heading_prefix>` section up to the next `## ` heading."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith(f"## {heading_prefix}"):
            start = i + 1
            break
    if start is None:
        raise AssertionError(f"section not found: {heading_prefix}")
    body = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        body.append(line)
    return "\n".join(body)


def _strip_fences(text):
    return "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("```")
    )


def test_no_script_invocations_in_code_fences():
    for readme in (README_ZH, README_EN):
        for body in _fenced_bodies(readme.read_text(encoding="utf-8")):
            assert not COMMAND_PATTERN.search(body), (
                f"{readme.name} fence contains a terminal command:\n{body}"
            )


def test_user_facing_sections_have_no_inline_commands():
    for readme, sections in USER_FACING_SECTIONS.items():
        text = readme.read_text(encoding="utf-8")
        for section in sections:
            body = _strip_fences(_section_body(text, section))
            assert not COMMAND_PATTERN.search(body), (
                f"{readme.name} section '{section}' contains an inline terminal command"
            )


def test_readme_mirror_structure():
    zh_headings = [l for l in README_ZH.read_text(encoding="utf-8").splitlines() if l.startswith("## ")]
    en_headings = [l for l in README_EN.read_text(encoding="utf-8").splitlines() if l.startswith("## ")]
    assert len(zh_headings) == len(en_headings), (
        f"heading count mismatch: zh={len(zh_headings)} en={len(en_headings)}"
    )


def test_nl_table_present():
    assert "| 你说 | Agent 做 |" in README_ZH.read_text(encoding="utf-8")
    assert "| You say | Agent does |" in README_EN.read_text(encoding="utf-8")
