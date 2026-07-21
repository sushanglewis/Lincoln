# 用户故事: 2026-07-21-lew-49-handoff

<!-- status: approved -->
<!-- version: v1.0 -->

## 角色

### 人类 PM

- 作为 PM，我希望在 clarify 阶段就知道 PM→UX 交接产物清单，以便我能在 product-design-docs exit gate 前把它们全部澄清。
- 作为 PM，我希望 `product-design-docs` 的 exit gate 检查 handoff 契约是否有效且版本一致，以便我不会把未完成的交接传递给 UX。

### 人类 UX

- 作为 UX，我希望在 `issue-{N}/handoffs/pm-to-ux/` 中找到一份带版本的主文档，以便我一读即懂全局。
- 作为 UX，我希望主文档通过链接路由到需求、场景、流程、页面关系，而不是把所有内容内嵌，以便我按需深入。

### UX Agent

- 作为 UX Agent，我希望从 `pm-to-ux.handoff.yaml` 开始阅读，以便我知道该读什么、按什么顺序读。
- 作为 UX Agent，我希望契约中明确禁止直接读原始录音，除非 Tier-2 链接要求，以便我避免信息过载。

### Lincoln 系统

- 作为 Lincoln，我希望 `documents.yaml` 能索引 handoff 文档并显示版本，以便任何 Agent 快速发现它们。
- 作为 Lincoln，我希望 `init-lincoln-branch.sh` 预创建 `handoffs/pm-to-ux/` 目录，以免 PM 漏放交接物。
