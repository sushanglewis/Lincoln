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
<link rel="stylesheet" href="../../../assets/prototype.css">
</head>
<body>

<div id="win"></div>

<script src="../../../assets/prototype.js"></script>
<script>
(function () {
    var ui = LincolnPrototype.ui;
    var org = LincolnPrototype.data.currentOrg;

    var hero = '<div class="org-hero">'
        + ui.orgLogo(org.initial, 'lg')
        + '<div class="org-name" data-uid="{UID}-org-name">' + ui.escapeHtml(org.name) + '</div>'
        + '</div>';

    var body = '<div class="field" data-uid="{UID}-field-email">'
        + '<label>企业邮箱</label>'
        + '<input type="email" value="' + ui.escapeHtml(LincolnPrototype.data.currentUser.email) + '" data-uid="{UID}-input-email">'
        + '</div>'
        + '<div class="field" data-uid="{UID}-field-password">'
        + '<label>密码</label>'
        + '<input type="password" placeholder="请输入密码" data-uid="{UID}-input-password">'
        + '</div>'
        + '<div class="field-row" data-uid="{UID}-remember">'
        + '<label class="checkbox-line"><input type="checkbox" checked data-uid="{UID}-chk-remember">记住我</label>'
        + '<a class="link" data-uid="{UID}-link-forgot">忘记密码？</a>'
        + '</div>'
        + '<button class="btn primary" data-uid="{UID}-btn-login">登录</button>';

    var content = ui.onboardingCard('{TITLE}', body, { hero: hero });
    LincolnPrototype.proto.mount(content);
})();
</script>

<!--
  Variables:
  {TITLE}        - page title shown in the portal window title
  {NAV_GROUP}    - group name used by the portal (e.g. Onboarding)
  {UID}          - stable page uid
-->

</body>
</html>
