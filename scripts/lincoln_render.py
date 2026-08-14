#!/usr/bin/env python3
"""Generic template renderer for Lincoln issue-package HTML pages.

Reads stage YAML `artifact_templates` mappings, replaces runtime variables and
page-level placeholders, injects Markdown or structured data for doc pages, and
writes the rendered HTML atomically.  Intended to replace ad-hoc
copy-and-replace in skill prompts with a single CLI that agent prompts can
reference.

Examples:
    python scripts/lincoln_render.py \\
        --stage clarify \\
        --target issue-42/pages/docs/prd.html \\
        --title "产品需求文档" \\
        --nav-label "PRD" \\
        --nav-group "Docs" \\
        --version v1.0 \\
        --uid prd \\
        --markdown issue-42/pages/docs/prd.md

    python scripts/lincoln_render.py \\
        --stage product-design-docs \\
        --target issue-42/pages/docs/feature-catalog.html \\
        --title "功能目录" \\
        --nav-label "功能目录" \\
        --version v1.0 \\
        --uid feature-catalog \\
        --data issue-42/pages/docs/feature-catalog.yaml
"""

from __future__ import annotations

import argparse
import fnmatch
import html
import json
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import yaml

from scripts.lincoln_paths import (
    PROJECT_ROOT as _PROJECT_ROOT,
    atomic_write_text,
    get_process_slug,
    load_yaml,
    resolve_state_path,
)

STAGES_DIR = PROJECT_ROOT / ".claude" / "stages"

# Placeholders that the renderer always supports.
PAGE_PLACEHOLDERS = {
    "TITLE",
    "NAV_LABEL",
    "NAV_GROUP",
    "VERSION",
    "UID",
    "STAGE",
    "MARKDOWN_SOURCE",
}

# Placeholders rendered from structured page data.
DATA_PLACEHOLDERS = {
    "PAGE_DATA",
    "SECTIONS_HTML",
    "STORIES_HTML",
    "FEATURES_HTML",
    "ENTITIES_HTML",
    "FLOWS_HTML",
    "PAGES_HTML",
    "APIS_HTML",
    "FIELDS_HTML",
}

# Variables commonly declared in stage YAML `variables` and sourced from
# workflow-stage.yaml `current_run.variables`.
RUNTIME_VARIABLES = {
    "process_slug",
    "session_id",
    "design_id",
    "change_name",
    "feature_slug",
    "pr_number",
    "decision_id",
    "requirement_id",
}

VERSION_COMMENT_RE = re.compile(r"<!--\s*version:\s*(v\d+\.\d+)\s*-->", re.IGNORECASE)
META_RE = re.compile(r'<meta\s+name="([^"]+)"\s+content="([^"]*)"\s*/?>')


def _load_stage(stage_id: str) -> dict[str, Any]:
    path = STAGES_DIR / f"{stage_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Stage definition not found: {path}")
    data = load_yaml(path)
    if not isinstance(data, dict):
        raise ValueError(f"Stage YAML root is not a mapping: {path}")
    return data


def _load_runtime_variables(state_file: str | Path | None = None) -> dict[str, str]:
    """Load runtime variables from the canonical workflow state file."""
    if state_file is not None:
        state_path = Path(state_file)
    else:
        state_path = resolve_state_path(None, PROJECT_ROOT)
    if not state_path or not state_path.exists():
        return {}
    try:
        state = load_yaml(state_path)
    except Exception:
        return {}
    variables = state.get("current_run", {}).get("variables", {})
    return {k: str(v) for k, v in variables.items() if isinstance(v, (str, int, float))}


def _load_page_data(data_path: str | Path | None) -> dict[str, Any]:
    """Load optional structured page data from YAML or JSON."""
    if not data_path:
        return {}
    path = Path(data_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"Page data root must be an object: {path}")
    return data


def _resolve_template(templates: dict[str, str], target: str) -> tuple[Path, str]:
    """Return (template_path, matched_pattern) for *target* from interpolated templates."""
    if not templates:
        raise ValueError("No 'artifact_templates' mapping provided")

    # Exact match first.
    for pattern, template in templates.items():
        if pattern == target:
            return PROJECT_ROOT / template, pattern

    # Then glob match; prefer the longest/most specific pattern.
    matches: list[tuple[str, str]] = []
    for pattern, template in templates.items():
        if fnmatch.fnmatch(target, pattern):
            matches.append((pattern, template))
    if matches:
        # Longer pattern string is usually more specific.
        matches.sort(key=lambda x: len(x[0]), reverse=True)
        return PROJECT_ROOT / matches[0][1], matches[0][0]

    raise ValueError(f"No artifact_templates pattern matches target '{target}'")


