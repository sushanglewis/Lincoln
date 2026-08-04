from pathlib import Path

from .conftest import run_validator


def _doc_source(markdown: str) -> str:
    return f'<script type="text/markdown" id="docSource">\n{markdown}\n</script>\n'


def write_prototype_package(root: Path, design_id: str, prototype_approved: bool = False):
    docs = root / "lc-test" / "pages" / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    prototype_dir = root / "lc-test" / "pages" / "prototype"
    prototype_dir.mkdir(parents=True, exist_ok=True)
    (prototype_dir / "index.html").write_text(
        '<meta name="nav-label" content="Index">'
        '<meta name="doc-purpose" content="Index page.">'
        '<meta name="doc-layout" content="Portal index.">'
        '<meta name="doc-fields" content="id — identifier">'
        '<meta name="doc-boundaries" content="Empty package-data fallback">'
        '<meta name="doc-exceptions" content="Missing package data">'
        "prototype",
        encoding="utf-8",
    )

    (docs / "fields.html").write_text(
        _doc_source("# 字段\n## 校验\n## 错误状态\n"), encoding="utf-8"
    )
    ui = docs / "ui-spec.html"
    ui.write_text(
        _doc_source(
            "# UI 规格\n## 界面\n## 交互\n## 状态\n"
            f"{'<!-- prototype-status: approved -->' if prototype_approved else ''}"
        ),
        encoding="utf-8",
    )


def write_tdd_plan(root: Path, design_id: str, ready: bool = False):
    docs = root / "lc-test" / "pages" / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    tdd = docs / "tdd-plan.html"
    tdd.write_text(
        _doc_source(
            "# TDD Plan\n\n"
            "- Source: lc-test/pages/docs/requirements.html\n"
            "- Source: lc-test/pages/docs/design-review.html\n"
            "- Source: lc-test/pages/docs/fields.html\n"
            "- Source: lc-test/pages/docs/ui-spec.html\n"
            "- Source: lc-test/pages/prototype/\n\n"
            "## 验收映射\n## 测试场景\n## 红/绿/重构\n## 任务切片\n## 回归范围\n"
            f"{'<!-- status: ready-for-openspec -->' if ready else ''}"
        ),
        encoding="utf-8",
    )


class TestPrototypeArtifactComplete:
    def test_fails_when_prototype_pen_missing(self, tmp_project, design_id):
        assert run_validator(tmp_project, "prototype_artifact_complete", design_id) == 1

    def test_passes_when_all_artifacts_present(self, tmp_project, design_id):
        write_prototype_package(tmp_project, design_id)
        assert run_validator(tmp_project, "prototype_artifact_complete", design_id) == 0


class TestPrototypeNavLabel:
    def test_fails_when_prototype_page_missing_nav_label(self, tmp_project, design_id):
        write_prototype_package(tmp_project, design_id)
        proto_dir = tmp_project / "lc-test" / "pages" / "prototype"
        (proto_dir / "missing-nav.html").write_text(
            "<html><head><title>No nav label</title></head><body></body></html>", encoding="utf-8"
        )
        assert run_validator(tmp_project, "prototype_artifact_complete", design_id) == 1

    def test_passes_when_all_prototype_pages_have_nav_label(self, tmp_project, design_id):
        write_prototype_package(tmp_project, design_id)
        proto_dir = tmp_project / "lc-test" / "pages" / "prototype"
        (proto_dir / "with-nav.html").write_text(
            '<html><head>'
            '<meta name="nav-label" content="Page">'
            '<meta name="doc-purpose" content="Purpose.">'
            '<meta name="doc-layout" content="Layout.">'
            '<meta name="doc-fields" content="field — desc">'
            '<meta name="doc-boundaries" content="Boundary.">'
            '<meta name="doc-exceptions" content="Exception.">'
            '</head><body></body></html>',
            encoding="utf-8",
        )
        assert run_validator(tmp_project, "prototype_artifact_complete", design_id) == 0


