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
<!-- Asset paths assume this page lives at pages/prototype/mobile/chat/*.html (depth 4). -->
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

    // ---------- Mobile chat content ----------
    var messages = '';
    var chats = [
        { side: 'left', text: '你好，这是示例对话。' },
        { side: 'right', text: '收到，正在查看内容。' },
        { side: 'left', text: '点击返回可回到首页。' }
    ];
    chats.forEach(function (c, idx) {
        var align = c.side === 'right' ? 'flex-end' : 'flex-start';
        var bg = c.side === 'right' ? 'var(--brand)' : 'var(--surface-2)';
        var color = c.side === 'right' ? '#fff' : 'var(--text-1)';
        messages += '<div style="display:flex;justify-content:' + align + ';margin-bottom:10px" data-uid="{UID}-msg-' + (idx + 1) + '"'>'
            + '<div style="max-width:70%;padding:10px 14px;border-radius:16px;background:' + bg + ';color:' + color + ';font-size:14px" data-uid="{UID}-msg-' + (idx + 1) + '-bubble">'
            + c.text
            + '</div>'
            + '</div>';
    });

    var main = '<div style="padding:10px;display:flex;flex-direction:column;flex:1;justify-content:flex-end" data-uid="{UID}-chat">'
        + messages
        + '</div>';

    var inputBar = '<div style="display:flex;gap:8px;padding:10px;border-top:1px solid var(--border)" data-uid="{UID}-inputbar">'
        + '<input type="text" class="field" style="flex:1;margin:0" placeholder="输入消息..." data-uid="{UID}-input-message">'
        + '<button class="btn primary" data-uid="{UID}-btn-send">发送</button>'
        + '</div>';

    var content = ui.frameMobile(main, { active: 'chat', base: '../', bottom: inputBar });
    LincolnPrototype.proto.mount(content);
})();
</script>
</body>
</html>