def _replace_variables(text: str, variables: dict[str, str]) -> str:
    """Replace {VAR} placeholders where VAR is present in variables."""

    def repl(match: re.Match) -> str:
        key = match.group(1)
        if key in variables:
            return variables[key]
        # Preserve unknown placeholders so callers can see what is missing.
        return match.group(0)

    return re.sub(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", repl, text)


def _escape_script_content(text: str) -> str:
    """Escape content that would break an embedded <script> block."""
    return text.replace("</script>", "<\\/script>")


def _escape_markdown_for_script(markdown: str) -> str:
    """Escape content that would break the embedded <script type="text/markdown"> block."""
    return markdown.replace("</script>", "<\\/script>")


def _derive_uid_from_target(target: str) -> str:
    """Derive a stable UID from the target filename."""
    name = Path(target).name
    # Strip a single well-known extension.
    for ext in (".html", ".htm"):
        if name.lower().endswith(ext):
            return name[: -len(ext)]
    return name


def _detect_version_from_markdown(source: str | Path) -> str | None:
    """Extract a version marker from Markdown text or a Markdown file path."""
    text = ""
    if isinstance(source, Path):
        if not source.exists():
            return None
        try:
            text = source.read_text(encoding="utf-8")
        except Exception:
            return None
    else:
        text = source
    for line in text.splitlines()[:20]:
        m = VERSION_COMMENT_RE.search(line)
        if m:
            return m.group(1)
    return None


def _derive_defaults(
    markdown_path: str | Path | None,
    target: str,
    title: str,
    nav_label: str | None,
    nav_group: str | None,
    version: str | None,
    uid: str | None,
    stage_mark: str | None,
    stage_id: str,
) -> dict[str, str]:
    """Return coarse defaults for page-level placeholders.

    The CLI already provides defaults for some fields; this helper centralizes
    the "derive from title/target/markdown" logic so both single-page and batch
    rendering behave the same way.
    """
    md_path: Path | None = None
    md_content: str | None = None
    if markdown_path:
        if isinstance(markdown_path, Path):
            md_path = markdown_path
        elif "\n" in markdown_path or len(markdown_path) > 260 or not (PROJECT_ROOT / markdown_path).exists():
            # Treat as inline Markdown content rather than a file path.
            md_content = markdown_path
        else:
            md_path = PROJECT_ROOT / markdown_path

    derived_title = title
    derived_nav_label = nav_label if nav_label is not None else title
    derived_nav_group = nav_group if nav_group is not None else "Docs"
    derived_version = version if version is not None else ""
    derived_uid = uid if uid is not None else ""
    derived_stage_mark = stage_mark if stage_mark is not None else stage_id

    if not derived_version:
        if md_path and md_path.exists():
            derived_version = _detect_version_from_markdown(md_path) or ""
        elif md_content:
            derived_version = _detect_version_from_markdown(md_content) or ""
    if not derived_version:
        derived_version = "v1.0"

    if not derived_uid:
        derived_uid = _derive_uid_from_target(target)

    return {
        "title": derived_title,
        "nav_label": derived_nav_label,
        "nav_group": derived_nav_group,
        "version": derived_version,
        "uid": derived_uid,
        "stage_mark": derived_stage_mark,
    }


def _html_attr(value: str) -> str:
    return html.escape(value, quote=True)


def _render_sections_html(sections: Any) -> str:
    """Render a list of sections as titled cards."""
    if not isinstance(sections, list):
        return ""
    out = ['<div class="lincoln-sections">']
    for section in sections:
        if not isinstance(section, dict):
            continue
        title = section.get("title", "")
        content = section.get("content", "")
        out.append(f'<section class="lincoln-section">')
        if title:
            out.append(f'<h2 class="lincoln-section-title">{_html_attr(title)}</h2>')
        out.append(f'<div class="lincoln-section-body">{_escape_script_content(str(content))}</div>')
        out.append('</section>')
    out.append('</div>')
    return "\n".join(out)


def _render_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> str:
    """Render a generic HTML table from rows and (key, label) columns."""
    if not rows:
        return ""
    out = ['<table class="lincoln-data-table">', '<thead><tr>']
    for _key, label in columns:
        out.append(f'<th>{_html_attr(str(label))}</th>')
    out.append('</tr></thead><tbody>')
    for row in rows:
        out.append('<tr>')
        for key, _label in columns:
            value = row.get(key, "") if isinstance(row, dict) else ""
            out.append(f'<td>{_escape_script_content(str(value))}</td>')
        out.append('</tr>')
    out.append('</tbody></table>')
    return "\n".join(out)


def _render_stories_html(stories: Any) -> str:
    if not isinstance(stories, list):
        return ""
    columns = [
        ("who", "角色"),
        ("want", "想要"),
        ("so", "以便"),
        ("acceptance", "验收标准"),
        ("source", "来源"),
    ]
    return _render_table(stories, columns)


def _render_features_html(features: Any) -> str:
    if not isinstance(features, list):
        return ""
    columns = [
        ("id", "ID"),
        ("title", "功能"),
        ("priority", "优先级"),
        ("acceptance", "验收标准"),
        ("source", "来源"),
    ]
    return _render_table(features, columns)


def _render_entities_html(entities: Any) -> str:
    if not isinstance(entities, list):
        return ""
    out = ['<div class="lincoln-entities">']
    for entity in entities:
        if not isinstance(entity, dict):
            continue
        name = entity.get("name", "")
        fields = entity.get("fields", [])
        constraints = entity.get("constraints", "")
        states = entity.get("states", "")
        out.append(f'<section class="lincoln-entity"><h3>{_html_attr(str(name))}</h3>')
        if constraints:
            out.append(f'<p class="lincoln-meta"><strong>约束：</strong>{_escape_script_content(str(constraints))}</p>')
        if states:
            out.append(f'<p class="lincoln-meta"><strong>状态：</strong>{_escape_script_content(str(states))}</p>')
        if isinstance(fields, list) and fields:
            out.append(_render_table(fields, [
                ("name", "字段名"),
                ("type", "类型"),
                ("required", "必填"),
                ("description", "说明"),
                ("source", "来源"),
            ]))
        out.append('</section>')
    out.append('</div>')
    return "\n".join(out)


def _render_flows_html(flows: Any) -> str:
    if not isinstance(flows, list):
        return ""
    out = ['<div class="lincoln-flows">']
    for flow in flows:
        if not isinstance(flow, dict):
            continue
        name = flow.get("name", "")
        flow_type = flow.get("type", "")
        mermaid = flow.get("mermaid", "")
        steps = flow.get("steps", [])
        out.append(f'<section class="lincoln-flow"><h3>{_html_attr(str(name))}</h3>')
        if flow_type:
            out.append(f'<p class="lincoln-meta"><strong>类型：</strong>{_html_attr(str(flow_type))}</p>')
        if mermaid:
            out.append(f'<pre class="lincoln-mermaid">{_escape_script_content(str(mermaid))}</pre>')
        if isinstance(steps, list) and steps:
            out.append('<ol class="lincoln-flow-steps">')
            for step in steps:
                out.append(f'<li>{_escape_script_content(str(step))}</li>')
            out.append('</ol>')
        out.append('</section>')
    out.append('</div>')
    return "\n".join(out)


def _render_pages_html(pages: Any) -> str:
    if not isinstance(pages, list):
        return ""
    columns = [
        ("id", "ID"),
        ("title", "标题"),
        ("path", "路径"),
        ("links", "关联"),
        ("notes", "备注"),
    ]
    return _render_table(pages, columns)


def _render_apis_html(apis: Any) -> str:
    if not isinstance(apis, list):
        return ""
    columns = [
        ("name", "名称"),
        ("method", "方法"),
        ("endpoint", "端点"),
        ("purpose", "用途"),
        ("contract", "契约"),
    ]
    return _render_table(apis, columns)


def _render_fields_html(fields_spec: Any) -> str:
    """Render field specifications, supporting either a list of groups or a flat list."""
    if not isinstance(fields_spec, list):
        return ""
    # If first item has a "fields" key, treat as groups.
    if fields_spec and isinstance(fields_spec[0], dict) and "fields" in fields_spec[0]:
        out = ['<div class="lincoln-field-groups">']
        for group in fields_spec:
            if not isinstance(group, dict):
                continue
            title = group.get("title", "")
            fields = group.get("fields", [])
            out.append(f'<section class="lincoln-field-group"><h3>{_html_attr(str(title))}</h3>')
            out.append(_render_table(fields, [
                ("name", "字段名"),
                ("type", "类型"),
                ("required", "必填"),
                ("validation", "校验"),
                ("default", "默认值"),
                ("copy", "文案"),
                ("error", "错误提示"),
                ("source", "来源"),
            ]))
            out.append('</section>')
        out.append('</div>')
        return "\n".join(out)

    return _render_table(fields_spec, [
        ("name", "字段名"),
        ("type", "类型"),
        ("required", "必填"),
        ("validation", "校验"),
        ("default", "默认值"),
        ("copy", "文案"),
        ("error", "错误提示"),
        ("source", "来源"),
    ])


def _data_variables(page_data: dict[str, Any]) -> dict[str, str]:
    """Build placeholder variables from structured page data."""
    variables: dict[str, str] = {}

    # Raw JSON for client-side rendering.
    json_text = json.dumps(page_data, ensure_ascii=False, sort_keys=True)
    variables["PAGE_DATA"] = _escape_script_content(json_text)

    # Pre-rendered HTML fragments.
    variables["SECTIONS_HTML"] = _render_sections_html(page_data.get("sections"))
    variables["STORIES_HTML"] = _render_stories_html(page_data.get("stories"))
    variables["FEATURES_HTML"] = _render_features_html(page_data.get("features"))
    variables["ENTITIES_HTML"] = _render_entities_html(page_data.get("entities"))
    variables["FLOWS_HTML"] = _render_flows_html(page_data.get("flows"))
    variables["PAGES_HTML"] = _render_pages_html(page_data.get("pages"))
    variables["APIS_HTML"] = _render_apis_html(page_data.get("apis"))
    variables["FIELDS_HTML"] = _render_fields_html(page_data.get("fields"))

    return variables


COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def _html_comment_ranges(html: str) -> list[tuple[int, int]]:
    """Return [(start, end), ...] for all HTML comment blocks."""
    return [(m.start(), m.end()) for m in COMMENT_RE.finditer(html)]


def _inside_comment(pos: int, ranges: list[tuple[int, int]]) -> bool:
    return any(start <= pos < end for start, end in ranges)


def _inject_meta(html: str, name: str, content: str) -> str:
    """Add or update a <meta name="..." content="..."> tag in <head>."""
    if not content:
        return html
    tag = f'<meta name="{name}" content="{content}">'
    comment_ranges = _html_comment_ranges(html)

    # Update an existing tag with the same name, if any (skip placeholders inside comments).
    for match in META_RE.finditer(html):
        if match.group(1) == name and not _inside_comment(match.start(), comment_ranges):
            return html[: match.start()] + tag + html[match.end() :]

    # Insert right after <head> (or before </head> if no <head> tag found).
    head_open = re.search(r"<head[^>]*>", html, re.IGNORECASE)
    if head_open:
        insert_at = head_open.end()
        return html[:insert_at] + "\n" + tag + html[insert_at:]
    head_close = re.search(r"</head>", html, re.IGNORECASE)
    if head_close:
        insert_at = head_close.start()
        return html[:insert_at] + tag + "\n" + html[insert_at:]
    return html


def _inject_annotation_metas(html: str, page_data: dict[str, Any]) -> str:
    """Inject portal annotation meta tags from page_data.annotations into <head>."""
    annotations = page_data.get("annotations") if isinstance(page_data, dict) else None
    if not isinstance(annotations, dict):
        return html
    for key, value in annotations.items():
        content = str(value) if value is not None else ""
        if not content:
            continue
        name = key if key.startswith("doc-") else f"doc-{key}"
        html = _inject_meta(html, name, content)
    return html


def _ensure_version_comment(html: str, version: str) -> str:
    """Ensure the HTML contains a <!-- version: vX.Y --> marker."""
    if not version:
        return html
    if VERSION_COMMENT_RE.search(html):
        return html
    # Insert before </body> or append.
    body_close = re.search(r"</body>", html, re.IGNORECASE)
    marker = f"\n<!-- version: {version} -->\n"
    if body_close:
        return html[: body_close.start()] + marker + html[body_close.start() :]
    return html + marker


GLOB_CHARS = frozenset("*?[]")


def _is_glob_pattern(pattern: str) -> bool:
    return any(ch in GLOB_CHARS for ch in pattern)


def _render_stage_batch(stage_id: str, state_file: str | Path | None) -> list[str]:
    """Render all missing artifact pages declared by a stage definition.

    Only exact (non-glob) patterns are rendered automatically. If a matching
    .md file exists next to the target, it is used as the Markdown source.
    Returns the list of rendered target paths.
    """
    stage_data = _load_stage(stage_id)
    runtime = _load_runtime_variables(state_file)
    variables: dict[str, str] = {k: "" for k in RUNTIME_VARIABLES}
    variables.update(runtime)

    raw_templates = stage_data.get("artifact_templates", {}) or {}
    interpolated_templates = {
        _replace_variables(str(pattern), variables): str(template_path)
        for pattern, template_path in raw_templates.items()
    }

    rendered: list[str] = []
    for pattern, template_path in interpolated_templates.items():
        if _is_glob_pattern(pattern):
            print(f"Skipping glob pattern in batch render: {pattern}")
            continue

        target_path = PROJECT_ROOT / pattern
        if target_path.exists():
            continue

        # Look for a matching Markdown file (e.g. design-review.html -> design-review.md).
        md_path = target_path.with_suffix(".md")
        markdown_source = ""
        if md_path.exists():
            markdown_source = md_path.read_text(encoding="utf-8")

        defaults = _derive_defaults(
            markdown_path=md_path if markdown_source else None,
            target=pattern,
            title="",
            nav_label=None,
            nav_group=None,
            version=None,
            uid=None,
            stage_mark=None,
            stage_id=stage_id,
        )

        try:
            html = render_page(
                stage_id=stage_id,
                target=pattern,
                title=defaults["title"],
                nav_label=defaults["nav_label"],
                nav_group=defaults["nav_group"],
                version=defaults["version"],
                uid=defaults["uid"],
                stage_mark=defaults["stage_mark"],
                markdown_source=markdown_source,
                page_data=None,
                extra_variables=None,
                state_file=state_file,
            )
        except Exception as exc:
            print(f"Failed to render {pattern}: {exc}", file=sys.stderr)
            continue

        target_path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(target_path, html)
        print(f"Rendered {target_path}")
        rendered.append(pattern)

    return rendered


PAGE_UID_META_RE = re.compile(r'<meta\s+name="page-uid"', re.IGNORECASE)


def _resolve_meta_uid_kind(template: str, target: str) -> str:
    """Return 'doc-uid' for doc pages, 'page-uid' for prototype pages."""
    if "/prototype/" in target or PAGE_UID_META_RE.search(template):
        return "page-uid"
    return "doc-uid"


def render_page(
    stage_id: str,
    target: str,
    title: str = "",
    nav_label: str = "",
    nav_group: str = "Docs",
    version: str = "",
    uid: str = "",
    stage_mark: str = "",
    markdown_source: str = "",
    page_data: dict[str, Any] | None = None,
    extra_variables: dict[str, str] | None = None,
    state_file: str | Path | None = None,
) -> str:
    """Render a single HTML page and return the rendered text."""
    stage_data = _load_stage(stage_id)

    defaults = _derive_defaults(
        markdown_path=markdown_source if markdown_source else None,
        target=target,
        title=title,
        nav_label=nav_label,
        nav_group=nav_group,
        version=version,
        uid=uid,
        stage_mark=stage_mark,
        stage_id=stage_id,
    )
    title = defaults["title"]
    nav_label = defaults["nav_label"]
    nav_group = defaults["nav_group"]
    version = defaults["version"]
    uid = defaults["uid"]
    stage_mark = defaults["stage_mark"]

    runtime = _load_runtime_variables(state_file)
    variables: dict[str, str] = {k: "" for k in RUNTIME_VARIABLES}
    variables.update(runtime)
    if extra_variables:
        variables.update(extra_variables)

    raw_templates = stage_data.get("artifact_templates", {}) or {}
    interpolated_templates = {
        _replace_variables(str(pattern), variables): str(template_path)
        for pattern, template_path in raw_templates.items()
    }
    target = _replace_variables(target, variables)
    template_path, _ = _resolve_template(interpolated_templates, target)
    template = template_path.read_text(encoding="utf-8")

    # Page-level placeholders.
    variables.update(
        {
            "TITLE": title,
            "NAV_LABEL": nav_label or title,
            "NAV_GROUP": nav_group or "Docs",
            "VERSION": version,
            "UID": uid,
            "STAGE": stage_mark or stage_id,
            "MARKDOWN_SOURCE": _escape_markdown_for_script(markdown_source),
        }
    )

    # Structured data placeholders.
    if page_data:
        variables.update(_data_variables(page_data))
    else:
        for key in DATA_PLACEHOLDERS:
            variables.setdefault(key, "")

    html = _replace_variables(template, variables)

    # Auto-fill meta tags that the portal index relies on.
    html = _inject_meta(html, "doc-title", title or nav_label)
    html = _inject_meta(html, "nav-label", nav_label or title)
    html = _inject_meta(html, "nav-group", nav_group or "Docs")
    html = _inject_meta(html, "doc-version", version)
    uid_kind = _resolve_meta_uid_kind(template, target)
    html = _inject_meta(html, uid_kind, uid)

    # Inject portal annotation metas from structured page data so the portal
    # index and right-panel annotations are present in the static HTML source.
    html = _inject_annotation_metas(html, page_data or {})

    html = _ensure_version_comment(html, version)

    return html


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render a Lincoln HTML page from a stage template."
    )
    parser.add_argument("--stage", required=True, help="Stage ID (e.g. clarify)")
    parser.add_argument(
        "--target", default="", help="Repo-relative target artifact path"
    )
    parser.add_argument("--title", default="", help="Page title")
    parser.add_argument("--nav-label", default=None, help="Navigation label (defaults to title)")
    parser.add_argument("--nav-group", default=None, help="Navigation group (defaults to Docs)")
    parser.add_argument("--version", default=None, help="Version marker (defaults to v1.0 or from Markdown)")
    parser.add_argument("--uid", default=None, help="Stable page/doc UID (defaults to target filename)")
    parser.add_argument(
        "--stage-mark", default=None, help="Stage label to display (defaults to stage ID)"
    )
    parser.add_argument(
        "--markdown",
        default="",
        help="Path to a Markdown file to inject as the doc page source",
    )
    parser.add_argument(
        "--data",
        default="",
        help="Path to a YAML or JSON file with structured page data",
    )
    parser.add_argument(
        "--set",
        action="append",
        default=[],
        help="Extra variable in key=value form (can be repeated)",
    )
    parser.add_argument(
        "--state-file",
        default=None,
        help="Path to workflow-stage.yaml (defaults to canonical discovery)",
    )
    parser.add_argument(
        "--render-stage",
        action="store_true",
        help="Render all missing artifact pages declared by --stage (requires --state-file)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print rendered HTML to stdout instead of writing",
    )
    return parser


