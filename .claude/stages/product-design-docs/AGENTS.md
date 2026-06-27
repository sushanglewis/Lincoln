# AGENTS.md - 产品设计文档阶段

## 阶段目的

将已确认的需求转化为面向人类 PM 评审的简洁产品设计文档包。产出包括：设计评审入口文档、用户场景、功能清单、数据模型、流程图和可行性分析。本阶段不生成原型或代码。

## 入口要求

- 前置阶段 `clarify-requirements` 已完成
- `requirements/<session_id>/requirements.md` 包含 `<!-- status: approved -->` 或 `[x] PM 已确认需求`
- 需求文档包含背景、问题、用户、方案、验收标准等必要章节

## 允许操作

- 读取 `requirements/<session_id>/` 下的需求文件
- 在 `designs/<design_id>/` 目录下创建新的 Markdown 文档
- 使用 Mermaid 语法在 `flows.md` 中绘制流程图
- 查询当前官方技术文档或开源项目主仓库以获取技术框架建议
- 向人类 PM 提出澄清问题（每次最多 3 个）
- 在 `design-review.md` 中添加 `<!-- status: approved -->` 标记

## 禁止操作

- 禁止创建 Pencil 原型（`.pen` 文件）
- 禁止生成 TDD 研发计划或 OpenSpec artifact
- 禁止修改 `requirements/` 下的原始需求文件
- 禁止在需求未确认时生成设计文档
- 禁止绕过校验继续工作流

## 副作用策略

- 所有产物写入 `designs/<design_id>/` 目录，不修改已有文件
- 设计文档应可追溯回原始需求文件和访谈时间戳
- 如需修改已发布的设计文档，保留变更历史或变更说明

## 人类门控规则

- 本阶段标记 `human_gate: true`
- 文档生成后，必须请人类 PM 审阅 `design-review.md` 及关联文档
- 只有 PM 显式确认（输入 confirm 或在 `design-review.md` 中添加批准标记）后，才能进入下一阶段
- PM 拒绝时，根据反馈更新 artifact 并重新校验

## 下一阶段

- PM 确认后，提示用户运行：`claude build-product-prototype <session_id> <design_id>`
- 下一 stage：`product-prototype`
