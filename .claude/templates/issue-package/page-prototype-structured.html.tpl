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
  Optional portal annotations (right panel):
  这些 meta 可通过 pageData.annotations 自动注入。
  <meta name="doc-purpose" content="一句话功能说明">
  <meta name="doc-layout" content="顶部导航 | 左侧边栏 | 主内容区">
  <meta name="doc-fields" content="字段A — 类型 — 必填 — 说明">
  <meta name="doc-stories" content="作为...我想要...以便...">
  <meta name="doc-rules" content="点击提交后校验输入">
  <meta name="doc-boundaries" content="空列表展示占位图">
  <meta name="doc-exceptions" content="网络断开显示重试">
  <meta name="doc-refs" content="PRD #3 | flows.html">
-->
<title>{TITLE}</title>
<!-- Asset paths assume this page lives at pages/prototype/{group}/*.html (depth 3). -->
<link rel="stylesheet" href="../../../assets/prototype.css">
</head>
<body class="proto-page" data-page-uid="{UID}">

<div class="window full" id="win"></div>

<script type="application/json" id="pageData">
{PAGE_DATA}
</script>

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
        try { return localStorage.getItem(THEME_KEY); } catch (err) { return null; }
    }

    function setStoredTheme(theme) {
        try { localStorage.setItem(THEME_KEY, theme); } catch (err) {}
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
            if (window.parent) window.parent.postMessage({ type: 'lincoln-theme-ready' }, '*');
        });
    }

    initTheme();

    function loadData() {
        var el = document.getElementById('pageData');
        if (!el) return {};
        try { return JSON.parse(el.textContent) || {}; } catch (e) { return {}; }
    }

    function injectAnnotationMetas(data) {
        var annotations = data.annotations || {};
        var head = document.head;
        Object.keys(annotations).forEach(function (key) {
            var name = key.indexOf('doc-') === 0 ? key : 'doc-' + key;
            var value = annotations[key];
            var existing = document.querySelector('meta[name="' + name + '"]');
            if (existing) {
                existing.setAttribute('content', value);
            } else {
                var meta = document.createElement('meta');
                meta.setAttribute('name', name);
                meta.setAttribute('content', value);
                head.appendChild(meta);
            }
        });
    }

    var data = loadData();
    injectAnnotationMetas(data);

    var ui = window.LincolnPrototype && window.LincolnPrototype.ui;
    if (!ui) {
        document.getElementById('win').innerHTML = '<p style="padding:20px">LincolnPrototype.ui 未加载。请确认 prototype.js 路径正确。</p>';
        return;
    }

    var layout = data.layout || {};
    var type = layout.type || 'web';
    var shell = layout.shell || 'dashboard';
    var title = layout.title || document.title;

    // Build inner HTML from components or raw contentHtml.
    var contentHtml = '';
    if (typeof data.contentHtml === 'string') {
        contentHtml = data.contentHtml;
    } else if (Array.isArray(data.components)) {
        contentHtml = data.components.map(function (component) {
            var props = component.props || {};
            var uid = component.uid || (component.type + '-' + Math.random().toString(36).slice(2, 8));
            switch (component.type) {
                case 'html':
                    return '<div data-uid="' + uid + '"'
                        + (component.region ? ' data-region="' + component.region + '"' : '')
                        + '>' + (props.html || '') + '</div>';
                case 'wv':
                    return ui.wvPlaceholder(props.kind || 'chat');
                case 'onboarding':
                    var body = '<p data-uid="' + uid + '-desc">' + (props.body || '') + '</p>';
                    if (props.buttons) {
                        body += '<div style="display:flex;gap:10px;justify-content:center;margin-top:20px">';
                        props.buttons.forEach(function (btn) {
                            body += '<button class="btn ' + (btn.variant || 'default') + '" data-uid="' + (btn.uid || uid + '-btn') + '"'
                                + (btn.action ? ' onclick="' + btn.action + '"' : '') + '>' + btn.label + '</button>';
                        });
                        body += '</div>';
                    }
                    return ui.onboardingCard(props.title || title, body, { hero: props.hero });
                case 'settings':
                    return ui.settingsPage(props.active || '', props.title || title, props.bodyHtml || '', props.footHtml || '', {
                        groups: props.groups
                    });
                default:
                    return '<div data-uid="' + uid + '">' + (props.label || component.type) + '</div>';
            }
        }).join('\n');
    }

    var win = document.getElementById('win');
    if (type === 'app') {
        win.innerHTML = ui.frameApp(contentHtml, {
            active: layout.active || '',
            items: layout.sidebarItems,
            badge: layout.badge
        });
    } else if (type === 'mobile') {
        win.innerHTML = ui.frameMobile(contentHtml, {
            title: title,
            active: layout.active || '',
            tabs: layout.tabs
        });
    } else {
        // web
        var shellFn = ui['frame' + shell.charAt(0).toUpperCase() + shell.slice(1)];
        if (shellFn) {
            win.innerHTML = shellFn(contentHtml, {
                title: title,
                active: layout.active || '',
                navItems: layout.navItems
            });
        } else {
            win.innerHTML = ui.frameWeb(contentHtml, {
                title: title,
                active: layout.active || '',
                navItems: layout.navItems
            });
        }
    }

    // Tray controller pages post state to the portal instead of redrawing chrome.
    if (layout.trayController && typeof layout.trayState === 'object') {
        window.parent.postMessage({
            type: 'lincoln-tray-state',
            unread: layout.trayState.unread || 0,
            open: !!layout.trayState.open
        }, '*');
    }

    // Attach interactions for analytics / portal annotations.
    if (Array.isArray(data.interactions) && data.interactions.length) {
        var ann = document.createElement('div');
        ann.style.display = 'none';
        ann.setAttribute('data-interactions', JSON.stringify(data.interactions));
        document.body.appendChild(ann);
    }
})();
</script>
</body>
</html>
