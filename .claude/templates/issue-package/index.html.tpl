<!DOCTYPE html>
<html lang="zh-CN" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Lincoln Issue Package · 门户</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<div class="portal-wrap">
    <nav class="pnav" id="pnav">
        <div class="pnav-header">
            <div class="pnav-logo">L</div>
            <div>
                <div class="pnav-title">Issue Package</div>
                <div class="pnav-subtitle">初始化中...</div>
            </div>
        </div>
        <div class="pnav-status">阶段: <span class="stage">not_started</span></div>

        <div class="pnav-checklist" id="artifactChecklist">
            <h4>必要产物清单</h4>
            <ul>
                <li data-key="prd">PRD</li>
                <li data-key="ui-spec">UI 规范</li>
                <li data-key="fields">字段说明</li>
                <li data-key="decisions">决策记录</li>
                <li data-key="research">调研笔记</li>
                <li data-key="prototype-web">原型 · Web 端</li>
                <li data-key="prototype-mobile">原型 · 手机端</li>
                <li data-key="prototype-app">原型 · 应用端</li>
                <li data-key="handoff">Handoff 交接</li>
                <li data-key="openspec">OpenSpec 提案</li>
            </ul>
        </div>
    </nav>

    <main class="pstage" id="pstage">
        <div class="mac-menubar">
            <div class="mac-menu-left">
                <span class="mac-apple">&#63743;</span>
                <span class="mac-app">Lincoln</span>
                <span>文件</span>
                <span>编辑</span>
                <span>视图</span>
                <span>窗口</span>
                <span>帮助</span>
            </div>
            <div class="mac-menu-right">
                <button class="theme-toggle" id="themeToggle" title="切换主题" aria-label="切换主题">☀</button>
                <span class="mac-tray" id="macTray">L</span>
                <span class="mac-date" id="macDate"></span>
            </div>
        </div>

        <div class="mac-tray-menu" id="macTrayMenu"></div>

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
    </main>

    <aside class="pann" id="pann">
        <div class="pann-inner" id="pannInner">
            <p>点击左侧页面索引加载文档或原型。每个页面应通过 meta 标签提供功能、布局、字段、边界与异常流注解。</p>
        </div>
    </aside>
</div>

<script src="assets/js/package-data.js"></script>
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
