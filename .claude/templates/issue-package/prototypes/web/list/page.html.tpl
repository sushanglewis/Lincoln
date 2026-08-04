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
<!-- Asset paths assume this page lives at pages/prototype/web/list/*.html (depth 4). -->
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

    // ---------- List content ----------
    var toolbar = '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px" data-uid="{UID}-toolbar">'
        + '<div class="field" style="margin:0;width:240px" data-uid="{UID}-search"><input type="text" placeholder="搜索..." data-uid="{UID}-input-search"></div>'
        + '<button class="btn primary" data-uid="{UID}-btn-create">新建</button>'
        + '</div>';

    var rows = '';
    for (var i = 1; i <= 5; i++) {
        rows += '<tr data-uid="{UID}-row-' + i + '" style="cursor:pointer" onclick="location.href=\'../detail/page.html\'">'
            + '<td data-uid="{UID}-row-' + i + '-name">示例项目 ' + i + '</td>'
            + '<td data-uid="{UID}-row-' + i + '-status"><span class="p1-tag">进行中</span></td>'
            + '<td data-uid="{UID}-row-' + i + '-owner">负责人 ' + i + '</td>'
            + '<td data-uid="{UID}-row-' + i + '-date">2026-07-' + (10 + i) + '</td>'
            + '</tr>';
    }

    var table = '<div class="proto-frame" style="padding:0;overflow:hidden" data-uid="{UID}-table-wrap">'
        + '<table style="width:100%;border-collapse:collapse" data-uid="{UID}-table">'
        + '<thead><tr><th>名称</th><th>状态</th><th>负责人</th><th>更新日期</th></tr></thead>'
        + '<tbody>' + rows + '</tbody>'
        + '</table>'
        + '</div>';

    var main = toolbar + table;

    var content = ui.frameWeb(main, { active: 'list', base: '../' });
    LincolnPrototype.proto.mount(content);
})();
</script>
</body>
</html>
