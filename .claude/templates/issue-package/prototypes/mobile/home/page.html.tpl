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
<!-- Asset paths assume this page lives at pages/prototype/mobile/home/*.html (depth 4). -->
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

    // ---------- Mobile home content ----------
    var cards = '';
    for (var i = 1; i <= 4; i++) {
        cards += '<div class="proto-frame" style="padding:14px;margin-bottom:10px" data-uid="{UID}-card-' + i + '" onclick="location.href=\'../chat/page.html\'">'
            + '<div style="font-weight:600;margin-bottom:4px" data-uid="{UID}-card-' + i + '-title">动态 ' + i + '</div>'
            + '<div style="font-size:12px;color:var(--text-3)" data-uid="{UID}-card-' + i + '-desc">点击查看详情与聊天入口</div>'
            + '</div>';
    }

    var main = '<div style="padding:10px" data-uid="{UID}-content">'
        + cards
        + '</div>';

    var content = ui.frameMobile(main, { active: 'home', base: '../' });
    LincolnPrototype.proto.mount(content);
})();
</script>
</body>
</html>
