#!/usr/bin/env python3
"""Deterministic content-quality checks for Lincoln PRD Markdown/HTML documents.

The checker deliberately does not call an LLM.  It validates the core-v2 content
contract while preserving the old thirteen-heading structural check for legacy
documents.  Shared stage/workflow registries can call ``validate_prd`` directly.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
import re
import sys
from typing import Iterable

CORE_V2 = "core-v2"
LEGACY = "legacy"
AUTO = "auto"
CONTRACT_MARKER_RE = re.compile(r"<!--\s*prd-contract:\s*core-v2\s*-->", re.IGNORECASE)
VERSION_MARKER_RE = re.compile(r"<!--\s*version:\s*v\d+\.\d+\s*-->")
DOC_SOURCE_RE = re.compile(
    r"<script(?=\s)([^>]*?\s(?:id=\"docSource\"|type=\"text/markdown\")[^>]*?)>(.*?)</script>",
    re.DOTALL | re.IGNORECASE,
)
HEADING_RE = re.compile(r"^##(?!#)\s*(?:\d+\s*[.、．]?\s*)?(.+?)\s*#*\s*$", re.MULTILINE)

CORE_V2_SECTIONS = (
    "版本说明",
    "修订记录",
    "执行摘要",
    "问题与证据",
    "用户与相关者",
    "目标与成功指标",
    "范围与非目标",
    "用户故事",
    "功能需求",
    "业务流程与规则",
    "验收标准",
    "非功能需求",
    "依赖与发布",
    "风险与开放问题",
    "相关产物链接",
)

# Keep this list structurally identical to the issue-129 validator.  Legacy mode
# intentionally checks headings only, so existing skeletons do not break.
LEGACY_SECTIONS = (
    "版本说明",
    "修订记录",
    "功能列表",
    "需求背景",
    "用户故事",
    "功能拆解",
    "业务流程图",
    "验收标准",
    "业务规则",
    "非功能需求",
    "关联系统/接口",
    "相关产物链接",
    "风险与开放问题",
)

PLACEHOLDER_RE = re.compile(r"待确认|待补充|待人类|待\s*PM|TODO|FIXME|TBD", re.IGNORECASE)
PLACEHOLDER_PHRASES = {
    "",
    "-",
    "--",
    "---",
    "...",
    "…",
    "?",
    "???",
    "n/a",
    "na",
    "none",
    "null",
    "placeholder",
    "lorem ipsum",
    "待填写",
    "待确认",
    "待补充",
    "待人类",
    "待pm",
    "todo",
    "fixme",
    "tbd",
    "待定",
    "暂无",
    "无",
    "无内容",
    "略",
    "占位",
    "请填写",
    "在此填写",
}
ID_CANDIDATE_RES = {
    "REQ": re.compile(r"(?<![A-Za-z0-9])REQ-[A-Za-z0-9-]*", re.IGNORECASE),
    "AC": re.compile(r"(?<![A-Za-z0-9])AC-[A-Za-z0-9-]*", re.IGNORECASE),
}
ID_FULL_RES = {
    "REQ": re.compile(r"REQ-\d{3,}"),
    "AC": re.compile(r"AC-\d{3,}"),
}


@dataclass(frozen=True)
class QualityIssue:
    """One actionable validation failure."""

    code: str
    section: str
    message: str

    def format(self) -> str:
        location = f" [{self.section}]" if self.section else ""
        return f"[{self.code}]{location} {self.message}"


@dataclass(frozen=True)
class ValidationResult:
    mode: str
    issues: tuple[QualityIssue, ...]

    @property
    def ok(self) -> bool:
        return not self.issues

    def as_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "mode": self.mode,
            "issues": [
                {"code": issue.code, "section": issue.section, "message": issue.message}
                for issue in self.issues
            ],
        }


def extract_markdown(text: str) -> str:
    """Extract Lincoln's embedded docSource, or return plain Markdown unchanged."""
    match = DOC_SOURCE_RE.search(text)
    return match.group(2).strip() if match else text.strip()


def detect_mode(text: str) -> str:
    """Only an explicit core-v2 marker opts into semantic checks."""
    return CORE_V2 if CONTRACT_MARKER_RE.search(text) else LEGACY


def _headings(text: str) -> list[tuple[str, int, int]]:
    return [(match.group(1).strip(), match.start(), match.end()) for match in HEADING_RE.finditer(text)]


def _section_body(text: str, headings: list[tuple[str, int, int]], index: int) -> str:
    start = headings[index][2]
    end = headings[index + 1][1] if index + 1 < len(headings) else len(text)
    return text[start:end].strip()


def _strip_table_cell(cell: str) -> str:
    return cell.strip().strip("*_` ").strip()


