# Design Review: issue-59

<!-- status: approved -->

## 背景

- Issue: #59
- 关联需求: `issue-59/requirements/2026-07-15-issue-59/requirements.md`
- 关联访谈: `issue-59/interviews/2026-07-15-issue-59/summary.md`
- 审批依据: PM 于 2026-07-15 显式批准实现计划（方案 A)。

## 设计目标

1. 会话启动时,在无状态文件或 `current_stage: not_started` 的情况下,agent 被引导执行"摸排 → 判断 → 确认"开场流程,而不是只收到一行 init 命令。
2. 摸排为概览级(≤8 次只读操作、不读源码、禁深度扫描),判断覆盖"人"的五要素(角色/流程位置/问题/目标/认知象限)。
3. 确认采用 Johari 四象限策略,每轮 ≤3 问,收敛到"明确验收标准 + 确定执行路径"。
4. README 双语言版不再教终端命令,全部转为自然语言入口。

## 范围

### 范围内

- `.claude/hooks/on-session-start.sh`:fresh repo / issue 号不明 / not_started 三路径注入开场引导块;`LINCOLN_SKIP_DEP_CHECK` 测试旁路。
- `.claude/skills/lc-workflow-router/`:新增 `prompts/intake-prompt.md`;SKILL.md 与 router-prompt.md 扩展触发与前置依赖。
- `.claude/agents/default.md`、`CLAUDE.md`、`clarify-requirements/prompts/main.md`、`lc-workflow/SKILL.md`、`stages/workflow-router.yaml`:契约与措辞同步。
- `README.md` / `README.en.md`:消灭命令代码块,新增开场行为说明。
- 测试:`test_session_start_guidance.py`、`test_intake_skill.py`、`test_readme_natural_language.py`。

### 范围外

- LEW-31(GH #52)纯插件免脚手架改造(独立大工程)。
- codex prompts 真实 CLI 端到端验证(LEW-29 遗留)。
- 新建独立 intake/recon 阶段(方案 B,已否决)。
- `.claude-plugin/plugin.json` 补录 lc-stage/lc-wf(既有不一致,与本 issue 无关)。

## 方案对比

- 方案 A(选定):扩展 workflow-router + hook 注入。复用已有"上下文采集 → 置信度 → 确认问题"机制;不碰 stage 注册表/schema;约 10 改 + 4 新文件。
- 方案 B(否决):新建独立 intake 阶段。语义更贴合但需改 5 个 workflow 模板、schema、harness 适配、command-map,爆炸半径大,违反 KISS/YAGNI。
