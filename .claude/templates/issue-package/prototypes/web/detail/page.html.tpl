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
<!-- Asset paths assume this page lives at pages/prototype/web/detail/*.html (depth 4). -->
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

    LincolnPrototype.data.appName = '{TITLE}';

    var ui = LincolnPrototype.ui;

    // ---------- Detail content ----------
    var detail = '<div class="proto-frame" style="max-width:640px;margin:0 auto;padding:24px" data-uid="{UID}-detail">'
        + '<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:20px" data-uid="{UID}-header">'
        + '<div>'
        + '<h2 style="margin:0 0 6px" data-uid="{UID}-title">示例项目 1</h2>'
        + '<div style="font-size:12px;color:var(--text-3)" data-uid="{UID}-meta">创建于 2026-07-31 · 负责人：张三</div>'
        + '</div>'
        + '<span class="p1-tag" data-uid="{UID}-status">进行中</span>'
        + '</div>'
        + '<p style="line-height:1.7;color:var(--text-2)" data-uid="{UID}-desc">这里是详情页面的描述内容。可以包含多行文本，展示条目的完整信息。</p>'
        + '<div style="display:flex;gap:10px;margin-top:24px" data-uid="{UID}-actions">'
        + '<a class="btn default" href="../list/page.html" data-uid="{UID}-btn-back">返回列表</a>'
        + '<a class="btn primary" href="../form/page.html" data-uid="{UID}-btn-edit">编辑</a>'
        + '</div>'
        + '</div>';

    var content = ui.frameWeb(detail, { active: 'detail', base: '../' });
    LincolnPrototype.proto.mount(content);
})();
</script>
</body>
</html>
