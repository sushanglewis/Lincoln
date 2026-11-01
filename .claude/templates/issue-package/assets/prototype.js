/* Lincoln issue-package prototype kit — generic UI builders and helpers.
 * ES5 syntax, no modules. Pages link to this file after prototype.css.
 *
 * Usage in a prototype page:
 *   <div class="window full" id="win"></div>
 *   <script src="../../../assets/prototype.js"></script>
 *   <script>
 *     var content = LincolnPrototype.ui.frameMain(
 *       LincolnPrototype.ui.wvPlaceholder('chat'),
 *       { active: 'chat' }
 *     );
 *     LincolnPrototype.proto.mount(content);
 *   </script>
 */
window.LincolnPrototype = window.LincolnPrototype || {};

LincolnPrototype.data = {
    appName: 'Lincoln App',
    appInitial: 'L',
    appVersion: '1.0.0',
    currentUser: {
        name: '当前用户',
        initial: '用',
        email: 'user@example.com',
        nickname: '昵称',
        position: '职位',
        department: '部门',
        gender: '保密',
        phone: '138****0000',
        role: '成员',
        status: 'online'
    },
    currentOrg: {
        name: '示例组织',
        initial: '示',
        url: 'https://example.com'
    },
    orgs: [
        { name: '示例组织', initial: '示', url: 'https://example.com', current: true, role: '管理员', status: '当前' }
    ],
    settingsDefaults: {
        desktopNotify: true,
        notifySound: true,
        emailNotify: '跟随服务端',
        keywords: '@all @channel',
        messagePreview: true,
        theme: '跟随系统',
        language: '简体中文',
        timezone: '跟随系统',
        showOnlineStatus: true,
        autoStart: false,
        minimizeToTray: true,
        downloadPath: '/Users/example/Downloads',
        cacheSize: '128 MB'
    },
    unreadTotal: 3,
    unreadItems: [
        { sender: '张三', initial: '张', channelType: 'dm', preview: '这是第一条未读消息的摘要。', unread: 2, time: '09:30', mention: true },
        { sender: '产品群', initial: '产', channelType: 'group', preview: '李四：原型已更新。', unread: 1, time: '09:15', mention: false }
    ],
    webviews: {
        chat: { tag: 'WebView', name: '聊天', url: 'https://example.com/chat' },
        contacts: { tag: 'WebView', name: '通讯录', url: 'https://example.com/contacts' },
        tables: { tag: 'WebView', name: 'AI 表格', url: 'https://example.com/tables' }
    }
};

