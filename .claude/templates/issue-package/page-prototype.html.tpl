<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="doc-title" content="{TITLE}">
<meta name="nav-group" content="{NAV_GROUP}">
<meta name="page-uid" content="{UID}">
<meta name="prototype-base" content="../../../">
<title>{TITLE}</title>
<!-- Asset paths assume this page lives at pages/prototype/{group}/*.html (depth 3). -->
<link rel="stylesheet" href="../../../assets/prototype.css">
</head>
<body class="proto-page" data-page-uid="{UID}">

<!--
  Agent instructions:
  1. Keep this page self-contained: link prototype.css + prototype.js from the
     issue-package assets directory (paths above are correct for pages/prototype/*).
  2. Every interactive element must carry a stable data-uid attribute.
  3. Replace {TITLE}, {NAV_GROUP}, {UID} when copying this template.
  4. See .claude/templates/issue-package/prototypes/ for fuller examples
     (main, onboarding, settings, overlays, tray, org).
-->

<div class="window full" id="win"></div>

<script src="../../../assets/prototype.js"></script>
<script>
(function () {
    var ui = LincolnPrototype.ui;
    var hero = '<div style="display:flex;justify-content:center">' + ui.appLogo('lg') + '</div>';
    var body = '<p data-uid="{UID}-desc">在此放置原型内容。所有交互元素必须携带 <code>data-uid</code> 属性。</p>'
        + '<div style="display:flex;gap:10px;justify-content:center;margin-top:20px">'
        + '<button class="btn primary" data-uid="{UID}-btn-primary">主要操作</button>'
        + '<button class="btn default" data-uid="{UID}-btn-default">次要操作</button>'
        + '</div>';
    var content = ui.onboardingCard('{TITLE}', body, { hero: hero });
    LincolnPrototype.proto.mount(content);
})();
</script>
</body>
</html>
