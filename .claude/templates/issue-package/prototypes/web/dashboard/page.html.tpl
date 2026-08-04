<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="doc-title" content="{TITLE}">
<meta name="nav-group" content="{NAV_GROUP}">
<meta name="page-uid" content="{UID}">
<meta name="prototype-base" content="../../../../">
<title>{TITLE}</title>
<!-- Asset paths assume this page lives at pages/prototype/web/dashboard/*.html (depth 4). -->
<link rel="stylesheet" href="../../../../assets/prototype.css">
</head>
<body class="proto-page" data-page-uid="{UID}">

<!--
  Variables:
  {TITLE}     - page title shown in the portal window title
  {NAV_GROUP} - group name used by the portal (e.g. Web)
  {UID}       - stable page uid
-->

<div class="window full" id="win"></div>

<script src="../../../../assets/prototype.js"></script>
<script>
(function () {
    'use strict';

    // Theme sync with portal
    var THEME_KEY = 'lincoln-theme';
    function applyTheme(theme) {
        if (theme === 'light' || theme === 'dark') {
            document.documentElement.setAttribute('data-theme', theme);
            try { localStorage.setItem(THEME_KEY, theme); } catch (e) {}
        }
    }
    var m = window.location.search.match(/[?&]theme=(light|dark)(?:&|$)/);
    applyTheme(m ? m[1] : (function () { try { return localStorage.getItem(THEME_KEY); } catch (e) { return null; } })() || 'light');
    window.addEventListener('message', function (e) { var d = e.data || {}; if (d.type === 'lincoln-theme') applyTheme(d.theme); });
    window.addEventListener('load', function () { if (window.parent) window.parent.postMessage({ type: 'lincoln-theme-ready' }, '*'); });

    // Override demo data for this page
    LincolnPrototype.data.appName = '{TITLE}';

    var ui = LincolnPrototype.ui;

    // ---------- Dashboard content ----------
    var main = '<div style="display:flex;flex-direction:column;gap:16px" data-uid="{UID}-content">'
        + '<div style="display:flex;justify-content:space-between;align-items:center" data-uid="{UID}-header">'
        + '<h2 style="margin:0" data-uid="{UID}-title">概览</h2>'
        + '<button class="btn primary" data-uid="{UID}-btn-create">新建</button>'
        + '</div>'
        + '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px" data-uid="{UID}-cards">'
        + '<div class="proto-frame" style="min-height:120px;padding:16px" data-uid="{UID}-card-1"><div style="font-size:24px;font-weight:700" data-uid="{UID}-metric-1">128</div><div style="color:var(--text-3)">总条目</div></div>'
        + '<div class="proto-frame" style="min-height:120px;padding:16px" data-uid="{UID}-card-2"><div style="font-size:24px;font-weight:700" data-uid="{UID}-metric-2">12</div><div style="color:var(--text-3)">待处理</div></div>'
        + '<div class="proto-frame" style="min-height:120px;padding:16px" data-uid="{UID}-card-3"><div style="font-size:24px;font-weight:700" data-uid="{UID}-metric-3">98%</div><div style="color:var(--text-3)">完成率</div></div>'
        + '</div>'
        + '<div class="proto-frame" style="min-height:200px;padding:16px;display:flex;align-items:center;justify-content:center" data-uid="{UID}-chart"><div style="color:var(--text-3)">图表占位</div></div>'
        + '</div>';

    var content = ui.frameWeb(main, { active: 'dashboard', base: '../' });
    LincolnPrototype.proto.mount(content);
})();
</script>
</body>
</html>
