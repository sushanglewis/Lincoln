## 关联 Issue

Closes #

## 变更说明

<!-- 这个 PR 解决了什么问题？方案是什么？（一个 PR 只解决一个问题） -->

## 贡献者护栏自查

- [ ] 已搜索确认不与现有 issue/PR 重复
- [ ] 本 PR 只解决一个问题
- [ ] 未移除或绕过任何 human_gate / 阶段门控
- [ ] 生成方式已披露（模型 + harness + 版本）：

## 测试

- [ ] `pytest tests/ -q` 全绿
- [ ] `bash scripts/static-check.sh` 通过
- [ ] 涉及 stage/skill/角色契约变更时，已附 benchmark 前后对比（无回归）
- [ ] 涉及 `.claude/` 事实源变更时，已重新生成 harness 产物并通过 drift 检查

## 测试计划

<!-- Reviewer 应如何验证这个改动？ -->
