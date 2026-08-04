<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="doc-title" content="{TITLE}">
<meta name="nav-group" content="{NAV_GROUP}">
<meta name="doc-version" content="{VERSION}">
<meta name="doc-uid" content="{UID}">
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
            html += '<pre><code class="language-' + (codeLang || 'text') + '">' + escapeHtml(codeBuffer.join('\n')) + '</code></pre>\n';
            inCode = false;
            codeLang = '';
            codeBuffer = [];
        }

        function flushTable() {
            if (!inTable || tableBuffer.length < 2) return;
            html += '<table>\n<thead><tr>';
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

        function blockRender(line) {
            if (/^#{1,6}\s+/.test(line)) {
                var level = line.match(/^(#{1,6})\s+/)[1].length;
                var text = line.replace(/^#{1,6}\s+/, '');
                return '<h' + level + '>' + inlineRender(text) + '</h' + level + '>';
            }
            if (/^\s*>\s*(.*)/.test(line)) {
                return '<blockquote><p>' + inlineRender(line.replace(/^\s*>\s*/, '')) + '</p></blockquote>';
            }
            if (/^\s*[-*+]\s+/.test(line)) {
                return '<li>' + inlineRender(line.replace(/^\s*[-*+]\s+/, '')) + '</li>';
            }
            if (/^\s*\d+\.\s+/.test(line)) {
                return '<li>' + inlineRender(line.replace(/^\s*\d+\.\s+/, '')) + '</li>';
            }
            return '<p>' + inlineRender(line) + '</p>';
        }

        for (var i = 0; i < lines.length; i++) {
            var line = lines[i];

            if (/^```/.test(line)) {
                if (inCode) {
                    flushCode();
                } else {
                    flushTable();
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
                inTable = true;
                tableBuffer.push(line);
                continue;
            } else {
                flushTable();
            }

            if (/^\s*$/.test(line)) {
                continue;
            }

            html += blockRender(line) + '\n';
        }
        flushCode();
        flushTable();

        // Wrap consecutive list items
        html = html.replace(/(<li>[^<]*<\/li>\n)+/g, function (match) {
            return '<ul>\n' + match + '</ul>\n';
        });

        return html;
    }

    initTheme();

    var sourceEl = document.getElementById('docSource');
    var contentEl = document.getElementById('docContent');
    if (sourceEl && contentEl) {
        var src = sourceEl.textContent;
        contentEl.innerHTML = renderMarkdown(src);
    }
})();
</script>
</body>
</html>
