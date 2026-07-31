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

<script src="../../../assets/prototype.js"></script>
<script>
(function () {
    var ui = LincolnPrototype.ui;
    var content = ui.frameMain(
        ui.wvPlaceholder('{VIEW_KIND}'),
        { active: '{ACTIVE_ITEM}', base: '../' }
    );
    LincolnPrototype.proto.mount(content);
})();
</script>

<!--
  Variables:
  {TITLE}        - page title shown in the portal window title
  {NAV_GROUP}    - group name used by the portal (e.g. Main)
  {UID}          - stable page uid
  {VIEW_KIND}    - key in LincolnPrototype.data.webviews (chat/contacts/tables)
  {ACTIVE_ITEM}  - sidebar item id to highlight (e.g. chat)
-->

</body>
</html>