LincolnPrototype.ui = (function () {
    var D = function () { return LincolnPrototype.data; };

    function escapeHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    function uidSlug(label) {
        return escapeHtml(String(label)).replace(/\s+/g, '-');
    }

    function badge(n) {
        return n ? '<span class="badge">' + n + '</span>' : '';
    }

    function avatar(initials, status, sm) {
        return '<div class="avatar' + (sm ? ' sm' : '') + '">' + escapeHtml(initials)
            + (status ? '<span class="status-dot' + (status === 'online' ? '' : ' ' + status) + '"></span>' : '')
            + '</div>';
    }

    function appLogo(size) {
        var cls = size === 'lg' ? ' app-logo lg' : 'app-logo';
        return '<div class="' + cls + '">' + escapeHtml(D().appInitial || 'L') + '</div>';
    }

    function orgLogo(initial, size) {
        var cls = 'org-logo' + (size ? ' ' + size : '');
        return '<div class="' + cls + '">' + escapeHtml(initial) + '</div>';
    }

    function sidebar(active, opts) {
        opts = opts || {};
        var base = opts.base || '../';
        var items = opts.items || [
            ['chat', '聊天', opts.badge || 0],
            ['contacts', '通讯录', 0],
            ['tables', 'AI 表格', 0]
        ];
        var html = '<div class="sidebar"><div class="side-nav">';
        items.forEach(function (it) {
            html += '<a class="side-item' + (active === it[0] ? ' active' : '') + '" href="'
                + base + 'main/' + it[0] + '.html" data-uid="nav-' + it[0] + '">'
                + escapeHtml(it[1]) + badge(it[2]) + '</a>';
        });
        var u = D().currentUser;
        html += '</div><a class="userbar" href="' + base + 'overlays/avatar-menu.html" data-uid="nav-userbar">'
            + avatar(u.initial, u.status) + '<div class="u-name">' + escapeHtml(u.name) + '</div></a></div>';
        return html;
    }

    function frameApp(contentHtml, opts) {
        opts = opts || {};
        // mount() wraps this in .window.full#win, so we only emit the app body here.
        return '<div class="appbody">'
            + sidebar(opts.active || '', opts)
            + '<div class="app-main">' + contentHtml + '</div>'
            + '</div>';
    }

    // Backward-compatible alias.
    function frameMain(contentHtml, opts) {
        return frameApp(contentHtml, opts);
    }

    function frameWeb(contentHtml, opts) {
        opts = opts || {};
        var base = opts.base || './';
        var logoText = escapeHtml(opts.logoText || D().appInitial || 'L');
        var logoLabel = escapeHtml(opts.logoLabel || D().appName || 'Lincoln');
        var navItems = opts.navItems || [
            { id: 'dashboard', label: '概览', href: base + 'dashboard/page.html' },
            { id: 'list', label: '列表', href: base + 'list/page.html' },
            { id: 'form', label: '表单', href: base + 'form/page.html' },
            { id: 'detail', label: '详情', href: base + 'detail/page.html' }
        ];
        var active = opts.active || '';
        var navHtml = navItems.map(function (it) {
            var isActive = active === it.id ? ' active' : '';
            return '<a class="' + isActive + '" href="' + escapeHtml(it.href) + '" data-uid="web-nav-' + escapeHtml(it.id) + '">' + escapeHtml(it.label) + '</a>';
        }).join('');
        // Wrap in web-nav class for styling
        navHtml = '<nav class="web-nav">' + navHtml + '</nav>';
        return '<div class="web-shell">'
            + '<header class="web-topbar" data-uid="web-topbar">'
            + '<div class="web-logo" data-uid="web-logo">' + appLogo() + '<span>' + logoLabel + '</span></div>'
            + navHtml
            + '</header>'
            + '<main class="web-main" data-uid="web-main">' + contentHtml + '</main>'
            + '<footer class="web-footer" data-uid="web-footer">' + escapeHtml(opts.footer || '© 2026 Lincoln') + '</footer>'
            + '</div>';
    }

    function frameMobile(contentHtml, opts) {
        opts = opts || {};
        var base = opts.base || './';
        var title = escapeHtml(opts.title || D().appName || 'Lincoln');
        var tabs = opts.tabs || [
            { id: 'home', label: '首页', icon: '⌂' },
            { id: 'chat', label: '消息', icon: '✉' },
            { id: 'settings', label: '设置', icon: '⚙' },
            { id: 'profile', label: '我的', icon: '👤' }
        ];
        var active = opts.active || '';
        var tabsHtml = tabs.map(function (t) {
            var isActive = active === t.id ? ' active' : '';
            return '<a class="' + isActive + '" href="' + base + t.id + '/page.html" data-uid="mobile-tab-' + escapeHtml(t.id) + '">'
                + '<span class="tab-icon">' + escapeHtml(t.icon) + '</span>'
                + '<span>' + escapeHtml(t.label) + '</span>'
                + '</a>';
        }).join('');
        return '<div class="mobile-shell">'
            + '<header class="mobile-topbar" data-uid="mobile-topbar">'
            + '<button class="btn default sm" data-uid="mobile-back" onclick="history.back()">返回</button>'
            + '<h1 data-uid="mobile-title">' + title + '</h1>'
            + '<button class="btn default sm" data-uid="mobile-more">更多</button>'
            + '</header>'
            + '<main class="mobile-main" data-uid="mobile-main">' + contentHtml + '</main>'
            + '<nav class="mobile-bottom" data-uid="mobile-bottom">' + tabsHtml + '</nav>'
            + '</div>';
    }

    function wvPlaceholder(kind) {
        var m = D().webviews[kind] || { tag: 'WebView', name: kind, url: '' };
        return '<div class="wv" data-uid="wv-' + kind + '"><div class="wv-body"><div class="wv-placeholder">'
            + '<div class="wv-tag">' + escapeHtml(m.tag) + '</div>'
            + '<div class="wv-name">' + escapeHtml(m.name) + '</div>'
            + '<div class="wv-url">' + escapeHtml(m.url) + '</div>'
            + '</div></div></div>';
    }

    function wvLoading() {
        return '<div class="wv"><div class="wv-body">'
            + '<div class="wv-placeholder" style="border-style:solid;background:var(--surface)">'
            + '<div class="spinner"></div>'
            + '<div class="wv-name" style="font-size:14px;font-weight:400">正在加载…</div>'
            + '</div></div></div>';
    }

    function wvError() {
        return '<div class="wv"><div class="wv-body">'
            + '<div class="wv-placeholder" style="border-style:solid;background:var(--surface)">'
            + '<div class="wv-name">页面加载失败</div>'
            + '<div class="wv-error-code">ERR_CONNECTION_REFUSED</div>'
            + '<div class="wv-actions">'
            + '<a class="btn primary sm" style="width:auto" href="webview-loading.html" data-uid="wv-retry">重试</a>'
            + '<a class="btn default sm" href="chat.html" data-uid="wv-back">返回首页</a>'
            + '</div></div></div></div>';
    }

    function wvOfflineBanner() {
        return '<div class="wv-offline-banner">网络连接已断开，正在尝试重连…</div>';
    }

    function wvOffline(kind) {
        var m = D().webviews[kind] || { tag: 'WebView', name: kind, url: '' };
        return '<div class="wv">' + wvOfflineBanner()
            + '<div class="wv-body"><div class="wv-placeholder">'
            + '<div class="wv-tag">' + escapeHtml(m.tag) + '</div>'
            + '<div class="wv-name">' + escapeHtml(m.name) + '</div>'
            + '<div class="wv-url">' + escapeHtml(m.url) + '</div>'
            + '</div></div></div>';
    }

    function onboardingCard(title, bodyHtml, opts) {
        opts = opts || {};
        return '<div class="onboard"><div class="onboard-card" data-uid="onboard-card">'
            + '<h1>' + escapeHtml(title) + '</h1>'
            + (opts.hero || '')
            + bodyHtml
            + '</div></div>';
    }

    function row(label, control) {
        return '<div class="set-row" data-uid="row-' + uidSlug(label) + '"><div class="sr-label">' + escapeHtml(label) + '</div><div>' + control + '</div></div>';
    }

    function sw(label, checked) {
        return row(label, '<label class="switch"><input type="checkbox"' + (checked ? ' checked' : '')
            + ' data-uid="sw-' + uidSlug(label) + '"><span class="track"></span></label>');
    }

    function select(label, options, value) {
        var h = '<select data-uid="select-' + uidSlug(label) + '">';
        options.forEach(function (o) {
            h += '<option' + (o === value ? ' selected' : '') + '>' + escapeHtml(o) + '</option>';
        });
        return row(label, h + '</select>');
    }

    function ro(label, value) {
        return row(label + ' <span class="ro-tag">只读</span>', '<span class="sr-value">' + escapeHtml(value) + '</span>');
    }

    function settingsNav(active, groups, base) {
        base = base || '../';
        groups = groups || [
            { label: '个人设置', items: [['profile', '账号信息'], ['notifications', '通知'], ['display', '显示'], ['security', '安全']] },
            { label: '系统设置', items: [['general', '通用'], ['advanced', '高级']] }
        ];
        var h = '<div class="page-side">'
            + '<a class="ps-back" href="' + base + 'main/chat.html" data-uid="settings-back">&#8249; 返回</a>'
            + '<div class="ps-title">设置</div>';
        groups.forEach(function (g) {
            h += '<div class="ps-group">' + escapeHtml(g.label) + '</div>';
            g.items.forEach(function (it) {
                var id = it[0];
                var label = it[1];
                var disabled = it[2];
                if (disabled) {
                    h += '<span class="ps-item disabled" data-uid="nav-' + id + '">' + escapeHtml(label) + '</span>';
                } else {
                    h += '<a class="ps-item' + (active === id ? ' active' : '') + '" href="'
                        + base + 'settings/' + id + '.html" data-uid="nav-' + id + '">' + escapeHtml(label) + '</a>';
                }
            });
        });
        return h + '</div>';
    }

    function settingsPage(active, title, bodyHtml, footHtml, opts) {
        opts = opts || {};
        return '<div class="page">' + settingsNav(active, opts.groups, opts.base || '../')
            + '<div class="page-main">'
            + '<div class="page-head"><h2 data-uid="settings-title">' + escapeHtml(title) + '</h2></div>'
            + '<div class="page-body"><div class="col">' + bodyHtml + '</div></div>'
            + (footHtml ? '<div class="page-foot">' + footHtml + '</div>' : '')
            + '</div></div>';
    }

    function trayUnreadItem(it, base) {
        return '<a class="tr-un" href="' + base + 'main/chat.html" data-uid="tray-' + escapeHtml(it.initial) + '">'
            + avatar(it.initial, null, true)
            + '<div class="u-main"><div class="u-top"><span class="u-name">' + escapeHtml(it.sender) + '</span>'
            + badge(it.unread)
            + '<span class="u-time">' + escapeHtml(it.time) + '</span></div>'
            + '<div class="u-preview">' + (it.mention ? '<span style="color:var(--error)">[@我] </span>' : '') + escapeHtml(it.preview) + '</div>'
            + '</div></a>';
    }

    function trayMenu(hasUnread, base) {
        var h = '<div class="menu">';
        if (hasUnread) {
            D().unreadItems.slice(0, 5).forEach(function (it) { h += trayUnreadItem(it, base); });
        } else {
            h += '<div class="tr-empty">暂无未读消息</div>';
        }
        h += '<div class="divider"></div>'
            + '<a class="mi" href="' + base + 'main/chat.html" data-uid="tray-open">打开应用</a>'
            + '<div class="divider"></div>'
            + '<div class="mi danger" data-uid="tray-quit">退出应用</div>'
            + '</div>';
        return h;
    }

    function avatarMenu(base) {
        var u = D().currentUser;
        return '<a class="overlay-clear" href="' + base + 'main/chat.html" data-uid="avatar-menu-back"></a>'
            + '<div class="menu pop" style="left:12px;bottom:64px" data-uid="avatar-menu">'
            + '<div class="menu-head">' + avatar(u.initial, u.status)
            + '<div><div class="m-name">' + escapeHtml(u.name) + '</div><div class="m-mail">' + escapeHtml(u.email) + '</div></div></div>'
            + '<div class="mi" data-uid="status-online"><span class="dot green"></span>在线<span class="mi-right"><span class="check">&#10003;</span></span></div>'
            + '<div class="mi" data-uid="status-away"><span class="dot yellow"></span>离开</div>'
            + '<div class="mi" data-uid="status-dnd"><span class="dot red"></span>勿扰</div>'
            + '<div class="mi" data-uid="status-offline"><span class="dot gray"></span>离线</div>'
            + '<div class="divider"></div>'
            + '<a class="mi" href="' + base + 'settings/profile.html" data-uid="menu-profile">个人设置</a>'
            + '<a class="mi" href="' + base + 'settings/general.html" data-uid="menu-general">系统设置</a>'
            + '<a class="mi" href="' + base + 'org/org-list.html" data-uid="menu-org">组织管理</a>'
            + '<a class="mi" href="' + base + 'overlays/about.html" data-uid="menu-about">关于</a>'
            + '<div class="divider"></div>'
            + '<a class="mi danger" href="' + base + 'onboarding/login.html" data-uid="menu-logout">退出登录</a>'
            + '</div>';
    }

    function toast(sender, preview, appName) {
        sender = sender || '通知';
        preview = preview || '你有一条新消息。';
        appName = appName || D().appName;
        return '<a class="toast" href="#" data-uid="toast">'
            + avatar(sender.charAt(0), null, true)
            + '<div style="min-width:0">'
            + '<div><span class="t-title">' + escapeHtml(sender) + '</span><span class="t-app">' + escapeHtml(appName) + '</span></div>'
            + '<div class="t-body">' + escapeHtml(preview) + '</div>'
            + '</div><div class="t-close">&#10005;</div></a>';
    }

    function aboutDialog(base) {
        var org = D().currentOrg;
        return '<a class="overlay-backdrop" href="' + base + 'main/chat.html" style="display:block" data-uid="about-backdrop"></a>'
            + '<div class="about-dialog" data-uid="about-dialog">'
            + '<div style="display:flex;justify-content:center">' + appLogo('lg') + '</div>'
            + '<div class="a-name">' + escapeHtml(D().appName) + '</div>'
            + '<div class="a-ver">版本 ' + escapeHtml(D().appVersion) + '</div>'
            + '<div class="a-org">' + escapeHtml(org.name) + '</div>'
            + '<div class="a-copy">&copy; 2026 ' + escapeHtml(org.name) + ' 保留所有权利</div>'
            + '<div class="a-links"><a class="link" data-uid="about-license">第三方开源许可声明</a></div>'
            + '</div>';
    }

    return {
        escapeHtml: escapeHtml,
        badge: badge,
        avatar: avatar,
        appLogo: appLogo,
        orgLogo: orgLogo,
        sidebar: sidebar,
        frameApp: frameApp,
        frameMain: frameMain,
        frameWeb: frameWeb,
        frameMobile: frameMobile,
        wvPlaceholder: wvPlaceholder,
        wvLoading: wvLoading,
        wvError: wvError,
        wvOffline: wvOffline,
        wvOfflineBanner: wvOfflineBanner,
        onboardingCard: onboardingCard,
        row: row,
        sw: sw,
        select: select,
        ro: ro,
        settingsNav: settingsNav,
        settingsPage: settingsPage,
        trayMenu: trayMenu,
        avatarMenu: avatarMenu,
        toast: toast,
        aboutDialog: aboutDialog
    };
})();

