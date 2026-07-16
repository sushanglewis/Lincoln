# 流程图: issue-59

<!-- status: approved -->

## 主流程

```mermaid
graph TD
    A[会话启动] --> B{hook 解析状态文件}
    B -->|无状态文件 + 非 issue 分支| C[注入开场引导块 A]
    B -->|无状态文件 + issue 分支| D[auto-init 工作包]
    D --> E[current_stage = not_started]
    B -->|有状态文件| F{current_stage?}
    F -->|not_started| E
    F -->|活跃阶段| G[原路径: 注入阶段上下文]
    E --> H[状态摘要末尾注入开场引导块 B]
    C --> I[agent 执行 intake 流程]
    H --> I
    I --> J[摸排: ≤8 次只读, 概览级]
    J --> K[判断: 五要素 + 置信度]
    K --> L[展示判断 + Johari 确认, 每轮 ≤3 问]
    L --> M{用户确认?}
    M -->|是| N[路由: team init / solo lc-wf / validate-entry]
    M -->|否| L
```

## 分支流程

### 分支一: 确认问题的象限策略

```mermaid
graph TD
    A[目标项] -->|知道自己知道| B[复述确认题: 防会错意]
    A -->|知道自己不知道| C[直接回答 + coach: 给背景]
    A -->|不知道自己知道| D[展示已有资产: knowledge/issue/文档]
    A -->|不知道自己不知道| E[探查题: 暴露风险与缺失]
```

### 分支二: 路由出口

```mermaid
graph TD
    A[确认完成] -->|无工作包 + team 意图| B[agent 代为 init-lincoln-branch.sh]
    A -->|无工作包 + solo 意图| C[router-prompt 选模板, lc-wf-* 启动]
    A -->|已有工作包 not_started| D[validate-entry 进入第一阶段]
```

## 状态机

- 未引导 → 引导中(hook 注入开场引导块)
- 引导中 → 已确认(用户确认目标与路径)
- 引导中 → 引导中(每轮 ≤3 问,更新 lc-intake.md)
- 已确认 → 已路由(init / lc-wf-* / validate-entry 其一完成)
