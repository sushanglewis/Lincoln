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
<!-- Asset paths assume this page lives at pages/prototype/web/form/*.html (depth 4). -->
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

    // ---------- Form content ----------
    var form = '<div class="proto-frame" style="max-width:640px;margin:0 auto;padding:24px" data-uid="{UID}-form">'
        + '<h2 style="margin:0 0 20px" data-uid="{UID}-title">新建条目</h2>'
        + '<div class="field" data-uid="{UID}-field-name">'
        + '<label>名称</label>'
        + '<input type="text" placeholder="请输入名称" data-uid="{UID}-input-name">'
        + '</div>'
        + '<div class="field" data-uid="{UID}-field-desc">'
        + '<label>描述</label>'
        + '<input type="text" placeholder="请输入描述" data-uid="{UID}-input-desc">'
        + '</div>'
        + '<div class="field" data-uid="{UID}-field-owner">'
        + '<label>负责人</label>'
        + '<input type="text" placeholder="请选择负责人" data-uid="{UID}-input-owner">'
        + '</div>'
        + '<div style="display:flex;justify-content:flex-end;gap:10px;margin-top:24px" data-uid="{UID}-actions">'
        + '<a class="btn default" href="../list/page.html" data-uid="{UID}-btn-cancel">取消</a>'
        + '<button class="btn primary" data-uid="{UID}-btn-submit">提交</button>'
        + '</div>'
        + '</div>';

    var content = ui.frameWeb(form, { active: 'form', base: '../' });
    LincolnPrototype.proto.mount(content);
})();
</script>
</body>
</html>