LincolnPrototype.proto = (function () {
    function mount(html) {
        var win = document.getElementById('win');
        if (!win) {
            // If the page uses a different container, create one.
            var fallback = document.createElement('div');
            fallback.className = 'window full';
            fallback.id = 'win';
            document.body.appendChild(fallback);
            win = fallback;
        }
        win.innerHTML = html;
        bindPortalLinks();
    }

    function getPrototypeBase() {
        var meta = document.querySelector('meta[name="prototype-base"]');
        if (meta) return meta.getAttribute('content') || '../../..';
        return '../../..';
    }

    /* Resolve a local anchor href to a root-relative pages/... path.
     * Returns null for external links, anchors, or links outside the package.
     */
    function portalPathFromHref(href) {
        if (!href) return null;
        if (/^(https?:|mailto:|javascript:|#)/.test(href)) return null;

        var base = getPrototypeBase();
        var abs, root;
        try { abs = new URL(href, window.location.href).href; } catch (err) { return null; }
        try { root = new URL(base, window.location.href).href; } catch (err) { return null; }
        if (abs.indexOf(root) !== 0) return null;

        var path = abs.substring(root.length);
        if (!path || path.indexOf('pages/') !== 0) return null;
        return path;
    }

    /* Intercept local links inside the prototype iframe and notify the portal
     * so the left navigation highlight and right panel stay in sync.
     */
    var portalLinksBound = false;
    function bindPortalLinks() {
        if (portalLinksBound) return;
        portalLinksBound = true;
        document.addEventListener('click', function (e) {
            var a = e.target.closest('a');
            if (!a) return;
            if (a.getAttribute('target') === '_top') return;

            var path = portalPathFromHref(a.getAttribute('href') || '');
            if (!path) return;

            window.parent.postMessage({ type: 'lincoln-navigate', path: path }, '*');
            e.preventDefault();
        });
    }

    function bindTray(cfg) {
        var icon = document.querySelector(cfg.icon);
        var panel = document.querySelector(cfg.panel);
        var backdrop = document.querySelector(cfg.backdrop);
        if (!icon || !panel) return;
        function open() { panel.classList.add('visible'); }
        function close() { panel.classList.remove('visible'); }
        icon.addEventListener('click', function (e) { e.stopPropagation(); panel.classList.contains('visible') ? close() : open(); });
        panel.addEventListener('click', function (e) {
            var a = e.target.closest('a');
            if (!a) return;
            var path = portalPathFromHref(a.getAttribute('href') || '');
            if (path) {
                window.parent.postMessage({ type: 'lincoln-navigate', path: path }, '*');
                e.preventDefault();
            }
            close();
        });
        if (backdrop) backdrop.addEventListener('click', close);
    }


    /* ---------- Numbered hotspot annotations (driver.js, MIT) ---------- */

    var hotspotDriver = null;
    var hotspotPinned = -1;
    var hotspotHideTimer = null;

    function hotspotResolveTarget(h) {
        var sel = (h && h.target) || '';
        if (!sel) return null;
        var el = null;
        try { el = document.querySelector(sel); } catch (err) { el = null; }
        if (!el && !/[#.[\]:\s]/.test(sel)) {
            el = document.querySelector('[data-uid="' + sel + '"]');
            if (!el && document.getElementById(sel)) el = document.getElementById(sel);
        }
        return el;
    }

    function hotspotBadgeContainer(el) {
        // Void and form elements cannot contain a badge button. Anchor the
        // badge to their field/container while retaining the real target for
        // popovers, notes and presentation highlighting.
        if (/^(INPUT|TEXTAREA|SELECT|IMG|BR|HR)$/.test(el.tagName)) {
            return el.parentElement || el;
        }
        return el;
    }

    function hotspotDestroyPopover() {
        if (hotspotDriver) {
            try { hotspotDriver.destroy(); } catch (err) { /* ignore */ }
            hotspotDriver = null;
        }
    }

    function hotspotShow(index, el, h) {
        if (!window.driver || !window.driver.js || !window.driver.js.driver) return;
        hotspotDestroyPopover();
        hotspotDriver = window.driver.js.driver({
            showButtons: [],
            showProgress: false,
            allowClose: false,
            overlayOpacity: 0,
            stagePadding: 6,
            popoverClass: 'lc-driver-popover',
            onDestroyed: function () { hotspotDriver = null; }
        });
        hotspotDriver.highlight({
            element: el,
            popover: {
                title: (index + 1) + '. ' + (h.title || ''),
                description: h.text || '',
                side: 'bottom',
                align: 'start'
            }
        });
    }

    function hotspotScheduleHide() {
        if (hotspotHideTimer) clearTimeout(hotspotHideTimer);
        hotspotHideTimer = setTimeout(function () {
            if (hotspotPinned < 0) hotspotDestroyPopover();
        }, 180);
    }

    function hotspotCancelHide() {
        if (hotspotHideTimer) {
            clearTimeout(hotspotHideTimer);
            hotspotHideTimer = null;
        }
    }

    function initHotspots(hotspots) {
        if (!Array.isArray(hotspots) || !hotspots.length) return;
        if (!document.body.classList.contains('lc-hotspots-ready')) {
            document.body.classList.add('lc-hotspots-ready');
        }
        hotspots.forEach(function (h, index) {
            var el = hotspotResolveTarget(h);
            if (!el) return;
            var container = hotspotBadgeContainer(el);
            var position = window.getComputedStyle(container).position;
            if (position === 'static') {
                container.style.position = 'relative';
            }
            var badge = document.createElement('button');
            badge.type = 'button';
            badge.className = 'lc-hotspot';
            badge.textContent = String(index + 1);
            badge.setAttribute('data-hotspot-index', String(index));
            badge.setAttribute('aria-label', (h.title || '说明') + '：' + (h.text || ''));

            badge.addEventListener('mouseenter', function () {
                hotspotCancelHide();
                if (hotspotPinned < 0) hotspotShow(index, el, h);
            });
            badge.addEventListener('mouseleave', hotspotScheduleHide);
            badge.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                if (hotspotPinned === index) {
                    hotspotPinned = -1;
                    hotspotDestroyPopover();
                } else {
                    hotspotPinned = index;
                    hotspotShow(index, el, h);
                }
            });
            container.appendChild(badge);
        });

        // Clicking anywhere else unpins the popover.
        document.addEventListener('click', function (e) {
            if (hotspotPinned < 0) return;
            if (e.target.closest && e.target.closest('.lc-hotspot')) return;
            if (e.target.closest && e.target.closest('.driver-popover')) return;
            hotspotPinned = -1;
            hotspotDestroyPopover();
        });
    }


    /* ---------- Structured Axure-style review annotations ---------- */

    var annotationData = null;
    var annotationNotes = [];
    var annotationIndex = -1;
    var annotationTab = 'overview';
    var annotationPanel = null;
    var annotationControls = null;
    var annotationActiveElement = null;

    function annotationEscape(value) {
        return LincolnPrototype.ui.escapeHtml(String(value));
    }

    function annotationField(label, value) {
        if (value === undefined || value === null || value === '') return '';
        return '<div class="lc-annotation-field"><dt>' + annotationEscape(label) + '</dt><dd>' + annotationEscape(String(value)) + '</dd></div>';
    }

    function annotationFields(fields) {
        return '<dl class="lc-annotation-fields">' + fields.map(function (field) {
            return annotationField(field[0], field[1]);
        }).join('') + '</dl>';
    }

    function annotationNote(target, category, title, summary, fields) {
        return { target: target, category: category, title: title, summary: summary, fields: fields };
    }

    function annotationBuildNotes(data) {
        var notes = [];
        (data.sections || []).forEach(function (section) {
            notes.push(annotationNote(section.target, 'overview', section.title || '页面区域', section.purpose, [
                ['区域作用', section.purpose],
                ['包含内容', section.content]
            ]));
        });
        (data.interactions || []).forEach(function (interaction) {
            notes.push(annotationNote(interaction.target, 'interactions', interaction.name || '交互', interaction.response, [
                ['如何操作', interaction.trigger],
                ['系统反馈', interaction.response],
                ['业务规则', interaction.rule],
                ['后续去向', interaction.next]
            ]));
        });
        (data.exceptions || []).forEach(function (exception) {
            notes.push(annotationNote(exception.target, 'states', exception.name || '异常', exception.feedback, [
                ['何时发生', exception.trigger],
                ['用户看到什么', exception.feedback],
                ['如何恢复', exception.recovery]
            ]));
        });
        return notes;
    }

    function annotationClearHighlight() {
        if (annotationActiveElement) {
            annotationActiveElement.classList.remove('lc-annotation-active');
            annotationActiveElement = null;
        }
    }

    function annotationClose() {
        if (annotationPanel) annotationPanel.classList.remove('visible');
        annotationIndex = -1;
        annotationClearHighlight();
    }

    function annotationStateCard(state) {
        if (state.not_applicable) {
            return '<section class="lc-annotation-card na"><h4>' + annotationEscape(state.kind) + '（不适用）</h4>'
                + '<p>' + annotationEscape(state.reason || '') + '</p></section>';
        }
        return '<section class="lc-annotation-card"><h4>' + annotationEscape(state.name || state.kind)
            + ' <span class="lc-annotation-kind">' + annotationEscape(state.kind) + '</span></h4>'
            + annotationFields([
                ['何时发生', state.when],
                ['数据状态', state.data],
                ['可见与可用行为', state.feedback],
                ['恢复路径', state.recovery]
            ])
            + (state.page ? '<button type="button" class="lc-annotation-link" data-page="' + annotationEscape(state.page) + '">查看此状态页面</button>' : '')
            + '</section>';
    }

    function annotationDataTable(items) {
        return '<div class="lc-annotation-table-wrap"><table class="lc-annotation-table"><thead><tr>'
            + '<th>数据</th><th>业务含义</th><th>允许值/状态</th><th>为空时</th><th>校验规则</th><th>来源</th>'
            + '</tr></thead><tbody>' + (items || []).map(function (item) {
                return '<tr>' + [item.name, item.meaning, item.values, item.empty, item.validation, item.source].map(function (value) {
                    return '<td>' + annotationEscape(value || '') + '</td>';
                }).join('') + '</tr>';
            }).join('') + '</tbody></table></div>';
    }

    function annotationMainHtml() {
        var data = annotationData || {};
        if (annotationIndex >= 0 && annotationNotes[annotationIndex]) {
            var note = annotationNotes[annotationIndex];
            return '<section class="lc-annotation-note"><div class="lc-annotation-eyebrow">逐项演示</div><h3>'
                + annotationEscape(note.title) + '</h3><p class="lc-annotation-summary">' + annotationEscape(note.summary || '')
                + '</p>' + annotationFields(note.fields) + '</section>';
        }
        if (annotationTab === 'overview') {
            var overview = data.overview || {};
            return '<section class="lc-annotation-card"><h3>页面目标</h3>' + annotationFields([
                ['使用角色', overview.role],
                ['使用场景', overview.scenario],
                ['用户目标', overview.goal],
                ['从哪里进入', overview.entry],
                ['怎样算完成', overview.completion],
                ['当前页面状态', overview.current_state],
                ['所属业务流程', overview.flow]
            ]) + '</section>'
                + '<h3 class="lc-annotation-section-title">页面结构</h3>'
                + (data.sections || []).map(function (section) {
                    return '<section class="lc-annotation-card"><h4>' + annotationEscape(section.title || '') + '</h4>'
                        + annotationFields([['区域作用', section.purpose], ['包含内容', section.content]]) + '</section>';
                }).join('');
        }
        if (annotationTab === 'interactions') {
            return (data.interactions || []).map(function (interaction) {
                return '<section class="lc-annotation-card"><h4>' + annotationEscape(interaction.name || '') + '</h4>'
                    + annotationFields([
                        ['如何操作', interaction.trigger],
                        ['系统反馈', interaction.response],
                        ['业务规则', interaction.rule],
                        ['后续去向', interaction.next]
                    ]) + '</section>';
            }).join('');
        }
        if (annotationTab === 'states') {
            return '<h3 class="lc-annotation-section-title">完整状态目录</h3>'
                + (data.states || []).map(annotationStateCard).join('')
                + '<h3 class="lc-annotation-section-title">异常与恢复</h3>'
                + (data.exceptions || []).map(function (exception) {
                    return '<section class="lc-annotation-card exception"><h4>' + annotationEscape(exception.name || '') + '</h4>'
                        + annotationFields([
                            ['何时发生', exception.trigger],
                            ['用户看到什么', exception.feedback],
                            ['如何恢复', exception.recovery]
                        ]) + '</section>';
                }).join('');
        }
        return annotationDataTable(data.data || []);
    }

    function annotationRender() {
        if (!annotationPanel) return;
        var tabs = [
            ['overview', '页面结构'],
            ['interactions', '交互'],
            ['states', '状态与异常'],
            ['data', '数据']
        ];
        annotationPanel.innerHTML = '<div class="lc-annotation-head"><div><span class="lc-annotation-kicker">评审标注</span><strong>'
            + annotationEscape((annotationData.overview || {}).goal || '页面说明') + '</strong></div>'
            + '<button type="button" class="lc-annotation-close" aria-label="关闭标注">×</button></div>'
            + '<div class="lc-annotation-tabs" role="tablist">' + tabs.map(function (tab) {
                return '<button type="button" role="tab" data-tab="' + tab[0] + '" aria-selected="' + (annotationTab === tab[0] && annotationIndex < 0 ? 'true' : 'false') + '" class="' + (annotationTab === tab[0] && annotationIndex < 0 ? 'active' : '') + '">' + tab[1] + '</button>';
            }).join('') + '</div>'
            + '<div class="lc-annotation-body">' + annotationMainHtml() + '</div>'
            + (annotationIndex >= 0 ? '<div class="lc-annotation-foot"><button type="button" class="lc-annotation-prev"' + (annotationIndex === 0 ? ' disabled' : '') + '>上一条</button><span>' + (annotationIndex + 1) + ' / ' + annotationNotes.length + '</span><button type="button" class="lc-annotation-next"' + (annotationIndex >= annotationNotes.length - 1 ? ' disabled' : '') + '>下一条</button></div>' : '');

        annotationPanel.querySelector('.lc-annotation-close').addEventListener('click', annotationClose);
        annotationPanel.querySelectorAll('[data-tab]').forEach(function (button) {
            button.addEventListener('click', function () {
                annotationTab = button.getAttribute('data-tab');
                annotationIndex = -1;
                annotationClearHighlight();
                annotationRender();
            });
        });
        annotationPanel.querySelectorAll('[data-page]').forEach(function (button) {
            button.addEventListener('click', function () {
                var path = button.getAttribute('data-page');
                if (window.parent && window.parent !== window) {
                    window.parent.postMessage({ type: 'lincoln-navigate', path: path }, '*');
                } else {
                    window.location.href = getPrototypeBase() + path;
                }
            });
        });
        var prev = annotationPanel.querySelector('.lc-annotation-prev');
        var next = annotationPanel.querySelector('.lc-annotation-next');
        if (prev) prev.addEventListener('click', function () { annotationNext(-1); });
        if (next) next.addEventListener('click', function () { annotationNext(1); });
    }

    function annotationOpen(tab) {
        annotationTab = tab || annotationTab;
        annotationIndex = -1;
        annotationClearHighlight();
        annotationPanel.classList.add('visible');
        annotationRender();
    }

    function annotationShow(index) {
        if (!annotationNotes[index]) return;
        annotationIndex = index;
        annotationTab = annotationNotes[index].category;
        annotationClearHighlight();
        var el = hotspotResolveTarget(annotationNotes[index]);
        if (el) {
            annotationActiveElement = el;
            el.classList.add('lc-annotation-active');
        }
        annotationPanel.classList.add('visible');
        annotationRender();
    }

    function annotationNext(direction) {
        var next = annotationIndex + direction;
        if (next < 0 || next >= annotationNotes.length) return;
        annotationShow(next);
    }

    function annotationCreateShell() {
        annotationControls = document.createElement('div');
        annotationControls.className = 'lc-annotation-controls';
        annotationControls.innerHTML = '<button type="button" class="lc-annotation-toggle">标注 <span>' + annotationNotes.length + '</span></button><button type="button" class="lc-annotation-demo">演示</button>';
        document.body.appendChild(annotationControls);
        annotationControls.querySelector('.lc-annotation-toggle').addEventListener('click', function () {
            if (annotationPanel.classList.contains('visible')) annotationClose();
            else annotationOpen('overview');
        });
        annotationControls.querySelector('.lc-annotation-demo').addEventListener('click', function () {
            if (annotationNotes.length) annotationShow(0);
        });

        annotationPanel = document.createElement('aside');
        annotationPanel.className = 'lc-annotation-panel';
        annotationPanel.setAttribute('aria-label', '原型评审标注');
        document.body.appendChild(annotationPanel);

        document.addEventListener('keydown', function (event) {
            if (!annotationPanel.classList.contains('visible')) return;
            if (event.key === 'Escape') annotationClose();
            if (annotationIndex >= 0 && event.key === 'ArrowRight') annotationNext(1);
            if (annotationIndex >= 0 && event.key === 'ArrowLeft') annotationNext(-1);
        });
    }

    function initAnnotations(data, legacyHotspots) {
        if (!data || typeof data !== 'object') {
            initHotspots(legacyHotspots || []);
            return;
        }
        annotationData = data;
        annotationNotes = annotationBuildNotes(data);
        (legacyHotspots || []).forEach(function (hotspot) {
            annotationNotes.push(annotationNote(hotspot.target, 'interactions', hotspot.title || '说明', hotspot.text, [['说明', hotspot.text]]));
        });
        annotationCreateShell();
        annotationNotes.forEach(function (note, index) {
            var el = hotspotResolveTarget(note);
            if (!el) return;
            var container = hotspotBadgeContainer(el);
            if (window.getComputedStyle(container).position === 'static') container.style.position = 'relative';
            var badge = document.createElement('button');
            badge.type = 'button';
            badge.className = 'lc-hotspot lc-annotation-badge';
            badge.textContent = String(index + 1);
            badge.setAttribute('aria-label', '查看标注：' + note.title);
            badge.addEventListener('click', function (event) {
                event.preventDefault();
                event.stopPropagation();
                annotationShow(index);
            });
            container.appendChild(badge);
        });
        document.body.classList.add('lc-hotspots-ready');
    }

    function toggleHotspots() {
        var off = document.body.classList.toggle('lc-hotspots-off');
        if (off) {
            hotspotPinned = -1;
            hotspotDestroyPopover();
            annotationClose();
        }
        return !off;
    }

    return {
        mount: mount,
        bindPortalLinks: bindPortalLinks,
        bindTray: bindTray,
        getPrototypeBase: getPrototypeBase,
        portalPathFromHref: portalPathFromHref,
        initAnnotations: initAnnotations,
        initHotspots: initHotspots,
        toggleHotspots: toggleHotspots
    };
})();
