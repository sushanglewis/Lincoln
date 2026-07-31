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

<div class="window full" id="win"></div>

<script src="../../../assets/prototype.js"></script>
<script>
(function () {
    var ui = LincolnPrototype.ui;
    // Render an overlay inside the app window. Choose one of the helpers below
    // depending on the scenario being demonstrated.
    var content = ui.avatarMenu('../');
    // var content = ui.aboutDialog('../');
    // var content = ui.toast('通知发送者', '这是一条系统通知的摘要内容。', LincolnPrototype.data.appName);
    LincolnPrototype.proto.mount(content);
})();
</script>

</body>
</html>
