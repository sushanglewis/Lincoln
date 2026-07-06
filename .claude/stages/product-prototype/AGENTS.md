# AGENTS.md - 产品原型阶段

## 阶段目的

将已确认的产品设计文档转化为可交互的 Pencil 原型和开发可用的 UI/字段规格文档。产出包括：字段规格、UI 规格和 `.pen` 原型文件。PM 可直接在 Pencil 中查看和修改原型。

## 入口要求

- 前置阶段 `product-design-docs` 已完成
- `{process_slug}/designs/<design_id>/design-review.md` 包含 `<!-- status: approved -->` 或 `[x] PM 已确认设计文档`
- 设计文档包完整（6 个文件均存在且非空）

## 允许操作

- 读取 `{process_slug}/designs/<design_id>/` 下的全部设计文档
- 创建 `{process_slug}/designs/<design_id>/fields.md` 和 `{process_slug}/designs/<design_id>/ui-spec.md`
- 使用 Pencil MCP 工具创建或更新 `{process_slug}/designs/<design_id>/prototype.pen`
- 使用 `snapshot_layout` 检查布局问题并修复
- 向人类 PM 展示原型并请求审阅
- 在 `ui-spec.md` 中添加 `<!-- prototype-status: approved -->` 标记

## 禁止操作

- **禁止**使用普通文件工具（Read、Write、Edit、Grep 等）读取或修改 `.pen` 文件
- 禁止在设计文档未确认时生成原型
- 禁止生成 TDD 研发计划或 OpenSpec artifact
- **禁止将 TaskCreate/TaskUpdate 当作消息占位符**：本阶段必须直接向人类 PM 展示原型/提出问题，不得用任务工具拆分或延迟“发消息”动作
- 禁止绕过校验继续工作流
- 禁止将截图或 HTML 作为主要审批产物（仅可作为辅助审阅材料）

## 副作用策略

- `.pen` 文件只能通过 Pencil MCP 工具或 Pencil 应用操作
- 字段规格和 UI 规格以 Markdown 形式写入，便于开发者直接阅读
- 原型修改后，开发者应以 PM 确认保存后的 `.pen` 文件作为最终开发参照
- 所有产物写入 `{process_slug}/designs/<design_id>/` 目录

## 人类门控规则

- 本阶段标记 `human_gate: true`
- 原型生成后，必须请人类 PM 在 Pencil 应用中打开并审阅 `prototype.pen`
- PM 可直接在 Pencil 中修改并保存原型
- 只有 PM 显式确认后，才能在 `ui-spec.md` 中添加批准标记并进入下一阶段
- PM 拒绝时，根据反馈使用 Pencil 工具修改原型并重新校验

## 下一阶段

- PM 确认后，提示用户运行：`claude plan-tdd-development <session_id> <design_id>`
- 下一 stage：`tdd-development-plan`
