# 可行性分析: issue-59

<!-- status: approved -->

## 业务可行性

- 全部机制复用既有资产:workflow-router 已有上下文采集/置信度/确认问题;hook 注入是已验证机制(依赖检测、auto-init 均同款);clarify 已有多轮澄清框架。无新依赖、无新 CLI。
- 用户价值直接对应 issue:降低学习曲线(README 去命令化)+ 开场自然引导(摸排/判断/确认/开展)。

## 技术可行性

- hook 变更约 40 行 bash:两个 echo 块替换 + 一个 flag 分支,风险低;`LINCOLN_SKIP_DEP_CHECK` 旁路使 hook 首次可单测。
- intake-prompt.md 为纯 prompt 资产,pytest 内容标记可守卫。
- README 改写为文档工程,fence/标题结构双语言镜像已由现状验证(各 17 个 `## ` 标题),测试可自动防回归。
- default.md 变更经 harness adapter 派生到 codex/opencode,`check-harness-drift.sh` 已接入 static-check,可验证一致性。

## 开源项目 / 框架参考

- Johari window(认知象限模型):四象限提问策略的理论来源,issue 原文直接点名。
- 既有实现参考:`lc-workflow-router/prompts/router-prompt.md`(信号采集与置信度输出范式)、`clarify-requirements/prompts/main.md`(多轮澄清与 ≤3 问节奏)。

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| hook 注入文本过长稀释系统提示 | 中 | 只注入指针 + 四步骨架,完整流程放 intake-prompt.md |
| 开场确认打扰熟练用户 | 中 | 摸排概览级 + 操作上限;活跃阶段不注入;高置信度时问题可减到 1 个 |
| codex/opencode 端行为漂移 | 低 | 派生重新生成 + drift 检查进 CI |
| 双 README 改写不同步 | 低 | pytest 守卫标题数一致与无命令规则 |

## 建议方案

方案 A:扩展 lc-workflow-router + hook 注入 + default.md(PM 已于 2026-07-15 批准)。理由:复用度最高、爆炸半径最小、不碰 stage 注册表与 schema;方案 B(新建独立 intake 阶段)语义更贴合但牵动面过大,不符合 KISS/YAGNI。
