<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="doc-title" content="{TITLE}">
<meta name="nav-group" content="{NAV_GROUP}">
<meta name="page-uid" content="{UID}">
<meta name="prototype-base" content="../../../../">
<title>{TITLE}</title>
<!-- Asset paths assume this page lives at pages/prototype/mobile/profile/*.html (depth 4). -->
<link rel="stylesheet" href="../../../../assets/prototype.css">
</head>
<body class="proto-page" data-page-uid="{UID}">

<!--
  Variables:
  {TITLE}     - page title shown in the portal window title
  {NAV_GROUP} - group name used by the portal (e.g. Mobile)
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

    // ---------- Mobile profile content ----------
    var main = '<div style="padding:24px 14px;text-align:center" data-uid="{UID}-profile">'
        + '<div style="width:72px;height:72px;border-radius:50%;background:var(--brand);margin:0 auto 16px;display:flex;align-items:center;justify-content:center;color:#fff;font-size:28px;font-weight:700" data-uid="{UID}-avatar">用</div>'
        + '<h3 style="margin:0 0 6px" data-uid="{UID}-name">用户名</h3>'
        + '<div style="font-size:13px;color:var(--text-3);margin-bottom:24px" data-uid="{UID}-bio">产品 · 设计 · 研发协作平台</div>'
        + '<a class="btn primary" href="../home/page.html" style="display:inline-block" data-uid="{UID}-btn-home">返回首页</a>'
        + '</div>';

    var content = ui.frameMobile(main, { active: 'profile', base: '../' });
    LincolnPrototype.proto.mount(content);
})();
</script>
</body>
</html>
