# 流程图: {design_id}

## 用户场景与流程

<!-- 对应 PRD 第 2 章用户故事与第 4 章业务流程图；此处按场景展开关键任务流。 -->

### 场景一：场景名称

- **用户**:
- **目标**:
- **关键步骤**:
  1.
  2.

## 主流程

```mermaid
graph TD
    A[开始] --> B[步骤]
    B --> C[结束]
```

## 分支流程

### 分支一

```mermaid
graph TD
    A[条件] -->|分支 A| B[处理 A]
    A -->|分支 B| C[处理 B]
```

## 界面流转图

<!-- 描述用户完成主任务时经历的页面/状态序列，可补充页面编号。 -->

```mermaid
graph TD
    P1[P-001 页面名称] -->|点击/跳转| P2[P-002 页面名称]
    P2 -->|返回| P1
```

## 状态机

- 状态 1 → 状态 2（事件）
- 状态 2 → 状态 3（事件）

---

*PM→UX 交接：本流程图是 [`handoffs/pm-to-ux/master-handoff-pm-to-ux-v*.md`](../handoffs/pm-to-ux/master-handoff-pm-to-ux-v1.0.md) 的 Tier-2 产物。*
