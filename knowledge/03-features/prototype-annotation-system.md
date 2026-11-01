# Axure 式原型标注系统

## 元信息

- **来源需求**: GitHub issue #155
- **状态**: 已实施
- **标签**: lincoln, prototype, annotations, axure, review, presentation

## 业务知识

旧原型只要求 hotspots 数组存在，无法保证 PM 讲清交互、状态与异常；目标缺失还会被静默跳过。新系统用数字角标、四分类说明抽屉和分步演示支持团队评审。

每页必须说明角色、场景、目标、入口、完成结果、页面结构、交互反馈、完整状态、异常恢复与数据规则。五类基础状态逐项枚举，不适用必须有业务理由，叙述使用业务语言。

## 技术知识

- `pageData.annotations` 是结构化说明载体，旧 hotspots 保持兼容。
- `prototype.js` 提供角标、抽屉、演示、高亮、状态导航与键盘操作。
- `lincoln_prototype_annotations.py` 提供确定性内容校验。
- `prototype_annotations_complete` 接入共享 Stage/Workflow，仅对 core-v2 强制。
- 标准见 `docs/prototype-annotation-standard.md`，实施说明见 `docs/designs/prototype-annotation-system.md`。
