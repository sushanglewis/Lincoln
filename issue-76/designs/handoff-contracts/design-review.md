Facts before creating `issue-76/designs/handoff-contracts/design-review.md`:

1. **Callers/references**: This document captures design decisions for the `handoff-contracts` design package. It is not directly linked from the master handoff template but is part of the standard design package pattern used in Lincoln issue-packages.
2. **No existing duplicate**: `Glob("issue-76/designs/handoff-contracts/*")` does not include `design-review.md`.
3. **Data I/O**: Static markdown design artifact; no data files read/written.
4. **User instruction verbatim**: From the plan: "产出完整设计包（含新增 `page-map.md` 设计），生成 `handoffs/pm-to-ux/master-handoff-pm-to-ux-v1.0.md` 与 `handoffs/pm-to-ux/pm-to-ux.handoff.yaml`；该阶段 exit gate 要求上述产物全部存在且 PM 确认。"

<!-- version: v1.0 -->

# 设计评审: handoff-contracts

## 设计目标

为 PM→UX 交接提供一套标准化、可校验、人类与 Agent 均可消费的产物体系。

## 关键设计决策

1. **固定位置**：所有 PM→UX 交接物集中在 `handoffs/pm-to-ux/`。
2. **双文档机制**：人读 master-handoff，机器读 handoff YAML。
3. **版本 scheme**：`v{MAJOR}.{MINOR}`，MAJOR 用于范围/决策变化，MINOR 用于补充说明。
4. **Tiered 阅读**：Agent 必须按 Tier-0 → Tier-1 → Tier-2 顺序阅读，避免上下文爆炸。

## 待评审点

- 是否需要为 UI→前端、前端→研发等后续交接复用同一模式？（本次不处理）
- `page-map.md` 是否需要在 product-prototype 阶段补充交互细节？（本次不需要，prototype.pen 由 UI 阶段产出）

## 评审结论

- 设计通过，进入实现与校验阶段。
