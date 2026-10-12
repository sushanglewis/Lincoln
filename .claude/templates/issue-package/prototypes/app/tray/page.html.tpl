<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="doc-title" content="{TITLE}">
<meta name="nav-label" content="{NAV_LABEL}">
<meta name="nav-group" content="{NAV_GROUP}">
<meta name="page-uid" content="{UID}">
<meta name="prototype-base" content="../../../../">
<!--
  Explanations are numbered on-page hotspots (driver.js, MIT) via
  LincolnPrototype.proto.initHotspots([{target, title, text}, ...]) —
  never doc-* meta tags. Tray scenario pages must NOT render a tray chrome.

  IMPORTANT: This page must NOT render a tray inside the app prototype.
  The system tray is portal-level chrome. Send postMessage to drive it:

      window.parent.postMessage({
          type: 'lincoln-tray-state',
          unread: 3,   // number; 0 hides the badge
          open: true   // boolean; true opens the portal tray menu
      }, '*');
-->
<title>{TITLE}</title>
<link rel="stylesheet" href="../../../../assets/prototype.css">
<style>
.tray-hint {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    max-width: 420px;
    padding: 24px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.12);
    text-align: center;
    color: var(--text);
}
.tray-hint h2 { margin: 0 0 12px; font-size: 18px; }
.tray-hint p { margin: 0; color: var(--text-2); line-height: 1.6; }
</style>
</head>
<body class="desktop">

<div class="tray-hint" data-uid="{UID}-hint">
    <h2>系统托盘场景：{TITLE}</h2>
    <p>此场景通过 postMessage 驱动门户层 macOS 托盘，请看画布右上角菜单栏。</p>
</div>

<script src="../../../../assets/prototype.js"></script>
<script>
(function () {
    var unread = 0;   // override per scenario: 0, 3, etc.
    var open = false; // override per scenario: true for menu-open state

    function sendTrayState() {
        if (window.parent) {
            window.parent.postMessage({ type: 'lincoln-tray-state', unread: unread, open: open }, '*');
        }
    }

    sendTrayState();
    window.addEventListener('load', sendTrayState);
})();
</script>

</body>
</html>
