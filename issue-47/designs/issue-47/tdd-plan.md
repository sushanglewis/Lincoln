# TDD 研发计划: issue-47

## 总体策略

按 feature-catalog 的 F 编号分 4 个任务切片,每片遵循 RED → GREEN → REFACTOR。测试先行,全部使用仓库现有 pytest 栈,不新增依赖。

## 切片 1:生成器核心 + harness manifest(F-001/F-006,先行)

**目标**:`scripts/lincoln_harness_adapter.py`,读 `.claude/harnesses/<name>.yaml`,按 targets 生成产物;幂等;`--check` 模式(漂移校验)重新生成到临时目录比对零 diff。

- **RED**:`tests/test_lincoln_harness_adapter.py`
  - 加载 manifest,非法 YAML / 缺字段报错
  - command_map 键不以 `lc-` 开头 → 校验失败
  - 生成到临时 project 目录:产物存在、含"自动生成"头注释、来源路径标注
  - 二次运行零 diff(幂等)
  - `--check` 模式:产物一致返回 0;人为改产物后返回 1
- **GREEN**:实现 `load_manifest()` / `validate_manifest()` / `generate()` / `check_drift()`;转换器 `frontmatter` / `concat` / `copy` / `command-template`。
- **REFACTOR**:与 `lincoln_dependency_manager.py` 共享 yaml 加载与路径工具(如已存在则复用,不重复造)。
- **轻量门控**:本切片同时在生成的命令模板中统一写入"阶段推进前必须运行 `stage_loader.py validate-entry/validate-exit`"约束段(一处模板,三 harness 复用)。

## 切片 2:opencode 适配(F-003)

**目标**:`.claude/harnesses/opencode.yaml` + 生成 `.opencode/agent/lincoln-*.md`、`.opencode/command/lc-*.md`。

- **RED**:断言生成的 agent 文件 frontmatter 仅含 spike 确认字段(description/mode/model/permission);command 文件含 `description` + 正文模板与 `$ARGUMENTS`;`lc-status` 命令 action 指向 `python3 scripts/lincoln-status.py`。
- **GREEN**:编写 opencode.yaml manifest(agents 来自 `.claude/agents/*.md`,commands 来自 command_map);`frontmatter` 转换器支持 opencode 字段白名单。
- **REFACTOR**:字段白名单集中到 manifest 而非代码。

## 切片 3:codex 适配(F-002)

**目标**:`.claude/harnesses/codex.yaml` + 生成 `AGENTS.md`(项目根,拼接角色契约 + 阶段工作流 + `lc-*` 命令说明)与 `~/.codex/prompts/lc-*.md`。

- **前置 spike**(实现第一天,15 分钟):本机/CI 验证 codex prompts 目录与 frontmatter 约定(`docs/slash_commands.md`、`docs/skills.md`);不符则回退为 AGENTS.md 内联命令段,manifest 中移除 prompts target。
- **RED**:断言 `AGENTS.md` 由 `.claude/agents/default.md` + 阶段注册表 + 命令清单拼接,含自动生成头;prompt 文件(若 spike 通过)每个 `lc-*` 一份,action 正确。
- **GREEN**:`concat` 转换器 + codex.yaml manifest。
- **REFACTOR**:拼接顺序与标题层级抽到模板常量。

## 切片 4:`lc-*` 重命名 + 安装集成 + CI(F-004/F-005/F-007/F-008)

**目标**:Claude Code 侧 `lincoln-*` 命令/技能入口统一重命名为 `lc-*`;`lincoln-setup.py bootstrap --harness`;漂移校验接入 static-check;README/CLAUDE.md 更新。

- **RED**:
  - `tests/test_lincoln_setup.py` 新增 `--harness` 参数用例(调用生成器、报告产物清单)
  - 旧名检测:安装输出含迁移提示(模拟 `~/.claude/skills/lincoln-status` 残留)
  - static-check 包含漂移校验步骤(脚本存在且可执行)
- **GREEN**:重命名 `.claude/skills/lincoln-*` → `lc-*`(目录与引用机械替换);setup 增加 `--harness` 子参数串联生成器;`scripts/check-harness-drift.sh` 接入 `static-check.sh`;README 多 harness 安装小节 + 迁移指引;`.gitignore` 增加 `.opencode/`。
- **REFACTOR**:命令映射表单一来源(`.claude/harnesses/command-map.yaml`),三 manifest 引用,CI 校验键集一致。

## 测试与回归基线

- 既有 263 测试全程保持绿(每切片后跑全量)。
- 每切片结束:`pytest tests/ -q` + `bash scripts/static-check.sh`。
- 最终验证(手动):opencode 产物目录结构检查;codex `AGENTS.md` 内容审阅;`lc-status` 在 Claude Code 中可用。

## 风险预案

- codex spike 失败 → 当天回退 AGENTS.md 内联方案,不阻塞切片 4。
- 重命名引发既有测试 fixture 失败 → 先改测试断言再改代码(RED 先于 GREEN)。