def _split_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [_strip_table_cell(cell) for cell in stripped.split("|")]


def _is_table_separator(line: str) -> bool:
    cells = _split_table_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells)


def _tables(text: str) -> list[tuple[list[str], list[list[str]]]]:
    """Return simple Markdown tables as (header, data rows)."""
    lines = text.splitlines()
    tables: list[tuple[list[str], list[list[str]]]] = []
    index = 0
    while index + 1 < len(lines):
        if "|" not in lines[index] or not _is_table_separator(lines[index + 1]):
            index += 1
            continue
        header = _split_table_row(lines[index])
        index += 2
        rows: list[list[str]] = []
        while index < len(lines) and "|" in lines[index] and lines[index].strip():
            if not _is_table_separator(lines[index]):
                rows.append(_split_table_row(lines[index]))
            index += 1
        tables.append((header, rows))
    return tables


def _content_lines(body: str) -> list[str]:
    """Remove document scaffolding but retain words, numbers and diagram labels."""
    body = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
    lines = body.splitlines()
    meaningful: list[str] = []
    for index, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line or re.match(r"^#{1,6}\s+", line):
            continue
        if re.fullmatch(r"(?:[-*_]\s*){3,}", line):
            continue
        if _is_table_separator(line):
            continue
        # A table header followed by its separator is scaffolding, not content.
        if "|" in line and index + 1 < len(lines) and _is_table_separator(lines[index + 1]):
            continue
        if line.startswith("```") or line.startswith("~~~"):
            continue
        line = re.sub(r"^>\s*", "", line)
        line = re.sub(r"^[-+*]\s+", "", line)
        line = re.sub(r"^\d+[.)、]\s*", "", line)
        line = re.sub(r"</?(?:br|p|div|span)(?:\s[^>]*)?>", "", line, flags=re.IGNORECASE)
        if "|" in line:
            line = " ".join(cell for cell in _split_table_row(line) if cell)
        line = line.strip().strip("*_`#> ").strip()
        if line:
            meaningful.append(line)
    return meaningful


