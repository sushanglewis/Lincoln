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
<link rel="stylesheet" href="../../../../assets/prototype.css">
</head>
<body class="desktop">

<div class="menubar">
    <div class="tray-icon" id="trayIcon" data-uid="{UID}-tray-icon">
        <div class="app-logo">L</div>
        <span class="tray-badge" data-uid="{UID}-tray-badge">3</span>
    </div>
</div>

<div class="tray-panel" id="trayPanel" data-uid="{UID}-tray-panel">
    <!-- tray menu rendered by JS -->
</div>

<div class="desk-hint" data-uid="{UID}-hint">
    点击右上角托盘图标查看系统托盘菜单。<br>
    子页面链接会通过 postMessage 通知门户进行统一导航。
</div>

<script src="../../../../assets/prototype.js"></script>
<script>
(function () {
    var ui = LincolnPrototype.ui;
    var hasUnread = LincolnPrototype.data.unreadTotal > 0;
    document.getElementById('trayPanel').innerHTML = ui.trayMenu(hasUnread, '../');
    LincolnPrototype.proto.bindTray({
        icon: '#trayIcon',
        panel: '#trayPanel',
        backdrop: 'body'
    });
})();
</script>

</body>
</html>
