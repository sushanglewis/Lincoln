# SKILLS.md - 产品原型阶段

## 主要技能命令

- `claude build-product-prototype <session_id> <design_id>`
  - 基于已确认设计文档生成字段规格、UI 规格和 Pencil 原型
  - 参数：
    - `session_id`: 访谈会话 ID，如 `2026-06-27-stakeholder`
    - `design_id`: 产品设计 ID（kebab-case），如 `checkout-redesign`
  - 完整 prompt 文件：`.claude/skills/interview-workflow/prompts/build-product-prototype.md`

## 辅助技能

- `claude workflow-continue`
  - 当人类 PM 修改文件后，恢复被暂停的工作流

## 校验器使用

- 入口校验：`python .claude/skills/interview-workflow/validators/validate.py --phase entry --check product_design_approved --args <design_id>`
- 出口校验：`python .claude/skills/interview-workflow/validators/validate.py --phase exit --check prototype_artifact_complete --args <design_id>`
- 校验失败时：停止 loop、报告失败项、给出修复建议、等待人类处理

## MCP 工具

### Pencil MCP（核心）

- `pencil__get_editor_state` - 获取当前编辑器状态和 schema（操作 `.pen` 前必须调用）
- `pencil__batch_design` - 生成或修改设计节点
- `pencil__batch_get` - 读取设计节点信息
- `pencil__snapshot_layout` - 检查布局问题（裁剪、重叠）
- `pencil__get_screenshot` - 获取截图（仅作为辅助审阅材料）
- `pencil__export_nodes` - 导出节点为图片（可选）
- `pencil__export_html` - 导出为 HTML（可选，非主要审批产物）

### 标准文件工具（仅限 Markdown 规格文件）

- `Read` - 读取设计文档和已生成的规格文件
- `Write` - 创建 `fields.md` 和 `ui-spec.md`
- `Edit` - 修改规格文件

## 错误处理

- 设计文档未批准：暂停工作流，提示用户先完成 `product-design-docs` 阶段
- Pencil 工具调用失败：检查 schema 是否已获取，重试或报告错误
- 布局问题（裁剪/重叠）：使用 `snapshot_layout` 定位问题，通过 `batch_design` 修复
- 校验失败：根据校验器输出补充缺失内容，重新校验
- `.pen` 文件损坏：通过 Pencil 工具重新生成，绝不使用普通文件工具修复

## 重要提醒

- `.pen` 文件是加密格式，**绝对禁止**使用 Read、Write、Edit、Grep 等普通文件工具操作
- 所有 `.pen` 操作必须通过 Pencil MCP 工具完成
- 人类 PM 可直接在 Pencil 应用中修改并保存 `.pen` 文件
