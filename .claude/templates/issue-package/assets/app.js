/**
 * Lincoln issue-package portal runtime.
 * Reads window.LINC_PACKAGE from assets/js/package-data.js and renders the
 * left navigation, iframe canvas, and right annotation panel.
 * Also manages light/dark theme synchronization between portal and child pages.
 */
(function () {
    'use strict';

    var THEME_KEY = 'lincoln-theme';

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
        if (btn) btn.textContent = theme === 'dark' ? '☾' : '☀';
    }

    function notifyFrame(theme) {
        var frame = document.getElementById('frame');
        if (frame && frame.contentWindow) {
            frame.contentWindow.postMessage({ type: 'lincoln-theme', theme: theme }, '*');
        }
    }

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

        window.LincolnPortal = window.LincolnPortal || {};
        window.LincolnPortal.resetTray = function () {
            if (!window.LincolnPortalData) window.LincolnPortalData = {};
            window.LincolnPortalData.unreadTotal = DEFAULT_UNREAD;
            renderTrayIcon();
            hideTrayMenu();
        };
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

    function findPage(path, pages) {
        for (var i = 0; i < pages.length; i++) {
            var items = pages[i].items || [];
            for (var j = 0; j < items.length; j++) {
                if (items[j].path === path) return items[j];
            }
        }
        return null;
    }

    function renderNav(container, packageData) {
        var html = '';
        html += '<div class="pnav-header">';
        html += '<div class="pnav-logo">L</div>';
        html += '<div>';
        html += '<div class="pnav-title">Issue #' + escapeHtml(packageData.issue_number || '') + '</div>';
        html += '<div class="pnav-subtitle">' + escapeHtml(packageData.process_slug || '') + '</div>';
        html += '</div></div>';

        if (packageData.current_stage) {
            html += '<div class="pnav-status">阶段: <span class="stage">' + escapeHtml(packageData.current_stage) + '</span></div>';
        }

        html += '<div class="pnav-checklist" id="artifactChecklist">';
        html += '<h4>必要产物清单</h4>';
        html += '<ul>';
        var checklist = packageData.checklist || [
            { key: 'prd', label: 'PRD' },
            { key: 'ui-spec', label: 'UI 规范' },
            { key: 'fields', label: '字段说明' },
            { key: 'decisions', label: '决策记录' },
            { key: 'research', label: '调研笔记' },
            { key: 'prototype-web', label: '原型 · Web 端' },
            { key: 'prototype-mobile', label: '原型 · 手机端' },
            { key: 'prototype-app', label: '原型 · 应用端' },
            { key: 'handoff', label: 'Handoff 交接' },
            { key: 'openspec', label: 'OpenSpec 提案' }
        ];
        var done = packageData.checklist_done || {};
        checklist.forEach(function (item) {
            var cls = done[item.key] ? ' class="done"' : '';
            html += '<li' + cls + ' data-key="' + escapeHtml(item.key) + '">' + escapeHtml(item.label) + '</li>';
        });
        html += '</ul></div>';

        (packageData.nav || []).forEach(function (group) {
            html += '<div class="pnav-group">' + escapeHtml(group.group) + '</div>';
            (group.items || []).forEach(function (item) {
                html += '<a class="pnav-link" data-path="' + escapeHtml(item.path) + '" href="#">' + escapeHtml(item.label) + '</a>';
            });
        });
        container.innerHTML = html;
    }

    function renderPanel(panel, page) {
        if (!page) {
            panel.innerHTML = '<p>点击左侧页面索引加载文档或原型。</p>';
            return;
        }
        var html = '';
        html += '<div class="ann-kicker">' + escapeHtml(page.group || 'Document') + '</div>';
        html += '<h2>' + escapeHtml(page.title || page.label || '') + '</h2>';
        html += '<div class="p-path">' + escapeHtml(page.path) + '</div>';
        if (page.version) {
            html += '<p><strong>版本:</strong> ' + escapeHtml(page.version) + '</p>';
        }
        if (page.status) {
            html += '<p><strong>状态:</strong> ' + escapeHtml(page.status) + '</p>';
        }
        if (page.stage) {
            html += '<p><strong>阶段:</strong> ' + escapeHtml(page.stage) + '</p>';
        }
        if (page.human_confirmed) {
            html += '<p><strong>人工确认:</strong> 已确认</p>';
        }
        if (page.purpose) {
            html += '<h3>用途</h3><p>' + escapeHtml(page.purpose) + '</p>';
        }
        if (page.layout) {
            html += '<h3>布局</h3><p>' + escapeHtml(page.layout) + '</p>';
        }
        ['stories', 'fields', 'rules', 'boundaries', 'exceptions', 'refs'].forEach(function (key) {
            if (page[key] && page[key].length) {
                html += '<h3>' + ({ stories: '用户故事', fields: '字段', rules: '规则', boundaries: '边界', exceptions: '异常流', refs: '引用' }[key]) + '</h3>';
                html += '<ul>' + page[key].map(function (v) { return '<li>' + escapeHtml(v) + '</li>'; }).join('') + '</ul>';
            }
        });
        panel.innerHTML = html;
    }

    function bindPortal(nav, frame, panel, packageData) {
        var pages = packageData.nav || [];

        nav.addEventListener('click', function (e) {
            var link = e.target.closest('.pnav-link');
            if (!link) return;
            e.preventDefault();
            var path = link.getAttribute('data-path');
            frame.src = path;
            nav.querySelectorAll('.pnav-link').forEach(function (l) { l.classList.remove('active'); });
            link.classList.add('active');
            var page = findPage(path, pages);
            renderPanel(panel, page);
            if (page && page.title) {
                var winTitle = document.getElementById('winTitle');
                if (winTitle) winTitle.textContent = page.title;
            }
            if (window.LincolnPortal && window.LincolnPortal.resetTray) {
                window.LincolnPortal.resetTray();
            }
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
    }

    function selectByPath(path, nav, frame, panel, pages) {
        var link = null;
        var links = nav.querySelectorAll('.pnav-link');
        for (var i = 0; i < links.length; i++) {
            if (links[i].getAttribute('data-path') === path) link = links[i];
        }
        if (link) {
            link.click();
            return;
        }
        // Path not in registry: load iframe directly without updating the panel.
        if (frame) frame.src = path;
    }

    function bindPrototypeLinks(nav, frame, panel, pages) {
        window.addEventListener('message', function (e) {
            if (e.source !== frame.contentWindow) return;
            var data = e.data || {};
            if (data.type === 'lincoln-navigate' && data.path) {
                selectByPath(data.path, nav, frame, panel, pages);
            }
            if (data.type === 'lincoln-theme-ready') {
                notifyFrame(getPreferredTheme());
            }
        });
    }

    function init() {
        var packageData = window.LINC_PACKAGE || {};
        var nav = document.getElementById('pnav');
        var frame = document.getElementById('frame');
        var panel = document.getElementById('pannInner');
        if (nav) renderNav(nav, packageData);
        if (frame && panel) bindPortal(nav, frame, panel, packageData);
        if (nav && frame) bindPrototypeLinks(nav, frame, panel, packageData.nav || []);
        initTheme();
        initTray();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    window.LincolnPortal = { generateUUID: generateUUID, escapeHtml: escapeHtml, setTheme: setTheme };
})();
