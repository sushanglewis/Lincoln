<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="doc-title" content="{TITLE}">
<meta name="nav-group" content="{NAV_GROUP}">
<meta name="page-uid" content="{UID}">
<title>{TITLE}</title>
<!-- Asset paths assume this page lives at pages/prototype/{web,mobile,overlays}/*.html (depth 3). Adjust if placed elsewhere. -->
<link rel="stylesheet" href="../../../assets/style.css">
</head>
<body class="proto-page" data-page-uid="{UID}">

<div class="proto-frame">
    <div class="proto-placeholder">
        <h2 data-uid="{UID}-title">{TITLE}</h2>
        <p data-uid="{UID}-desc">在此放置原型内容。所有交互元素必须携带 data-uid 属性。</p>
        <button class="btn primary" data-uid="{UID}-btn-primary">主要操作</button>
        <button class="btn default" data-uid="{UID}-btn-default">次要操作</button>
    </div>
</div>

<script src="../../../assets/app.js"></script>
</body>
</html>
