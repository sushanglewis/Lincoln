# 流程图: issue-47

## 主流程:安装与适配生成

```mermaid
graph TD
    A[用户运行 lincoln-setup.py bootstrap --harness X] --> B{依赖检查<br/>check-skill-dependencies}
    B -->|缺失| C[确认后安装 skills/CLIs]
    B -->|通过| D[加载 .claude/harnesses/X.yaml]
    C --> D
    D --> E[按 targets 从 .claude/ 生成适配产物]
    E --> F[写入白名单目录<br/>project 或 user scope]
    F --> G[结构校验 + 旧命令残留检测]
    G --> H[报告:已生成产物/lc-* 命令清单/迁移提示]
```

## 分支流程

### 分支一:弱能力 harness 的门控执行

```mermaid
graph TD
    A[阶段推进请求] -->|harness 有 hooks<br/>claude-code| B[hooks 自动注入阶段上下文<br/>+ 强制校验]
    A -->|harness 无 hooks<br/>codex/opencode| C[lc-* 命令提示词约束:<br/>先跑 stage_loader validate-entry]
    B --> D[stage_loader.py 执行准入/准出校验]
    C --> D
    D -->|通过| E[继续阶段工作]
    D -->|失败| F[暂停并报告缺失产物/待审批]
```

### 分支二:CI 漂移校验

```mermaid
graph TD
    A[CI 触发] --> B[运行生成器到临时目录]
    B --> C{与当前产物/期望快照比对}
    C -->|零 diff| D[通过]
    C -->|有 diff| E[失败:提示运行生成命令并提交更新]
```

## 状态机

- 未安装 → 已适配(事件:bootstrap --harness 完成)
- 已适配 → 漂移(事件:`.claude/` 变更未重新生成)
- 漂移 → 已适配(事件:重新运行生成器)
- 任意状态 → 安装失败(事件:校验/写入失败;原子回滚,不留半成品)
