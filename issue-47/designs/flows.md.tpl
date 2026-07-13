# 流程图: {design_id}

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

## 状态机

- 状态 1 → 状态 2（事件）
- 状态 2 → 状态 3（事件）