def _parse_extra(variables: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in variables:
        if "=" not in item:
            raise ValueError(f"--set value must be key=value: {item}")
        key, value = item.split("=", 1)
        out[key] = value
    return out


def main(argv: list[str] | None = None) -> int:
    parser = _build_argument_parser()
    args = parser.parse_args(argv)

    if args.render_stage:
        if not args.state_file:
            print("--render-stage requires --state-file", file=sys.stderr)
            return 1
        try:
            _render_stage_batch(args.stage, args.state_file)
        except Exception as exc:
            print(f"Batch render failed: {exc}", file=sys.stderr)
            return 1
        return 0

    if not args.target:
        print("--target is required unless using --render-stage", file=sys.stderr)
        return 1

    markdown_source = ""
    if args.markdown:
        md_path = PROJECT_ROOT / args.markdown
        if not md_path.exists():
            print(f"Markdown source not found: {md_path}", file=sys.stderr)
            return 1
        markdown_source = md_path.read_text(encoding="utf-8")

    page_data: dict[str, Any] | None = None
    if args.data:
        data_path = PROJECT_ROOT / args.data
        if not data_path.exists():
            print(f"Data file not found: {data_path}", file=sys.stderr)
            return 1
        try:
            page_data = _load_page_data(data_path)
        except Exception as exc:
            print(f"Failed to load data file: {exc}", file=sys.stderr)
            return 1

    extra = _parse_extra(args.set)

    try:
        html = render_page(
            stage_id=args.stage,
            target=args.target,
            title=args.title,
            nav_label=args.nav_label,
            nav_group=args.nav_group,
            version=args.version,
            uid=args.uid,
            stage_mark=args.stage_mark,
            markdown_source=markdown_source,
            page_data=page_data,
            extra_variables=extra,
            state_file=args.state_file,
        )
    except Exception as exc:
        print(f"Render failed: {exc}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(html)
        return 0

    target_path = PROJECT_ROOT / args.target
    target_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(target_path, html)
    print(f"Rendered {target_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
