<!DOCTYPE html>
<html lang="zh-CN" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Lincoln Issue Package · 门户</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<div class="portal-wrap" id="portalWrap">
    <nav class="pnav" id="pnav">
        <div class="pnav-header">
            <div class="pnav-logo">L</div>
            <div>
                <div class="pnav-title">Issue Package</div>
                <div class="pnav-subtitle">初始化中...</div>
            </div>
        </div>
        <div class="pnav-status">阶段: <span class="stage">not_started</span></div>
        <div class="pnav-groups" id="pnavGroups"></div>
    </nav>

    <main class="pstage" id="pstage">
        <div class="mac-menubar">
            <div class="mac-menu-left">
                <span class="mac-app">Lincoln</span>
            </div>
            <div class="mac-menu-right">
                <button class="theme-toggle" id="focusToggle" title="聚焦模式（Esc 退出）" aria-label="聚焦模式" aria-pressed="false">&#10570;</button>
                <button class="theme-toggle" id="themeToggle" title="切换主题" aria-label="切换主题">&#9728;</button>
                <span class="mac-tray" id="macTray">L</span>
                <span class="mac-date" id="macDate"></span>
            </div>
        </div>

        <div class="mac-tray-menu" id="macTrayMenu"></div>

        <button class="nav-drawer-btn" id="navDrawerBtn" title="展开目录（Esc 收起）" aria-label="展开目录" aria-expanded="false">&#9776;</button>
        <div class="nav-drawer-backdrop" id="navDrawerBackdrop" hidden></div>

        <div class="pstage-body" id="pstageBody">
            <div class="doc-view hidden" id="docView" tabindex="-1"></div>
            <div class="mac-window" id="macWindow">
                <div class="mac-titlebar">
                    <div class="mac-traffic">
                        <span class="mac-close"></span>
                        <span class="mac-min"></span>
                        <span class="mac-max"></span>
                    </div>
                    <div class="mac-win-title" id="winTitle">Lincoln Issue Package</div>
                </div>
                <iframe id="frame" title="page"></iframe>
            </div>
        </div>
    </main>
</div>

<script src="assets/js/package-data.js"></script>
<script src="assets/marked.min.js"></script>
<script src="assets/mermaid.min.js"></script>
<script src="assets/app.js"></script>
<script>
(function(){
    var dateEl = document.getElementById('macDate');
    if (dateEl) {
        var now = new Date();
        dateEl.textContent = now.getFullYear() + '/' + (now.getMonth() + 1) + '/' + now.getDate();
    }
})();
</script>
</body>
</html>
