/**
 * Lincoln issue-package portal runtime.
 * Reads window.LINC_PACKAGE from assets/js/package-data.js and renders the
 * left navigation, iframe canvas, and right annotation panel.
 */
(function () {
    'use strict';

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
        ['stories', 'fields', 'rules', 'refs'].forEach(function (key) {
            if (page[key] && page[key].length) {
                html += '<h3>' + ({ stories: '用户故事', fields: '字段', rules: '规则', refs: '引用' }[key]) + '</h3>';
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
        });
    }

    function initPanelToggle() {
        var btn = document.getElementById('pannToggle');
        var pann = document.getElementById('pann');
        if (btn && pann) {
            btn.addEventListener('click', function () {
                pann.classList.toggle('collapsed');
                btn.innerHTML = pann.classList.contains('collapsed') ? '&#10095;' : '&#10094;';
            });
        }
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
        initPanelToggle();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    window.LincolnPortal = { generateUUID: generateUUID, escapeHtml: escapeHtml };
})();
