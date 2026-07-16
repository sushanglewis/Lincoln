# OpenSpec 任务: session-opening-guidance

<!-- status: approved -->

## 任务清单

- [ ] T1: 新建 `.claude/skills/lc-workflow-router/prompts/intake-prompt.md`(摸排/判断/Johari/路由/禁忌)
- [ ] T2: 扩展 `lc-workflow-router/SKILL.md`、`prompts/router-prompt.md`、`.claude/stages/workflow-router.yaml`
- [ ] T3: 改造 `.claude/hooks/on-session-start.sh`(dep-check 旁路 + 两处引导块注入 + not_started flag + 末尾输出)
- [ ] T4: 更新 `.claude/agents/default.md`、`CLAUDE.md`
- [ ] T5: 更新 `clarify-requirements/prompts/main.md`(认知象限 + 收敛标准)、`lc-workflow/SKILL.md`
- [ ] T6: 改写 `README.md` 与 `README.en.md`(消灭命令块 + 新增开场行为小节 + NL 表扩充)
- [ ] T7: 新增 `tests/test_session_start_guidance.py`、`tests/test_intake_skill.py`、`tests/test_readme_natural_language.py`
- [ ] T8: 验证:pytest 全绿、static-check、harness 双端重新生成、drift 检查

## 验收标准

- [ ] 双 README 用户面向章节零终端命令(pytest 守卫)
- [ ] hook 三分支注入行为正确(pytest 守卫)
- [ ] intake-prompt 含摸排上限、五要素判断、Johari 四象限、≤3 问、收敛标准(pytest 守卫)
- [ ] 269 基线全绿 + 新增约 13 例;drift 检查通过

## 关联 Issue

- #59
