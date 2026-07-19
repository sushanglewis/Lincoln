# TDD 计划: issue-59

<!-- status: approved -->

## 测试策略

本变更为 prompt/hook/文档工程,测试以"行为守卫 + 内容标记 + 文档规则"三层为主:

1. **行为测试**(hook):直接执行 `.claude/hooks/on-session-start.sh`,断言三种状态下的输出。
2. **内容标记测试**(prompt/契约):断言关键机制词存在于对应文件,防止后续编辑丢机制。
3. **文档规则测试**(README):解析 fence 与内联 code,断言用户面向章节无终端命令调用,双语言结构镜像。

基线:既有 269 个测试必须保持全绿。测试环境变量 `LINCOLN_SKIP_DEP_CHECK=1` 用于密封 hook 的依赖检测分支。

## 测试清单(RED → 先写失败测试)

### tests/test_session_start_guidance.py

- `test_fresh_repo_injects_opening_guidance`:无状态文件 + 非 issue 分支 cwd → rc=0,stdout 含"开场引导"与 `intake-prompt.md`。
- `test_not_started_stage_injects_opening_guidance`:状态文件 `current_stage: not_started` → stdout 含"开场引导"与 `validate-entry`。
- `test_active_stage_does_not_inject_guidance`:状态文件 `current_stage: clarify` → stdout 不含"开场引导",含阶段上下文(回归保护)。

### tests/test_intake_skill.py

- intake-prompt.md 存在,含四象限标签、"摸排"、"验收标准"、每轮问题上限"3"、禁止深度扫描声明。
- `lc-workflow-router/SKILL.md` 含 `not_started` 触发条件;`router-prompt.md` 引用 `intake-prompt.md`。
- `.claude/agents/default.md` 与 `CLAUDE.md` 含"开场引导"。
- `clarify-requirements/prompts/main.md` 含"认知象限"与"验收标准"。
- `.claude/stages/workflow-router.yaml` 的 goal 含"摸排"。

### tests/test_readme_natural_language.py

- `test_no_script_invocations_in_code_fences`:两 README 全部 fence(含缩进)无 `python3? scripts/`、`scripts/*.sh` 调用(目录树 fence 不误伤)。
- `test_user_facing_sections_have_no_inline_commands`:快速开始/工作状态与交接/多 harness 三节无内联脚本命令。
- `test_readme_mirror_structure`:双文件 `## ` 标题数一致。
- `test_nl_table_present`:zh 含 `| 你说 | Agent 做 |`,en 含 `| You say | Agent does |`。

## 实现顺序(GREEN)

1. `.claude/skills/lc-workflow-router/prompts/intake-prompt.md`(新建,指针目标先于指针)
2. `lc-workflow-router/SKILL.md`、`prompts/router-prompt.md`、`.claude/stages/workflow-router.yaml`
3. `.claude/hooks/on-session-start.sh`(四处变更)
4. `.claude/agents/default.md`、`CLAUDE.md`
5. `.claude/skills/clarify-requirements/prompts/main.md`、`.claude/skills/lc-workflow/SKILL.md`
6. `README.md`、`README.en.md`
7. 三个测试文件落位并跑绿

## 验证(IMPROVE)

```bash
.venv/bin/python3 -m pytest tests/ -q
bash scripts/static-check.sh
python3 scripts/lincoln-setup.py generate-harness --harness codex
python3 scripts/lincoln-setup.py generate-harness --harness opencode
bash scripts/check-harness-drift.sh
```

手动 smoke:(1) fresh repo 开会话 → 引导块 → 摸排 → 摘要 + ≤3 问;(2) issue 分支 not_started → auto-init → 引导块 → 确认后 validate-entry。

## 覆盖目标

- 新增约 13 个测试;hook 三分支(fresh/not_started/active)全覆盖;README 规则防回归。
