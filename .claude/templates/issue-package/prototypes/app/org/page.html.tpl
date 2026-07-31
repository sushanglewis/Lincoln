<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="doc-title" content="{TITLE}">
<meta name="nav-group" content="{NAV_GROUP}">
<meta name="page-uid" content="{UID}">
<meta name="prototype-base" content="../../../../">
<title>{TITLE}</title>
<link rel="stylesheet" href="../../../../assets/prototype.css">
</head>
<body>

<script src="../../../../assets/prototype.js"></script>
<script>
(function () {
    var ui = LincolnPrototype.ui;
    var orgs = LincolnPrototype.data.orgs;

    function orgRow(org) {
        var currentBadge = org.current
            ? '<span class="ro-tag" style="background:var(--brand-light);color:var(--brand-dark)">当前组织</span>'
            : '';
        var switchBtn = org.current
            ? ''
            : '<button class="btn default sm" data-name="' + ui.escapeHtml(org.name) + '" data-uid="{UID}-btn-switch-' + ui.escapeHtml(org.initial) + '">切换</button>';
        return '<div class="set-row" data-name="' + ui.escapeHtml(org.name) + '">'
            + '<div class="sr-control">' + ui.avatar(org.initial, null, true)
            + '<div><div style="font-weight:600;font-size:14px">' + ui.escapeHtml(org.name) + '</div>'
            + '<div style="font-size:12px;color:var(--text-3)">' + ui.escapeHtml(org.url) + '</div>'
            + '<div style="font-size:12px;color:var(--text-2);margin-top:2px">我的角色：' + ui.escapeHtml(org.role) + '</div></div></div>'
            + '<div class="sr-control">' + currentBadge + switchBtn + '</div>'
            + '</div>';
    }

    var list = orgs.map(orgRow).join('');

    var body = '<div class="page-body"><div class="col">'
        + '<div class="set-row" style="padding-top:4px;border-bottom:none" data-uid="{UID}-header">'
        + '<div class="sr-label" style="font-weight:700">已添加组织</div></div>'
        + list
        + '<div class="set-row" style="border-bottom:none;margin-top:8px" data-uid="{UID}-add-row">'
        + '<div class="sr-label">需要访问其他组织？</div>'
        + '<a class="btn primary sm" style="width:auto" href="../onboarding/org-url.html" data-uid="{UID}-btn-add">添加组织</a>'
        + '</div></div></div>';

    var side = '<div class="page-side">'
        + '<a class="ps-back" href="../main/chat.html" data-uid="{UID}-back">&#8249; 返回</a>'
        + '<div class="ps-title">组织管理</div>'
        + '<a class="ps-item active" href="org-list.html" data-uid="{UID}-nav-org">我的组织</a>'
        + '</div>';

    var page = '<div class="page">' + side
        + '<div class="page-main"><div class="page-head"><h2 data-uid="{UID}-title">我的组织</h2></div>'
        + body + '</div></div>';

    var content = ui.frameMain(page, { base: '../' });
    LincolnPrototype.proto.mount(content);
})();
</script>

<!--
  Variables:
  {TITLE}        - page title shown in the portal window title
  {NAV_GROUP}    - group name used by the portal (e.g. Org)
  {UID}          - stable page uid
-->

</body>
</html>
