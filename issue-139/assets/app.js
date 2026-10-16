/**
 * Lincoln issue-package portal runtime.
 * Reads window.LINC_PACKAGE from assets/js/package-data.js and renders the
 * left navigation (collapsible groups + filter), the content area (Markdown
 * doc pages rendered in place via marked, prototype pages via iframe), and
 * focus mode. Also manages light/dark theme synchronization with child pages.
 */
(function () {
    'use strict';

    var THEME_KEY = 'lincoln-theme';
    var NAV_STATE_KEY = 'lincoln-nav-groups';
    var FOCUS_KEY = 'lincoln-focus';

    function generateUUID(prefix) {
        var hex = '';
        for (var i = 0; i < 8; i++) {
            hex += Math.floor(Math.random() * 16).toString(16);
        }
        return (prefix || 'e') + '-' + hex;
    }

    function escapeHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
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

    function getPreferredTheme() {
        var stored = getStoredTheme();
        if (stored === 'light' || stored === 'dark') return stored;
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) return 'dark';
        return 'light';
    }

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        var btn = document.getElementById('themeToggle');
        if (btn) btn.textContent = theme === 'dark' ? '\u263E' : '\u2600';
    }

    function notifyFrame(theme) {
        var frame = document.getElementById('frame');
        if (frame && frame.contentWindow) {
            frame.contentWindow.postMessage({ type: 'lincoln-theme', theme: theme }, '*');
        }
    }

    function setTheme(theme) {
        if (theme !== 'light' && theme !== 'dark') return;
        setStoredTheme(theme);
        applyTheme(theme);
        notifyFrame(theme);
    }

    function toggleTheme() {
        var current = document.documentElement.getAttribute('data-theme') || 'light';
        setTheme(current === 'dark' ? 'light' : 'dark');
    }

    function initTheme() {
        var theme = getPreferredTheme();
        applyTheme(theme);
        var btn = document.getElementById('themeToggle');
        if (btn) btn.addEventListener('click', toggleTheme);

        window.addEventListener('message', function (e) {
            var data = e.data || {};
            if (data.type === 'lincoln-theme-ready') {
                notifyFrame(getPreferredTheme());
            }
        });
    }

    /* ---------- Sidebar: groups, collapse state, filter ---------- */

    function loadNavState() {
        try {
            return JSON.parse(localStorage.getItem(NAV_STATE_KEY) || '{}') || {};
        } catch (err) {
            return {};
        }
    }

    function saveNavState(state) {
        try {
            localStorage.setItem(NAV_STATE_KEY, JSON.stringify(state));
        } catch (err) {
            // ignore
        }
    }

    function renderNav(container, packageData) {
        var html = '';
        html += '<div class="pnav-header">';
        html += '<button type="button" class="nav-toggle-btn pnav-collapse-btn" id="navCollapseBtn" title="收起目录（左侧栏展开）" aria-label="收起目录"><span class="nav-toggle-icon">&#9776;</span><span class="nav-toggle-text">收起目录</span></button>';
        html += '<div class="pnav-logo">L</div>';
        html += '<div>';
        html += '<div class="pnav-title">Issue #' + escapeHtml(packageData.issue_number || '') + '</div>';
        html += '<div class="pnav-subtitle">' + escapeHtml(packageData.process_slug || '') + '</div>';
        html += '</div></div>';

        html += '<div class="pnav-toolbar">';
        html += '<input type="search" class="pnav-filter" id="navFilter" placeholder="过滤页面…" aria-label="过滤页面">';
        html += '<button type="button" class="pnav-tool-btn" id="navCollapseAll" title="收起/展开全部目录" aria-label="收起或展开全部目录">&#8678;</button>';
        html += '</div>';

        html += '<div class="pnav-groups" id="pnavGroups">';
        (packageData.nav || []).forEach(function (group) {
            var items = group.items || [];
            if (!items.length) return;
            var archived = group.group === '归档' || items.every(function (item) { return item.archived; });
            html += '<details class="pnav-group-details'
                + (archived ? ' pnav-archive' : '')
                + '" data-group="' + escapeHtml(group.group) + '">';
            html += '<summary class="pnav-group">' + escapeHtml(archived ? '归档' : group.group)
                + '<span class="pnav-count">' + items.length + '</span></summary>';
            items.forEach(function (item) {
                html += '<a class="pnav-link" data-path="' + escapeHtml(item.path) + '" href="#/"'
                    + escapeHtml(item.path) + '"'
                    + (item.markdown ? ' data-doc="1"' : '') + '>'
                    + '<span class="pnav-link-label">' + escapeHtml(item.label) + '</span>';
                if (item.version) {
                    html += '<span class="pnav-link-version">' + escapeHtml(item.version) + '</span>';
                }
                html += '</a>';
            });
            html += '</details>';
        });
        html += '<div class="pnav-empty hidden" id="navEmpty">无匹配页面</div>';
        html += '</div>';

        if (packageData.current_stage) {
            html += '<div class="pnav-status">阶段: <span class="stage">' + escapeHtml(packageData.current_stage) + '</span></div>';
        }

        container.innerHTML = html;
        initNavGroups(container);
        initNavFilter(container);
    }

    function initNavGroups(nav) {
        var state = loadNavState();
        var groups = nav.querySelectorAll('details.pnav-group-details');
        groups.forEach(function (details) {
            var name = details.getAttribute('data-group');
            var archived = details.classList.contains('pnav-archive');
            var open = Object.prototype.hasOwnProperty.call(state, name) ? !!state[name] : !archived;
            if (open) details.setAttribute('open', '');
            else details.removeAttribute('open');
            details.addEventListener('toggle', function () {
                var current = loadNavState();
                current[name] = details.open;
                saveNavState(current);
            });
        });

        var btn = document.getElementById('navCollapseAll');
        if (!btn) return;
        function refreshIcon() {
            var anyOpen = false;
            groups.forEach(function (details) { if (details.open) anyOpen = true; });
            btn.innerHTML = anyOpen ? '&#8678;' : '&#8680;';
            btn.title = anyOpen ? '收起全部目录' : '展开全部目录';
        }
        refreshIcon();
        btn.addEventListener('click', function () {
            var anyOpen = false;
            groups.forEach(function (details) { if (details.open) anyOpen = true; });
            var next = {};
            groups.forEach(function (details) {
                if (anyOpen) details.removeAttribute('open');
                else details.setAttribute('open', '');
                next[details.getAttribute('data-group')] = !anyOpen;
            });
            saveNavState(next);
            refreshIcon();
        });
        groups.forEach(function (details) {
            details.addEventListener('toggle', refreshIcon);
        });
    }

    function initNavFilter(nav) {
        var input = document.getElementById('navFilter');
        var empty = document.getElementById('navEmpty');
        if (!input) return;
        input.addEventListener('input', function () {
            var query = input.value.trim().toLowerCase();
            var anyVisible = false;
            nav.querySelectorAll('details.pnav-group-details').forEach(function (details) {
                var groupVisible = false;
                details.querySelectorAll('.pnav-link').forEach(function (link) {
                    var haystack = (link.getAttribute('data-path') + ' '
                        + link.textContent).toLowerCase();
                    var match = !query || haystack.indexOf(query) !== -1;
                    link.classList.toggle('hidden', !match);
                    link.classList.toggle('match', !!query && match);
                    if (match) groupVisible = true;
                });
                details.classList.toggle('hidden', !groupVisible);
                if (groupVisible) {
                    anyVisible = true;
                    if (query) details.setAttribute('open', '');
                }
                if (!query) {
                    var name = details.getAttribute('data-group');
                    var state = loadNavState();
                    var archived = details.classList.contains('pnav-archive');
                    var open = Object.prototype.hasOwnProperty.call(state, name) ? !!state[name] : !archived;
                    if (open) details.setAttribute('open', '');
                    else details.removeAttribute('open');
                }
            });
            if (empty) empty.classList.toggle('hidden', anyVisible || !query);
        });
    }

    /* ---------- Sidebar collapse (unified for docs and prototypes) ---------- */

    var currentPage = null;

    function getFocusManual() {
        try {
            return localStorage.getItem(FOCUS_KEY) === '1';
        } catch (err) {
            return false;
        }
    }

    function setFocusManual(value) {
        try {
            localStorage.setItem(FOCUS_KEY, value ? '1' : '0');
        } catch (err) {
            // ignore
        }
    }

    function applyFocusMode() {
        var wrap = document.getElementById('portalWrap');
        var btn = document.getElementById('navExpandBtn');
        if (!wrap) return;
        var active = getFocusManual();
        wrap.classList.toggle('focus', active);
        if (btn) btn.setAttribute('aria-expanded', active ? 'true' : 'false');
    }

    function initFocusMode() {
        function toggle() {
            setFocusManual(!getFocusManual());
            applyFocusMode();
        }
        var expandBtn = document.getElementById('navExpandBtn');
        if (expandBtn) expandBtn.addEventListener('click', toggle);
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && getFocusManual()) {
                setFocusManual(false);
                applyFocusMode();
            }
        });
    }

    function bindNavCollapseButton(nav) {
        var btn = document.getElementById('navCollapseBtn');
        if (!btn || !nav) return;
        btn.addEventListener('click', function () {
            setFocusManual(true);
            applyFocusMode();
        });
    }

    /* ---------- Content area: in-place docs + iframe prototypes ---------- */

    function convertMermaidBlocks(root) {
        var blocks = root.querySelectorAll('pre code.language-mermaid');
        blocks.forEach(function (code) {
            var pre = code.parentNode;
            var container = document.createElement('pre');
            container.className = 'lincoln-mermaid';
            container.textContent = code.textContent;
            pre.parentNode.replaceChild(container, pre);
        });
    }

    function runMermaid(root) {
        if (typeof window.mermaid === 'undefined') return;
        var theme = document.documentElement.getAttribute('data-theme') || 'light';
        try {
            window.mermaid.initialize({
                startOnLoad: false,
                theme: theme === 'dark' ? 'dark' : 'default'
            });
        } catch (err) {
            // ignore init errors
        }
        var nodes = [];
        root.querySelectorAll('.lincoln-mermaid').forEach(function (node) {
            if (!node.getAttribute('data-mermaid-done')) nodes.push(node);
        });
        if (!nodes.length) return;
        nodes.forEach(function (node) { node.setAttribute('data-mermaid-done', '1'); });
        try {
            window.mermaid.run({ nodes: nodes });
        } catch (err) {
            // Fallback for older Mermaid versions
            try {
                window.mermaid.init(undefined, nodes);
            } catch (e2) {
                // ignore
            }
        }
    }

    function renderMarkdownDoc(view, page) {
        var body = '';
        if (window.marked) {
            try {
                window.marked.setOptions({ gfm: true, breaks: false });
                body = window.marked.parse(page.markdown || '');
            } catch (err) {
                body = '';
            }
        }
        if (!body) {
            body = '<pre>' + escapeHtml(page.markdown || '(无内容)') + '</pre>';
        }
        var meta = '';
        if (page.version) meta += '<span class="doc-version">' + escapeHtml(page.version) + '</span>';
        if (page.stage) meta += '<span class="doc-stage">阶段: ' + escapeHtml(page.stage) + '</span>';
        view.innerHTML = '<div class="doc-page"><div class="doc-header"><h1>'
            + escapeHtml(page.title || page.label || '')
            + '</h1><div class="doc-meta">' + meta + '</div></div>'
            + '<div class="doc-content">' + body + '</div></div>';
        convertMermaidBlocks(view);
        runMermaid(view);
    }

    function showDocPage(page) {
        var view = document.getElementById('docView');
        var win = document.getElementById('macWindow');
        if (!view) return;
        renderMarkdownDoc(view, page);
        view.classList.remove('hidden');
        if (win) win.classList.add('hidden');
        view.scrollTop = 0;
        view.focus({ preventScroll: true });
    }

    function showFramePage(path) {
        var view = document.getElementById('docView');
        var win = document.getElementById('macWindow');
        var frame = document.getElementById('frame');
        if (view) view.classList.add('hidden');
        if (win) win.classList.remove('hidden');
        if (frame && frame.getAttribute('src') !== path) frame.src = path;
    }

    function findPage(path, pages) {
        for (var i = 0; i < pages.length; i++) {
            var items = pages[i].items || [];
            for (var j = 0; j < items.length; j++) {
                if (items[j].path === path) return items[j];
            }
        }
        return null;
    }

    function findLandingPage(pages) {
        var fallback = null;
        for (var i = 0; i < pages.length; i++) {
            var items = pages[i].items || [];
            for (var j = 0; j < items.length; j++) {
                if (!fallback) fallback = items[j];
                if (items[j].markdown) return items[j];
            }
        }
        return fallback;
    }

    var suppressHash = false;

    function setHash(path) {
        suppressHash = true;
        if (window.location.hash !== '#/' + path) {
            window.location.hash = '#/' + path;
        }
        suppressHash = false;
    }

    function selectPage(path, nav, frame, packageData) {
        var pages = packageData.nav || [];
        var page = findPage(path, pages);
        currentPage = page || { path: path };
        nav.querySelectorAll('.pnav-link').forEach(function (l) {
            l.classList.toggle('active', l.getAttribute('data-path') === path);
        });
        var winTitle = document.getElementById('winTitle');
        if (winTitle) winTitle.textContent = (page && (page.title || page.label)) || path;
        if (page && page.markdown) {
            showDocPage(page);
        } else {
            showFramePage(path);
        }
        setHash(path);
        applyFocusMode();
        if (window.LincolnPortal && window.LincolnPortal.resetTray) {
            window.LincolnPortal.resetTray();
        }
    }

    function selectByPath(path, nav, frame, packageData) {
        var link = null;
        var links = nav.querySelectorAll('.pnav-link');
        for (var i = 0; i < links.length; i++) {
            if (links[i].getAttribute('data-path') === path) link = links[i];
        }
        if (link) {
            selectPage(path, nav, frame, packageData);
            return;
        }
        // Path not in registry: load iframe directly.
        currentPage = { path: path };
        showFramePage(path);
        setHash(path);
        applyFocusMode();
    }

    function bindPortal(nav, frame, packageData) {
        nav.addEventListener('click', function (e) {
            var link = e.target.closest('.pnav-link');
            if (!link) return;
            e.preventDefault();
            var path = link.getAttribute('data-path');
            selectPage(path, nav, frame, packageData);
        });

        frame.addEventListener('load', function () {
            try {
                var doc = frame.contentDocument;
                if (doc && doc.body) {
                    var title = doc.querySelector('meta[name="doc-title"]');
                    if (title) {
                        var winTitle = document.getElementById('winTitle');
                        if (winTitle) winTitle.textContent = title.getAttribute('content');
                    }
                }
            } catch (err) {
                // cross-origin iframe; ignore
            }
            notifyFrame(getPreferredTheme());
        });

        window.addEventListener('hashchange', function () {
            if (suppressHash) return;
            var path = decodeURIComponent(window.location.hash.replace(/^#\//, ''));
            if (path) selectByPath(path, nav, frame, packageData);
        });
    }

    function bindPrototypeLinks(nav, frame, packageData) {
        window.addEventListener('message', function (e) {
            if (e.source !== frame.contentWindow) return;
            var data = e.data || {};
            if (data.type === 'lincoln-navigate' && data.path) {
                selectByPath(data.path, nav, frame, packageData);
            }
            if (data.type === 'lincoln-theme-ready') {
                notifyFrame(getPreferredTheme());
            }
        });
    }

    /* ---------- macOS tray (kept for app-shell prototypes) ---------- */

    var DEFAULT_UNREAD = 0;

    function trayMenuHtml(hasUnread) {
        var items = '';
        if (hasUnread) {
            items += '<div class="mi"><span class="mi-avatar"></span><span class="mi-text"><strong>Alice</strong><br>未读消息 2</span></div>';
            items += '<div class="mi"><span class="mi-avatar"></span><span class="mi-text"><strong>Bob</strong><br>未读消息 1</span></div>';
        } else {
            items += '<div class="mi empty">暂无未读消息</div>';
        }
        return items +
            '<div class="mi-sep"></div>' +
            '<a class="mi" href="pages/prototype/app/main/page.html">打开 Lincoln</a>' +
            '<div class="mi-sep"></div>' +
            '<div class="mi danger">退出 Lincoln</div>';
    }

    function initTray() {
        var macTray = document.getElementById('macTray');
        var macTrayMenu = document.getElementById('macTrayMenu');
        if (!macTray || !macTrayMenu) return;

        function renderTrayIcon() {
            var unread = window.LincolnPortalData ? (window.LincolnPortalData.unreadTotal || 0) : 0;
            macTray.innerHTML = '<span class="mt-icon">L</span>' +
                (unread ? '<span class="mt-badge">' + unread + '</span>' : '');
        }
        function renderTrayMenu() {
            var unread = window.LincolnPortalData ? (window.LincolnPortalData.unreadTotal || 0) : 0;
            macTrayMenu.innerHTML = trayMenuHtml(unread > 0);
        }
        function toggleTrayMenu() {
            var showing = macTrayMenu.classList.toggle('visible');
            if (showing) renderTrayMenu();
        }
        function hideTrayMenu() { macTrayMenu.classList.remove('visible'); }

        renderTrayIcon();
        macTray.addEventListener('click', function (e) {
            e.stopPropagation();
            toggleTrayMenu();
        });
        macTrayMenu.addEventListener('click', function (e) {
            var a = e.target.closest('a');
            if (a) {
                e.preventDefault();
                var href = a.getAttribute('href');
                if (href) {
                    var frame = document.getElementById('frame');
                    if (frame) frame.src = href;
                }
                hideTrayMenu();
            } else if (e.target.closest('.mi.danger')) {
                hideTrayMenu();
            }
        });
        document.querySelector('.pstage').addEventListener('click', function (e) {
            if (!macTray.contains(e.target) && !macTrayMenu.contains(e.target)) hideTrayMenu();
        });

        window.addEventListener('message', function (e) {
            var d = e.data || {};
            if (d.type !== 'lincoln-tray-state') return;
            if (!window.LincolnPortalData) window.LincolnPortalData = {};
            if (typeof d.unread === 'number') window.LincolnPortalData.unreadTotal = d.unread;
            renderTrayIcon();
            if (d.open === true) {
                renderTrayMenu();
                macTrayMenu.classList.add('visible');
            } else if (d.open === false) {
                hideTrayMenu();
            }
        });
    }

    function init() {
        var packageData = window.LINC_PACKAGE || {};
        var nav = document.getElementById('pnav');
        var frame = document.getElementById('frame');
        if (nav) renderNav(nav, packageData);
        if (nav) bindNavCollapseButton(nav);
        if (nav && frame) bindPortal(nav, frame, packageData);
        if (nav && frame) bindPrototypeLinks(nav, frame, packageData);
        initTheme();
        initTray();
        initFocusMode();
        var initial = decodeURIComponent(window.location.hash.replace(/^#\//, ''));
        if (initial) {
            selectByPath(initial, nav, frame, packageData);
        } else {
            // Landing: never show a blank page — open the first page, preferring
            // a Markdown doc (the PRD) over a prototype frame.
            var landing = findLandingPage(packageData.nav || []);
            if (landing) selectByPath(landing.path, nav, frame, packageData);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    window.LincolnPortal = { generateUUID: generateUUID, escapeHtml: escapeHtml, setTheme: setTheme };
})();
