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
  Machine-readable metas consumed by the portal index (lincoln_index.py).
  Page explanations live in the Markdown body or, for prototypes, in
  numbered on-page hotspots — not in meta tags.
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
<script src="../../assets/marked.min.js"></script>
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

    function convertMermaidBlocks(root) {
        var blocks = root.querySelectorAll('pre code.language-mermaid');
        blocks.forEach(function (code) {
            var pre = code.parentNode;
            var container = document.createElement('pre');
            container.className = 'lincoln-mermaid';
            container.textContent = code.textContent;
            pre.parentNode.replaceChild(container, pre);
        });
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
        var html = '';
        if (window.marked) {
            try {
                window.marked.setOptions({ gfm: true, breaks: false });
                html = window.marked.parse(src);
            } catch (err) {
                html = '';
            }
        }
        contentEl.innerHTML = html || ('<pre>' + escapeHtml(src) + '</pre>');
        convertMermaidBlocks(contentEl);
        initMermaid();
    }
})();
</script>
</body>
</html>
