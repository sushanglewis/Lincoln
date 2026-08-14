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
    <!-- Markdown will be rendered here from #docSource -->
</div>

<script type="text/markdown" id="docSource">
<!-- version: {VERSION} -->

{MARKDOWN_SOURCE}
</script>

<script src="../../assets/app.js"></script>
<script src="../../assets/mermaid.min.js"></script>
<script>
(function () {
    'use strict';

    var THEME_KEY = 'lincoln-theme';

    function getQueryTheme() {
        var m = window.location.search.match(/[?&]theme=(light|dark)(?:&|$)/);
        return m ? m[1] : null;
    }

    function getStoredTheme() {
        try {
            return localStorage.getItem(THEME_KEY);
        } catch (err) {
            return null;
        }
    }

    function setStoredTheme(theme) {
        try {
            localStorage.setItem(THEME_KEY, theme);
        } catch (err) {
            // ignore
        }
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
            if (window.parent) {
                window.parent.postMessage({ type: 'lincoln-theme-ready' }, '*');
            }
        });
    }

    function escapeHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }

    function inlineRender(str) {
        return escapeHtml(str)
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>')
            .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
            .replace(/\*([^*]+)\*/g, '<em>$1</em>');
    }

    function renderMarkdown(src) {
        var lines = src.replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n');
        var html = '';
        var inCode = false;
        var codeLang = '';
        var codeBuffer = [];
        var inTable = false;
        var tableBuffer = [];

        function flushCode() {
            if (!inCode) return;
            var body = escapeHtml(codeBuffer.join('\n'));
            if (codeLang === 'mermaid') {
                html += '<pre class="lincoln-mermaid">' + body + '</pre>\n';
            } else {
                html += '<pre><code class="language-' + (codeLang || 'text') + '">' + body + '</code></pre>\n';
            }
            inCode = false;
            codeLang = '';
            codeBuffer = [];
        }

        function flushTable() {
            if (!inTable || tableBuffer.length < 2) {
                inTable = false;
                tableBuffer = [];
                return;
            }
            html += '<table class="lincoln-data-table">\n<thead><tr>';
            var headers = tableBuffer[0].split('|').map(function (s) { return s.trim(); }).filter(Boolean);
            headers.forEach(function (h) { html += '<th>' + inlineRender(h) + '</th>'; });
            html += '</tr></thead>\n<tbody>\n';
            for (var i = 2; i < tableBuffer.length; i++) {
                html += '<tr>';
                var cells = tableBuffer[i].split('|').map(function (s) { return s.trim(); }).filter(Boolean);
                cells.forEach(function (c) { html += '<td>' + inlineRender(c) + '</td>'; });
                html += '</tr>\n';
            }
            html += '</tbody>\n</table>\n';
            inTable = false;
            tableBuffer = [];
        }

        function blockRender(line) {
            if (/^#{1,6}\s+/.test(line)) {
                var level = line.match(/^(#{1,6})\s+/)[1].length;
                var text = line.replace(/^#{1,6}\s+/, '');
                return '<h' + level + '>' + inlineRender(text) + '</h' + level + '>';
            }
            if (/^\s*>\s*(.*)/.test(line)) {
                return '<blockquote><p>' + inlineRender(line.replace(/^\s*>\s*/, '')) + '</p></blockquote>';
            }
            return '<p>' + inlineRender(line) + '</p>';
        }

        function listMarker(line) {
            var unordered = line.match(/^(\s*)[-*+]\s+(.*)$/);
            if (unordered) {
                return { indent: unordered[1].length, type: 'ul', content: unordered[2] };
            }
            var ordered = line.match(/^(\s*)\d+\.\s+(.*)$/);
            if (ordered) {
                return { indent: ordered[1].length, type: 'ol', content: ordered[2] };
            }
            return null;
        }

        var listStack = [];

        function closeLists(targetDepth) {
            targetDepth = targetDepth || 0;
            while (listStack.length > targetDepth) {
                var last = listStack.pop();
                html += '</li></' + last.type + '>\n';
            }
        }

        function openList(type, depth) {
            closeLists(depth);
            html += '<' + type + '>\n';
            listStack.push({ type: type, depth: depth });
        }

        function renderListItem(marker) {
            var depth = marker.indent;
            var type = marker.type;
            var i = listStack.length - 1;
            while (i >= 0 && listStack[i].depth > depth) {
                i--;
            }
            if (i < 0 || listStack[i].type !== type || listStack[i].depth !== depth) {
                openList(type, depth);
            } else {
                closeLists(i + 1);
            }
            html += '<li>' + inlineRender(marker.content);
        }

        for (var i = 0; i < lines.length; i++) {
            var line = lines[i];

            if (/^```/.test(line)) {
                if (inCode) {
                    flushCode();
                } else {
                    flushTable();
                    closeLists();
                    inCode = true;
                    codeLang = line.replace(/^```\s*/, '').trim();
                }
                continue;
            }

            if (inCode) {
                codeBuffer.push(line);
                continue;
            }

            if (/^\|/.test(line)) {
                closeLists();
                inTable = true;
                tableBuffer.push(line);
                continue;
            } else {
                flushTable();
            }

            if (/^\s*$/.test(line)) {
                closeLists();
                continue;
            }

            var marker = listMarker(line);
            if (marker) {
                renderListItem(marker);
                continue;
            }

            closeLists();
            html += blockRender(line) + '\n';
        }

        flushCode();
        flushTable();
        closeLists();

        return html;
    }

    function initMermaid() {
        if (typeof window.mermaid === 'undefined') return;
        var theme = document.documentElement.getAttribute('data-theme') || 'light';
        try {
            window.mermaid.initialize({
                startOnLoad: false,
                theme: theme === 'dark' ? 'dark' : 'default'
            });
        } catch (err) {
            // ignore init errors
        }
        var nodes = document.querySelectorAll('.lincoln-mermaid');
        if (!nodes.length) return;
        try {
            window.mermaid.run({ querySelector: '.lincoln-mermaid' });
        } catch (err) {
            // Fallback for older Mermaid versions
            try {
                window.mermaid.init(undefined, nodes);
            } catch (e2) {
                // ignore
            }
        }
    }

    initTheme();

    var sourceEl = document.getElementById('docSource');
    var contentEl = document.getElementById('docContent');
    if (sourceEl && contentEl) {
        var src = sourceEl.textContent;
        contentEl.innerHTML = renderMarkdown(src);
        initMermaid();
    }
})();
</script>
</body>
</html>
