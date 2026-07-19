# 场景分析: issue-59

<!-- status: approved -->

## 用户画像

- 首次接触 Lincoln 的潜在用户:不愿学命令,打开对话即期待被引导。
- 熟练 PM:已在某个 issue 工作包中,期待不被打扰、直接进入阶段工作。
- 框架维护者:在任意仓库/分支调试 Lincoln 自身。

## 核心场景

### 场景一: fresh repo 首次打开(无状态文件,非 issue 分支)

- 触发条件: 会话启动 hook 解析不到 workflow-stage.yaml,分支不是 issue-*。
- 用户行为: 用户说"帮我看看这个项目"或直接抛出一个想法。
- 预期结果: hook 输出"=== Lincoln 开场引导 ==="块;agent 执行 ≤8 次只读摸排(顶层结构/README 头部/knowledge 索引/issues/访谈存在性/首条消息),输出"我了解到的情况"摘要 + 处境判断 + ≤3 个象限确认问题;用户确认后才推荐并启动工作流(team: agent 代为 init;solo: lc-wf-*)。

### 场景二: issue 分支工作包未启动(not_started)

- 触发条件: 分支为 issue-N,hook auto-init 工作包后 `current_stage: not_started`。
- 用户行为: 用户进入会话准备开工。
- 预期结果: hook 在状态摘要末尾输出 not_started 版开场引导;agent 先读 documents.yaml 与关联 issue 复核信息,展示目标/验收标准/起始阶段判断,经 ≤3 问确认后才运行 validate-entry。

### 场景三: 活跃阶段(已有进行中工作流)

- 触发条件: `current_stage` 为 ingest/clarify/... 等进行中阶段。
- 用户行为: 用户回来继续工作。
- 预期结果: 不注入开场引导;按原 Session Startup Protocol 汇报阶段并 validate-entry。

## 边界场景

- `gh` 不可用或未认证:跳过 issues 信号,在判断中标注该信息缺失,不阻塞。
- 仓库无 README / 无 knowledge/:以存在的信号为准,置信度降级,提问补齐。
- 用户首条消息已包含完整意图与 issue 号:摸排后判断可为高置信度,确认问题可减少到 1 个(复述确认)。

## 异常场景

- 摸排后仍无法形成任何判断:输出"信息不足"说明 + 最多 3 个最直接的问题,不编造判断。
- 用户拒绝确认或持续改方向:更新 `.context/lc-intake.md` 继续澄清,不进入实现;必要时提示用户明确最终目标。
