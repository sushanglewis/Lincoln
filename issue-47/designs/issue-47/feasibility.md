# 可行性分析: issue-47

## 业务可行性

- 需求来源明确(PM 提出并逐轮确认范围),目标用户(codex/opencode 使用者)与 Lincoln 现有用户群高度重叠。
- 增量交付路径清晰:生成器 + 两个适配器 + 重命名,可在一个 issue 内完成 MVP;分发渠道等重资产明确推后。

## 技术可行性

- **生成器**:纯本地文件转换(YAML → markdown/配置),仓库已有 Python + PyYAML 栈,无新依赖;`.claude/` 结构稳定(schema 版本化)。
- **codex**:spike 确认官方 docs 存在 `agents_md.md`、`slash_commands.md`、`skills.md` 机制(AGENTS.md 项目级指令、`~/.codex/prompts/*.md` 自定义斜杠命令、skills 机制)。具体目录/字段细节在实现阶段以真实 codex CLI 验证一次即可,风险可控。
- **opencode**:spike 已通过 Context7 获取源码级 schema 确认:
  - agents:`.opencode/agent/*.md`,frontmatter 支持 `description/mode(primary|subagent|all)/model/temperature/tools/permission/steps` 等;
  - commands:`.opencode/command/*.md`,frontmatter `description/agent/model`,正文为模板并支持 `$ARGUMENTS`;
  - plugins:`.opencode/plugin(s)/*.{ts,js}`,可做会话事件轻量 hook。
- **门控**:`stage_loader.py` 本就是独立 CLI,不依赖 Claude Code 运行时;弱 harness 以提示词约束调用顺序,语义无损。
- **重命名**:命令入口集中在 `.claude/skills/`(lincoln-*)与少量脚本引用,grep 可穷举,机械替换 + 测试守护。

## 开源项目 / 框架参考

- opencode 官方 agents/commands/plugin 机制(sst/opencode,MIT)。
- codex CLI 的 AGENTS.md / prompts / skills 机制(openai/codex)。
- 仓库内既有生成器先例:`scripts/sync-external-agents.sh`(manifest → 规范化产物 + NOTICES),可复用其"manifest 驱动 + 自动标注来源"的模式。

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| codex prompts/skills 目录约定与假设不符 | codex 命令入口不可用 | 实现阶段第一天做真实 CLI 验证;回退方案为 AGENTS.md 内联命令说明 |
| opencode 版本演进导致 frontmatter 变化 | 生成产物校验失败 | 只输出 spike 确认的稳定字段子集;CI 漂移校验及早暴露 |
| 破坏性重命名引发存量用户困惑 | 升级体验差 | 安装时旧名检测 + 迁移提示;README 迁移小节;发布说明醒目标注 |
| 生成器与 `.claude/` 演进脱节 | 产物腐烂 | PM 已决策:CI 漂移校验(重新生成零 diff)强制同步 |
| 三 harness 行为细微差异 | 用户认知混乱 | 命令清单文档为唯一口径;差异写入能力矩阵与降级说明 |

## 建议方案

按 design-review 的范围执行 MVP:先生成器核心 + opencode 适配(spike 已完全确认),再 codex 适配(含一次真实 CLI 验证),最后 `lc-*` 重命名与文档;门控与 CI 保持轻量实现。预估实现阶段 3-4 个工作包,单 PR 或按工作包拆 2-3 个 commit。
