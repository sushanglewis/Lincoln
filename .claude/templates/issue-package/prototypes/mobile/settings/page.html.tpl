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
<!-- Asset paths assume this page lives at pages/prototype/mobile/settings/*.html (depth 4). -->
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

    // ---------- Mobile settings content ----------
    var items = [
        { label: '账号与安全', uid: 'account' },
        { label: '通知设置', uid: 'notifications' },
        { label: '隐私', uid: 'privacy' },
        { label: '关于', uid: 'about' }
    ];
    var list = '';
    items.forEach(function (item) {
        list += '<div style="display:flex;justify-content:space-between;align-items:center;padding:14px 0;border-bottom:1px solid var(--border)" data-uid="{UID}-item-' + item.uid + '" onclick="location.href=\'../profile/page.html\'">'
            + '<span data-uid="{UID}-item-' + item.uid + '-label">' + item.label + '</span>'
            + '<span style="color:var(--text-3)">></span>'
            + '</div>';
    });

    var main = '<div style="padding:0 14px" data-uid="{UID}-list">'
        + list
        + '</div>';

    var content = ui.frameMobile(main, { active: 'settings', base: '../' });
    LincolnPrototype.proto.mount(content);
})();
</script>
</body>
</html>
