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
    var u = LincolnPrototype.data.currentUser;

    var body = ui.row('头像', '<div class="sr-control" data-uid="{UID}-avatar">'
            + ui.avatar(u.initial, null, true)
            + '<button class="btn default sm" data-uid="{UID}-btn-change-avatar">更换头像</button></div>')
        + ui.ro('姓名', u.name)
        + ui.ro('账号', u.email)
        + ui.row('昵称', '<input type="text" value="' + ui.escapeHtml(u.nickname) + '" data-uid="{UID}-input-nickname">')
        + ui.ro('职位', u.position)
        + ui.ro('部门', u.department)
        + ui.ro('性别', u.gender)
        + ui.ro('手机', u.phone)
        + ui.ro('企业邮箱', u.email);

    var foot = '<a class="btn default sm" href="../main/chat.html" data-uid="{UID}-btn-cancel">取消</a>'
        + '<a class="btn primary sm" style="width:auto" href="../main/chat.html" data-uid="{UID}-btn-save">保存</a>';

    var content = ui.frameMain(
        ui.settingsPage('{ACTIVE_ITEM}', '{TITLE}', body, foot, { base: '../' }),
        { base: '../' }
    );
    LincolnPrototype.proto.mount(content);
})();
</script>

<!--
  Variables:
  {TITLE}        - page title shown in the portal window title
  {NAV_GROUP}    - group name used by the portal (e.g. Settings)
  {UID}          - stable page uid
  {ACTIVE_ITEM}  - settings nav item id to highlight (e.g. profile)
-->

</body>
</html>
