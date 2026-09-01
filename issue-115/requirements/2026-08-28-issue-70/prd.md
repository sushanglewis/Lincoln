# PRD: 2026-08-28-issue-70

## 产品目标

为 Lincoln 框架提供关于 OpenHands 与 TeamAI 两个开源 coding-agent 项目的可借鉴模式评估，形成一份可追溯、可评审、可映射到 Lincoln 子系统的研究笔记，并登记到 Lincoln 的持久 OSS 项目注册表中。

## 功能需求

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 项目信息核实 | 确认 OpenHands / TeamAI 的许可证、技术栈、Star 数、最近活跃度 | P0 |
| 加权评分表 | 按 business 30% / technical 25% / maintenance 20% / docs 15% / integration 10% 评分 | P0 |
| 可借鉴模式映射 | 将两个项目的具体机制映射到 Lincoln 文件/子系统 | P0 |
| 推荐结论 | 给出 P0/P1/P2 采纳优先级与大致工作量 | P0 |
| OSS 注册表更新 | 在 `oss/projects.yaml` 中登记两个项目为 `reference_only` | P0 |
| 决策记录 | 记录研究范围、模板选择理由、框架兼容性处理 | P1 |

## 非功能需求

- 研究笔记必须可读、结构清晰，便于人类 PM 评审。
- 所有外部引用必须提供来源 URL。
- 不下载或执行第三方代码（符合 `lc-explore-opensource` 安全约束）。
- 阶段校验（entry/exit）必须通过 `scripts/stage_loader.py` 执行。

## 发布标准

- `issue-70/docs/research/openhands-teamai-research-oss-options.md` 已完成并通过 PM 评审。
- `oss/projects.yaml` 已更新并通过 YAML 解析校验。
- `explore-opensource` 阶段 `validate-entry` 与 `validate-exit` 均显示 PASS。
- 相关产物路径已通过 `record-artifacts` 写回 `issue-70/workflow-stage.yaml`。

## 风险

- 两个项目仍在快速迭代，部分机制可能在未来版本中变化。
- 某些模式（如 OpenHands 的 workspace factory、TeamAI 的代码图）与 Lincoln 当前架构差异较大，直接移植成本高。
- `oss-first-design` 工作流与 `clarify` 阶段的 `ingest` 前置条件存在不一致，需要显式记录处理方式。