class TestPrototypeTrayCoverage:
    def test_fails_when_app_shell_has_no_tray_page(self, tmp_project, design_id):
        write_prototype_package(tmp_project, design_id)
        app_dir = tmp_project / "lc-test" / "pages" / "prototype" / "app"
        app_dir.mkdir(parents=True, exist_ok=True)
        (app_dir / "main.html").write_text(
            '<html><head><meta name="nav-label" content="Main"></head><body></body></html>',
            encoding="utf-8",
        )
        assert run_validator(tmp_project, "prototype_artifact_complete", design_id) == 1

    def test_passes_when_app_shell_has_tray_page(self, tmp_project, design_id):
        write_prototype_package(tmp_project, design_id)
        tray_dir = tmp_project / "lc-test" / "pages" / "prototype" / "app" / "tray"
        tray_dir.mkdir(parents=True, exist_ok=True)
        (tray_dir / "default.html").write_text(
            '<html><head>'
            '<meta name="nav-label" content="Tray">'
            '<meta name="doc-purpose" content="Tray state.">'
            '<meta name="doc-layout" content="Menu bar.">'
            '<meta name="doc-fields" content="badge — count">'
            '<meta name="doc-boundaries" content="No unread.">'
            '<meta name="doc-exceptions" content="Dismiss.">'
            '</head>'
            '<body><script>window.parent.postMessage({type:"lincoln-tray-state"}, "*");</script></body></html>',
            encoding="utf-8",
        )
        assert run_validator(tmp_project, "prototype_artifact_complete", design_id) == 0

    def test_fails_when_tray_page_does_not_post_message(self, tmp_project, design_id):
        write_prototype_package(tmp_project, design_id)
        tray_dir = tmp_project / "lc-test" / "pages" / "prototype" / "app" / "tray"
        tray_dir.mkdir(parents=True, exist_ok=True)
        (tray_dir / "default.html").write_text(
            '<html><head><meta name="nav-label" content="Tray"></head><body></body></html>',
            encoding="utf-8",
        )
        assert run_validator(tmp_project, "prototype_artifact_complete", design_id) == 1


class TestPrototypeAnnotationCompleteness:
    def test_fails_when_annotation_meta_missing(self, tmp_project, design_id):
        write_prototype_package(tmp_project, design_id)
        proto_dir = tmp_project / "lc-test" / "pages" / "prototype"
        (proto_dir / "incomplete.html").write_text(
            '<html><head><meta name="nav-label" content="Page"></head><body></body></html>',
            encoding="utf-8",
        )
        assert run_validator(tmp_project, "prototype_artifact_complete", design_id) == 1

    def test_passes_when_annotation_meta_complete(self, tmp_project, design_id):
        write_prototype_package(tmp_project, design_id)
        proto_dir = tmp_project / "lc-test" / "pages" / "prototype"
        (proto_dir / "complete.html").write_text(
            '<html><head>'
            '<meta name="nav-label" content="Page">'
            '<meta name="doc-purpose" content="Purpose.">'
            '<meta name="doc-layout" content="Layout.">'
            '<meta name="doc-fields" content="field — desc">'
            '<meta name="doc-boundaries" content="Boundary.">'
            '<meta name="doc-exceptions" content="Exception.">'
            '</head><body></body></html>',
            encoding="utf-8",
        )
        assert run_validator(tmp_project, "prototype_artifact_complete", design_id) == 0


class TestPrototypeTrayAntiPattern:
    def test_fails_when_app_page_redraws_tray(self, tmp_project, design_id):
        write_prototype_package(tmp_project, design_id)
        app_dir = tmp_project / "lc-test" / "pages" / "prototype" / "app"
        app_dir.mkdir(parents=True, exist_ok=True)
        tray_dir = app_dir / "tray"
        tray_dir.mkdir(parents=True, exist_ok=True)
        (tray_dir / "default.html").write_text(
            '<html><head><meta name="nav-label" content="Tray"></head>'
            '<body><div class="menubar"><div class="tray-icon">T</div></div>'
            '<script>window.parent.postMessage({type:"lincoln-tray-state"}, "*");</script></body></html>',
            encoding="utf-8",
        )
        assert run_validator(tmp_project, "prototype_artifact_complete", design_id) == 1

    def test_fails_when_app_page_uses_bindtray_helper(self, tmp_project, design_id):
        write_prototype_package(tmp_project, design_id)
        app_dir = tmp_project / "lc-test" / "pages" / "prototype" / "app"
        app_dir.mkdir(parents=True, exist_ok=True)
        tray_dir = app_dir / "tray"
        tray_dir.mkdir(parents=True, exist_ok=True)
        (tray_dir / "default.html").write_text(
            '<html><head><meta name="nav-label" content="Tray"></head>'
            '<body><script>LincolnPrototype.proto.bindTray({icon:"#i",panel:"#p"});'
            'window.parent.postMessage({type:"lincoln-tray-state"}, "*");</script></body></html>',
            encoding="utf-8",
        )
        assert run_validator(tmp_project, "prototype_artifact_complete", design_id) == 1


class TestTddPlanComplete:
    def test_fails_when_sections_missing(self, tmp_project, design_id):
        docs = tmp_project / "lc-test" / "pages" / "docs"
        docs.mkdir(parents=True, exist_ok=True)
        (docs / "tdd-plan.html").write_text(_doc_source("# TDD Plan\n"), encoding="utf-8")
        assert run_validator(tmp_project, "tdd_plan_complete", design_id) == 1

    def test_passes_when_all_sections_present(self, tmp_project, design_id):
        write_tdd_plan(tmp_project, design_id)
        assert run_validator(tmp_project, "tdd_plan_complete", design_id) == 0
