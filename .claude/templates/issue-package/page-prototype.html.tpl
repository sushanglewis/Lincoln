<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="doc-title" content="{TITLE}">
<meta name="nav-label" content="{NAV_LABEL}">
<meta name="nav-group" content="{NAV_GROUP}">
<meta name="page-uid" content="{UID}">
<meta name="prototype-base" content="../../../">
<!--
  Explanations are numbered on-page hotspots (driver.js, MIT), not meta tags.
  Call LincolnPrototype.proto.initHotspots([...]) after mounting content:
    [{target: "search-box", title: "全局搜索", text: "支持拼音首字母，回车跳转首个结果"}]
  `target` is a CSS selector, a data-uid, or an element id. Hover shows the
  popover; click pins it. Keep nav metas (doc-title / nav-label / nav-group /
  page-uid) accurate for the portal index.
-->
<title>{TITLE}</title>
<!-- Asset paths assume this page lives at pages/prototype/{group}/*.html (depth 3). -->
<link rel="stylesheet" href="../../../assets/prototype.css">
<link rel="stylesheet" href="../../../assets/driver.css">
</head>
<body class="proto-page" data-page-uid="{UID}">

<!--
  Agent instructions:
  1. Keep this page self-contained: link prototype.css + prototype.js from the
     issue-package assets directory (paths above are correct for pages/prototype/*).
  2. Every interactive element must carry a stable data-uid attribute.
  3. Replace {TITLE}, {NAV_GROUP}, {UID} when copying this template.
  4. Choose the right shell from LincolnPrototype.ui (frameApp / frameWeb / frameMobile)
     based on the product form-factor.
  5. Explain functionality, layout, fields, boundary cases, and exception flows
     via LincolnPrototype.initHotspots (numbered badges + hover popovers) —
     never as on-screen prose, and never as doc-* meta tags.
  6. See .claude/templates/issue-package/prototypes/ for categorized examples:
     app/{main,onboarding,settings,overlays,tray,org}, web/{dashboard,list,form,detail},
     mobile/{home,chat,settings,profile}.
-->

<div class="window full" id="win"></div>

<script src="../../../assets/driver.js"></script>
<script src="../../../assets/prototype.js"></script>
<script>
(function () {
    'use strict';

    var THEME_KEY = 'lincoln-theme';

    function getQueryTheme() {
        var m = window.location.search.match(/[?&]theme=(light|dark)(?:&|$)/);
        return m ? m[1] : null;
    }

    function getStoredTheme() {
        try {
            return localStorage.getItem(THEME_KEY);
        } catch (err) {
            return null;
        }
    }

    function setStoredTheme(theme) {
        try {
            localStorage.setItem(THEME_KEY, theme);
        } catch (err) {
            // ignore
        }
    }

    function applyTheme(theme) {
        if (theme !== 'light' && theme !== 'dark') return;
        document.documentElement.setAttribute('data-theme', theme);
        setStoredTheme(theme);
    }

    function initTheme() {
        var theme = getQueryTheme() || getStoredTheme() || 'light';
        applyTheme(theme);

        window.addEventListener('message', function (e) {
            var data = e.data || {};
            if (data.type === 'lincoln-theme' && (data.theme === 'light' || data.theme === 'dark')) {
                applyTheme(data.theme);
            }
        });

        window.addEventListener('load', function () {
            if (window.parent) {
                window.parent.postMessage({ type: 'lincoln-theme-ready' }, '*');
            }
        });
    }

    initTheme();

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
