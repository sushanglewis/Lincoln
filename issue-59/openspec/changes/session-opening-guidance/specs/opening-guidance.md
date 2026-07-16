# 规格: session-opening-guidance

<!-- status: approved -->

## ADDED Requirements

### Requirement: 开场引导注入

会话启动 hook SHALL 在以下两种情形输出"=== Lincoln 开场引导 ==="指令块:(a) 解析不到 workflow-stage.yaml 且当前分支非 issue-\*(或 issue 号无法解析);(b) 状态文件存在且 `current_stage` 为 `not_started`。情形 (a) 输出后 exit 0;情形 (b) 在状态摘要末尾输出。`current_stage` 为进行中阶段时 MUST NOT 输出该块。

#### Scenario: fresh repo

- **WHEN** 仓库无 Lincoln 状态文件且分支非 issue-*
- **THEN** hook 输出开场引导块,包含摸排/判断/确认三步骨架与 `intake-prompt.md` 指针,并 exit 0

#### Scenario: 工作包未启动

- **WHEN** 状态文件存在且 current_stage 为 not_started
- **THEN** hook 在状态摘要末尾输出开场引导块,指示先完成处境确认再运行 validate-entry

#### Scenario: 活跃阶段不打扰

- **WHEN** current_stage 为进行中阶段(如 clarify)
- **THEN** hook 不输出开场引导块,按原流程注入阶段上下文

### Requirement: 概览摸排

intake 流程 SHALL 定义概览级摸排:信号清单(顶层结构、README 头部、knowledge 索引、issues、访谈/录音存在性、用户首条消息),只读操作上限 ≤8 次,MUST NOT 读取源码文件内容,MUST NOT 调用深度扫描(lc-build-codebase-knowledge),除 `.context/lc-intake.md` 外 MUST NOT 写文件。

#### Scenario: 摸排深度限制

- **WHEN** agent 执行开场摸排
- **THEN** 只读操作不超过 8 次,不读源码,不做深度扫描

### Requirement: 处境判断与认知象限确认

intake 流程 SHALL 输出五要素处境判断(角色/流程位置/问题/目标/象限初判 + 置信度),并按 Johari 四象限(知道自己知道/知道自己不知道/不知道自己知道/不知道自己不知道)设计确认问题,每轮 SHALL 不超过 3 个;用户确认目标与执行路径前 MUST NOT 开始实现性工作。

#### Scenario: 象限策略

- **WHEN** 某目标被判断为"知道自己不知道"
- **THEN** agent 直接回答并提供背景(coach),而非反问

### Requirement: README 自然语言化

README.md 与 README.en.md 的用户面向章节 MUST NOT 包含终端命令调用(代码块与内联);双文件结构 SHALL 保持镜像(同级标题数一致)。

#### Scenario: 命令教学移除

- **WHEN** 用户阅读快速开始章节
- **THEN** 所有操作以"对 Agent 说 X"自然语言表述,无 bash/python 命令
