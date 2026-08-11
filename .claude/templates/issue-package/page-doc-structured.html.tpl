<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="doc-title" content="{TITLE}">
<meta name="nav-label" content="{NAV_LABEL}">
<meta name="nav-group" content="{NAV_GROUP}">
<meta name="doc-version" content="{VERSION}">
<meta name="doc-uid" content="{UID}">
<!--
  Optional portal annotations (right panel):
  这些 meta 可通过 pageData.annotations 自动注入；也可手工在此维护。
  <meta name="doc-purpose" content="一句话功能说明">
  <meta name="doc-layout" content="顶部导航 | 左侧边栏 | 主内容区">
  <meta name="doc-fields" content="字段A — 类型 — 必填 — 说明 | 字段B — 说明">
  <meta name="doc-stories" content="作为...我想要...以便... | ...">
  <meta name="doc-rules" content="点击提交后校验输入 | 未登录跳转登录页">
  <meta name="doc-boundaries" content="空列表展示占位图 | 搜索无结果">
  <meta name="doc-exceptions" content="网络断开显示重试 | 无权限提示">
  <meta name="doc-refs" content="PRD #3 | flows.html">
-->
<title>{TITLE}</title>
<!-- Asset paths assume this page lives at pages/docs/*.html (depth 2). Adjust if placed elsewhere. -->
<link rel="stylesheet" href="../../assets/style.css">
<style>
.lincoln-intro { margin-bottom: 1.5rem; color: var(--text-secondary); }
.lincoln-section { margin-bottom: 2rem; }
.lincoln-section-title { margin-top: 0; }
.lincoln-section-body { line-height: 1.7; }
.lincoln-data-table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
.lincoln-data-table th, .lincoln-data-table td { border: 1px solid var(--border); padding: 0.5rem; text-align: left; }
.lincoln-data-table th { background: var(--surface); }
.lincoln-entity, .lincoln-flow, .lincoln-field-group { margin-bottom: 2rem; }
.lincoln-meta { color: var(--text-secondary); font-size: 0.95rem; }
.lincoln-mermaid { background: var(--surface); padding: 1rem; border-radius: 6px; overflow-x: auto; }
.lincoln-flow-steps li { margin-bottom: 0.5rem; }
</style>
</head>
<body class="doc-page" data-page-uid="{UID}">

<header class="doc-header">
    <h1 data-uid="{UID}-h1">{TITLE}</h1>
    <div class="doc-meta">
        <span class="doc-version">{VERSION}</span>
        <span class="doc-stage">阶段: {STAGE}</span>
    </div>
</header>

<div class="doc-content" id="docContent">
    <div class="lincoln-intro" id="docIntro"></div>
    <div id="docStructured"></div>

    <!-- Optional free-form Markdown supplement -->
    <div id="docMarkdown"></div>
</div>

<script type="application/json" id="pageData">
{PAGE_DATA}
</script>

<script type="text/markdown" id="docSource">
<!-- version: {VERSION} -->

{MARKDOWN_SOURCE}
</script>

<script src="../../assets/app.js"></script>
<script>
(function () {
    'use strict';

    var THEME_KEY = 'lincoln-theme';

    function getQueryTheme() {
        var m = window.location.search.match(/[?&]theme=(light|dark)(?:&|$)/);
        return m ? m[1] : null;
    }

    function getStoredTheme() {
        try { return localStorage.getItem(THEME_KEY); } catch (err) { return null; }
    }

    function setStoredTheme(theme) {
        try { localStorage.setItem(THEME_KEY, theme); } catch (err) {}
    }

    function applyTheme(theme) {
        if (theme !== 'light' && theme !== 'dark') return;
        document.documentElement.setAttribute('data-theme', theme);
        setStoredTheme(theme);
    }

    function initTheme() {
        var theme = getQueryTheme() || getStoredTheme() || 'light';
        applyTheme(theme);
        window.addEventListener('message', function (e) {
            var data = e.data || {};
            if (data.type === 'lincoln-theme' && (data.theme === 'light' || data.theme === 'dark')) {
                applyTheme(data.theme);
            }
        });
        window.addEventListener('load', function () {
            if (window.parent) window.parent.postMessage({ type: 'lincoln-theme-ready' }, '*');
        });
    }

    initTheme();

    function loadData() {
        var el = document.getElementById('pageData');
        if (!el) return {};
        try { return JSON.parse(el.textContent) || {}; } catch (e) { return {}; }
    }

    function injectAnnotationMetas(data) {
        var annotations = data.annotations || {};
        var head = document.head;
        Object.keys(annotations).forEach(function (key) {
            var name = key.indexOf('doc-') === 0 ? key : 'doc-' + key;
            var value = annotations[key];
            var existing = document.querySelector('meta[name="' + name + '"]');
            if (existing) {
                existing.setAttribute('content', value);
            } else {
                var meta = document.createElement('meta');
                meta.setAttribute('name', name);
                meta.setAttribute('content', value);
                head.appendChild(meta);
            }
        });
    }

    function escapeHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }

    function renderTable(rows, columns) {
        if (!Array.isArray(rows) || !rows.length) return '';
        var html = '<table class="lincoln-data-table"><thead><tr>';
        columns.forEach(function (col) { html += '<th>' + escapeHtml(col.label) + '</th>'; });
        html += '</tr></thead><tbody>';
        rows.forEach(function (row) {
            html += '<tr>';
            columns.forEach(function (col) {
                var value = (row && row[col.key]) || '';
                html += '<td>' + escapeHtml(String(value)) + '</td>';
            });
            html += '</tr>';
        });
        html += '</tbody></table>';
        return html;
    }

    var RENDERERS = {
        intro: function (value) {
            if (!value) return '';
            return '<p class="lincoln-intro">' + escapeHtml(String(value)) + '</p>';
        },
        sections: function (sections) {
            if (!Array.isArray(sections)) return '';
            return sections.map(function (s) {
                return '<section class="lincoln-section">' +
                    (s.title ? '<h2 class="lincoln-section-title">' + escapeHtml(s.title) + '</h2>' : '') +
                    '<div class="lincoln-section-body">' + escapeHtml(String(s.content || '')).replace(/\n/g, '<br>') + '</div>' +
                    '</section>';
            }).join('\n');
        },
        stories: function (stories) {
            return renderTable(stories, [
                {key: 'who', label: '角色'},
                {key: 'want', label: '想要'},
                {key: 'so', label: '以便'},
                {key: 'acceptance', label: '验收标准'},
                {key: 'source', label: '来源'}
            ]);
        },
        features: function (features) {
            return renderTable(features, [
                {key: 'id', label: 'ID'},
                {key: 'title', label: '功能'},
                {key: 'priority', label: '优先级'},
                {key: 'acceptance', label: '验收标准'},
                {key: 'source', label: '来源'}
            ]);
        },
        entities: function (entities) {
            if (!Array.isArray(entities)) return '';
            return entities.map(function (e) {
                var html = '<section class="lincoln-entity"><h3>' + escapeHtml(String(e.name || '')) + '</h3>';
                if (e.constraints) html += '<p class="lincoln-meta"><strong>约束：</strong>' + escapeHtml(String(e.constraints)) + '</p>';
                if (e.states) html += '<p class="lincoln-meta"><strong>状态：</strong>' + escapeHtml(String(e.states)) + '</p>';
                if (Array.isArray(e.fields) && e.fields.length) {
                    html += renderTable(e.fields, [
                        {key: 'name', label: '字段名'},
                        {key: 'type', label: '类型'},
                        {key: 'required', label: '必填'},
                        {key: 'description', label: '说明'},
                        {key: 'source', label: '来源'}
                    ]);
                }
                html += '</section>';
                return html;
            }).join('\n');
        },
        flows: function (flows) {
            if (!Array.isArray(flows)) return '';
            return flows.map(function (f) {
                var html = '<section class="lincoln-flow"><h3>' + escapeHtml(String(f.name || '')) + '</h3>';
                if (f.type) html += '<p class="lincoln-meta"><strong>类型：</strong>' + escapeHtml(String(f.type)) + '</p>';
                if (f.mermaid) html += '<pre class="lincoln-mermaid">' + escapeHtml(String(f.mermaid)) + '</pre>';
                if (Array.isArray(f.steps) && f.steps.length) {
                    html += '<ol class="lincoln-flow-steps">';
                    f.steps.forEach(function (step) { html += '<li>' + escapeHtml(String(step)) + '</li>'; });
                    html += '</ol>';
                }
                html += '</section>';
                return html;
            }).join('\n');
        },
        pages: function (pages) {
            return renderTable(pages, [
                {key: 'id', label: 'ID'},
                {key: 'title', label: '标题'},
                {key: 'path', label: '路径'},
                {key: 'links', label: '关联'},
                {key: 'notes', label: '备注'}
            ]);
        },
        apis: function (apis) {
            return renderTable(apis, [
                {key: 'name', label: '名称'},
                {key: 'method', label: '方法'},
                {key: 'endpoint', label: '端点'},
                {key: 'purpose', label: '用途'},
                {key: 'contract', label: '契约'}
            ]);
        },
        fields: function (fields) {
            if (!Array.isArray(fields)) return '';
            // Group support
            if (fields.length && fields[0] && Array.isArray(fields[0].fields)) {
                return fields.map(function (g) {
                    var html = '<section class="lincoln-field-group"><h3>' + escapeHtml(String(g.title || '')) + '</h3>';
                    html += renderTable(g.fields, [
                        {key: 'name', label: '字段名'},
                        {key: 'type', label: '类型'},
                        {key: 'required', label: '必填'},
                        {key: 'validation', label: '校验'},
                        {key: 'default', label: '默认值'},
                        {key: 'copy', label: '文案'},
                        {key: 'error', label: '错误提示'},
                        {key: 'source', label: '来源'}
                    ]);
                    html += '</section>';
                    return html;
                }).join('\n');
            }
            return renderTable(fields, [
                {key: 'name', label: '字段名'},
                {key: 'type', label: '类型'},
                {key: 'required', label: '必填'},
                {key: 'validation', label: '校验'},
                {key: 'default', label: '默认值'},
                {key: 'copy', label: '文案'},
                {key: 'error', label: '错误提示'},
                {key: 'source', label: '来源'}
            ]);
        }
    };

    var ORDER = ['intro', 'sections', 'stories', 'features', 'entities', 'flows', 'pages', 'apis', 'fields'];

    function renderStructured() {
        var data = loadData();
        injectAnnotationMetas(data);

        var introEl = document.getElementById('docIntro');
        if (introEl && data.intro) introEl.innerHTML = RENDERERS.intro(data.intro);

        var container = document.getElementById('docStructured');
        if (!container) return;
        var html = '';
        ORDER.forEach(function (key) {
            if (data[key] && RENDERERS[key]) {
                html += RENDERERS[key](data[key]);
            }
        });
        container.innerHTML = html;
    }

    function renderMarkdownFallback() {
        var sourceEl = document.getElementById('docSource');
        var contentEl = document.getElementById('docMarkdown');
        if (!sourceEl || !contentEl) return;
        var src = sourceEl.textContent.trim();
        if (!src || src === '<!-- version: {VERSION} -->') return;
        // Minimal markdown renderer for headings, bold, italic, code, links, lists, blockquotes.
        function escapeHtml(str) {
            return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        }
        function inlineRender(str) {
            return escapeHtml(str)
                .replace(/`([^`]+)`/g, '<code>$1</code>')
                .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>')
                .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
                .replace(/\*([^*]+)\*/g, '<em>$1</em>');
        }
        function blockRender(line) {
            var m;
            if ((m = line.match(/^(#{1,6})\s+(.*)/))) return '<h' + m[1].length + '>' + inlineRender(m[2]) + '</h' + m[1].length + '>';
            if ((m = line.match(/^\s*\>\s*(.*)/))) return '<blockquote><p>' + inlineRender(m[1]) + '</p></blockquote>';
            if ((m = line.match(/^\s*[-*+]\s+(.*)/))) return '<li>' + inlineRender(m[1]) + '</li>';
            if ((m = line.match(/^\s*\d+\.\s+(.*)/))) return '<li>' + inlineRender(m[1]) + '</li>';
            return '<p>' + inlineRender(line) + '</p>';
        }
        var lines = src.replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n');
        var out = '';
        var i = 0;
        while (i < lines.length) {
            var line = lines[i];
            if (/^```/.test(line)) {
                var lang = line.replace(/^```\s*/, '').trim();
                var buf = [];
                i++;
                while (i < lines.length && !/^```/.test(lines[i])) { buf.push(lines[i]); i++; }
                out += '<pre><code class="language-' + (lang || 'text') + '">' + escapeHtml(buf.join('\n')) + '</code></pre>\n';
                i++;
                continue;
            }
            if (/^\s*$/.test(line)) { i++; continue; }
            out += blockRender(line) + '\n';
            i++;
        }
        out = out.replace(/(<li>[^<]*<\/li>\n)+/g, function (match) {
            return '<ul>\n' + match + '</ul>\n';
        });
        contentEl.innerHTML = '<hr><h2>补充说明</h2>' + out;
    }

    renderStructured();
    renderMarkdownFallback();
})();
</script>
</body>
</html>