def _normalise_placeholder(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[\s*_`#>|:：，。；;、.!！?？()\[\]{}<>-]+", "", value)
    return value


def _validate_section_content(sections: dict[str, str]) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    for name in CORE_V2_SECTIONS:
        body = sections.get(name)
        if body is None:
            continue
        lines = _content_lines(body)
        if not lines:
            issues.append(
                QualityIssue(
                    "EMPTY_SECTION",
                    name,
                    "Chapter has no business content; answer the chapter question instead of leaving a heading or empty table.",
                )
            )
            continue
        normalised = [_normalise_placeholder(line) for line in lines]
        if all(value in {_normalise_placeholder(item) for item in PLACEHOLDER_PHRASES} for value in normalised):
            issues.append(
                QualityIssue(
                    "PLACEHOLDER_SECTION",
                    name,
                    "Chapter contains only placeholders; replace them with reviewed business content.",
                )
            )
        elif PLACEHOLDER_RE.search(body):
            issues.append(
                QualityIssue(
                    "PLACEHOLDER_CONTENT",
                    name,
                    "Resolve TODO/TBD/待补充-style notes in conversation, then write the decision into this chapter.",
                )
            )
    return issues


def _validate_structure(text: str, required: Iterable[str], *, core: bool) -> tuple[list[QualityIssue], dict[str, str]]:
    headings = _headings(text)
    required = tuple(required)
    issues: list[QualityIssue] = []
    sections: dict[str, str] = {}
    positions: list[int] = []

    for name in required:
        matches = [index for index, heading in enumerate(headings) if heading[0] == name]
        if not matches:
            issues.append(
                QualityIssue(
                    "MISSING_SECTION",
                    name,
                    f"Add an H2 chapter named '{name}' (an optional numeric prefix is allowed).",
                )
            )
            continue
        if core and len(matches) > 1:
            issues.append(
                QualityIssue(
                    "DUPLICATE_SECTION",
                    name,
                    "Keep exactly one H2 chapter with this name so readers and validators have one source of truth.",
                )
            )
        index = matches[0]
        positions.append(index)
        sections[name] = _section_body(text, headings, index)

    if core and len(positions) == len(required) and positions != sorted(positions):
        issues.append(
            QualityIssue(
                "SECTION_ORDER",
                "document",
                "Reorder the 15 core-v2 chapters to match docs/prd-quality-standard.md; additional chapters may follow the core contract.",
            )
        )
    return issues, sections


def _find_column(header: list[str], aliases: set[str]) -> int | None:
    for index, cell in enumerate(header):
        normalised = re.sub(r"[\s*_`]", "", cell)
        if normalised in aliases:
            return index
    return None


def _cell(row: list[str], index: int) -> str:
    return row[index].strip() if index < len(row) else ""


def _is_empty_value(value: str) -> bool:
    return _normalise_placeholder(value) in {_normalise_placeholder(item) for item in PLACEHOLDER_PHRASES}


def _validate_metrics(body: str) -> list[QualityIssue]:
    section = "目标与成功指标"
    metric_tables = [
        (header, rows)
        for header, rows in _tables(body)
        if _find_column(header, {"指标", "指标名称", "成功指标"}) is not None
    ]
    if not metric_tables:
        return [
            QualityIssue(
                "METRIC_TABLE",
                section,
                "Add at least one success-metric table with 指标、基线、目标值、时间窗 columns and a concrete data row.",
            )
        ]

    header, rows = metric_tables[0]
    columns = {
        "基线": _find_column(header, {"基线", "基线值"}),
        "目标值": _find_column(header, {"目标", "目标值"}),
        "时间窗": _find_column(header, {"时间窗", "时间窗口", "目标时间窗"}),
    }
    issues: list[QualityIssue] = []
    for label, column in columns.items():
        if column is None:
            issues.append(
                QualityIssue(
                    "METRIC_FIELDS",
                    section,
                    f"Success-metric table is missing '{label}'; add that column and record a concrete value for every metric.",
                )
            )
    if issues:
        return issues

    data_rows = [row for row in rows if any(not _is_empty_value(cell) for cell in row)]
    if not data_rows:
        return [
            QualityIssue(
                "METRIC_VALUES",
                section,
                "Success-metric table has no usable data row; add baseline, target and time window values.",
            )
        ]
    for row_number, row in enumerate(data_rows, start=1):
        for label, column in columns.items():
            assert column is not None
            if _is_empty_value(_cell(row, column)):
                issues.append(
                    QualityIssue(
                        "METRIC_VALUES",
                        section,
                        f"Metric row {row_number} has no concrete {label}; fill baseline, target and time window for every metric.",
                    )
                )
    return issues


def _validate_non_goals(body: str) -> list[QualityIssue]:
    match = re.search(
        r"(?:^#{3,6}\s*非目标\s*$|(?:\*\*)?非目标(?:\*\*)?\s*[:：])",
        body,
        re.MULTILINE,
    )
    if match:
        return []
    return [
        QualityIssue(
            "NON_GOALS",
            "范围与非目标",
            "Add an explicit '### 非目标' subsection (or labelled list) describing what is excluded and why.",
        )
    ]


def _valid_id(token: str, kind: str) -> bool:
    return bool(ID_FULL_RES[kind].fullmatch(token))


def _validate_ids(requirements_body: str, acceptance_body: str) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    requirement_tokens = ID_CANDIDATE_RES["REQ"].findall(requirements_body)
    acceptance_tokens = ID_CANDIDATE_RES["AC"].findall(acceptance_body)

    for kind, tokens, section in (
        ("REQ", requirement_tokens, "功能需求"),
        ("AC", acceptance_tokens, "验收标准"),
    ):
        for token in sorted({token for token in tokens if not _valid_id(token, kind)}):
            issues.append(
                QualityIssue(
                    f"{kind}_ID_FORMAT",
                    section,
                    f"Invalid {kind} ID '{token}'; use {kind}-001 with at least three digits and keep it stable across revisions.",
                )
            )

    valid_requirements = [token.upper() for token in requirement_tokens if _valid_id(token, "REQ")]
    valid_acceptance = [token.upper() for token in acceptance_tokens if _valid_id(token, "AC")]
    if not valid_requirements:
        issues.append(
            QualityIssue(
                "MISSING_REQUIREMENT_ID",
                "功能需求",
                "Give every functional requirement a stable ID such as REQ-001.",
            )
        )
    if not valid_acceptance:
        issues.append(
            QualityIssue(
                "MISSING_ACCEPTANCE_ID",
                "验收标准",
                "Give every acceptance criterion a stable ID such as AC-001 and link it to a requirement ID.",
            )
        )

    for kind, ids, section in (
        ("REQ", valid_requirements, "功能需求"),
        ("AC", valid_acceptance, "验收标准"),
    ):
        duplicates = sorted(token for token, count in Counter(ids).items() if count > 1)
        for token in duplicates:
            issues.append(
                QualityIssue(
                    f"DUPLICATE_{kind}_ID",
                    section,
                    f"{token} is defined more than once in this chapter; keep one definition and reference it from other rows.",
                )
            )

    defined_requirements = set(valid_requirements)
    covered_requirements: set[str] = set()
    for line in acceptance_body.splitlines():
        acceptance_ids = [token.upper() for token in ID_CANDIDATE_RES["AC"].findall(line) if _valid_id(token, "AC")]
        if not acceptance_ids:
            continue
        references = [token.upper() for token in ID_CANDIDATE_RES["REQ"].findall(line) if _valid_id(token, "REQ")]
        if not references:
            issues.append(
                QualityIssue(
                    "ACCEPTANCE_TRACE",
                    "验收标准",
                    f"Acceptance row {', '.join(acceptance_ids)} has no requirement ID; add the originating REQ-NNN in the same row.",
                )
            )
        for reference in references:
            if reference not in defined_requirements:
                issues.append(
                    QualityIssue(
                        "UNKNOWN_REQUIREMENT",
                        "验收标准",
                        f"Acceptance row references {reference}, which is not defined in 功能需求; correct the ID or define the requirement.",
                    )
                )
            else:
                covered_requirements.add(reference)

    for requirement in sorted(defined_requirements - covered_requirements):
        issues.append(
            QualityIssue(
                "REQUIREMENT_WITHOUT_ACCEPTANCE",
                "验收标准",
                f"{requirement} has no linked acceptance criterion; add an AC-NNN row that references it.",
            )
        )
    return issues


def validate_text(text: str, mode: str = AUTO) -> ValidationResult:
    """Validate Markdown or rendered HTML text without performing file or network I/O."""
    if mode not in {AUTO, CORE_V2, LEGACY}:
        raise ValueError("mode must be auto, core-v2 or legacy")
    text = extract_markdown(text)
    selected_mode = detect_mode(text) if mode == AUTO else mode

    if selected_mode == LEGACY:
        issues, _ = _validate_structure(text, LEGACY_SECTIONS, core=False)
        return ValidationResult(LEGACY, tuple(issues))

    issues, sections = _validate_structure(text, CORE_V2_SECTIONS, core=True)
    if not CONTRACT_MARKER_RE.search(text):
        issues.append(
            QualityIssue(
                "MISSING_CONTRACT_MARKER",
                "document",
                "Add <!-- prd-contract: core-v2 --> near the top; new documents must not silently fall back to legacy checks.",
            )
        )
    if not VERSION_MARKER_RE.search(text):
        issues.append(
            QualityIssue(
                "MISSING_VERSION_MARKER",
                "版本说明",
                "Add <!-- version: vX.Y --> so review, snapshots and related artifacts can refer to the same PRD baseline.",
            )
        )
    issues.extend(_validate_section_content(sections))
    if "目标与成功指标" in sections:
        issues.extend(_validate_metrics(sections["目标与成功指标"]))
    if "范围与非目标" in sections:
        issues.extend(_validate_non_goals(sections["范围与非目标"]))
    if "功能需求" in sections and "验收标准" in sections:
        issues.extend(_validate_ids(sections["功能需求"], sections["验收标准"]))
    return ValidationResult(CORE_V2, tuple(issues))


def validate_prd(path: str | Path, mode: str = AUTO) -> ValidationResult:
    """Validate a PRD file.  File errors are intentionally raised for CLI handling."""
    prd_path = Path(path)
    return validate_text(prd_path.read_text(encoding="utf-8"), mode=mode)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate Lincoln PRD core-v2 content quality or legacy 13-chapter structure (no LLM required)."
    )
    parser.add_argument("path", type=Path, help="Path to a PRD .md file or rendered .html file")
    parser.add_argument(
        "--mode",
        choices=(AUTO, CORE_V2, LEGACY),
        default=AUTO,
        help="auto uses core-v2 only when <!-- prd-contract: core-v2 --> is present (default: auto)",
    )
    parser.add_argument("--json", action="store_true", help="Emit stable machine-readable JSON instead of text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.path.is_file():
        message = f"ERROR: PRD file not found: {args.path}. Pass an existing .md or .html file."
        if args.json:
            print(json.dumps({"ok": False, "error": message}, ensure_ascii=False))
        else:
            print(message, file=sys.stderr)
        return 2
    try:
        result = validate_prd(args.path, mode=args.mode)
    except (OSError, UnicodeError) as error:
        message = f"ERROR: Cannot read PRD {args.path}: {error}. Check the path and UTF-8 encoding."
        if args.json:
            print(json.dumps({"ok": False, "error": message}, ensure_ascii=False))
        else:
            print(message, file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result.as_dict(), ensure_ascii=False, sort_keys=True))
    elif result.ok:
        print(f"PASS: {args.path} ({result.mode})")
    else:
        print(f"FAIL: {args.path} ({result.mode}) with {len(result.issues)} issue(s)", file=sys.stderr)
        for issue in result.issues:
            print(f"  - {issue.format()}", file=sys.stderr)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
