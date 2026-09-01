# 用户故事: 2026-08-28-issue-70

## 用户故事一：框架维护者评估可移植模式

- **作为**：Lincoln 框架维护者
- **我希望**：获得一份结构化的 OpenHands / TeamAI 模式调研报告
- **以便**：判断哪些机制（如事件驱动状态、skill 注入、安全策略、代码图）可以迁移到 Lincoln
- **验收标准**：
  - 报告中每个可借鉴模式都标明来源项目、具体机制、与 Lincoln 的映射点
  - 报告给出 P0/P1/P2 优先级建议

## 用户故事二：产品经理做出采纳决策

- **作为**：Lincoln 产品经理
- **我希望**：看到加权评分表和明确的推荐结论
- **以便**：基于业务价值、技术匹配度、维护成本做出采纳/暂缓决策
- **验收标准**：
  - 评分维度覆盖 business / technical / maintenance / docs / integration
  - 推荐结论区分“立即采纳”“后续评估”“不适用”

## 用户故事三：未来贡献者追溯设计依据

- **作为**：未来 Lincoln 贡献者
- **我希望**：在知识库中看到可追溯到本次 issue 的决策记录
- **以便**：理解 Lincoln 某些设计（如 sub-agent 委托、harness 抽象）来自哪些外部项目
- **验收标准**：
  - 知识库 `knowledge/06-references/` 下有对应参考文档
  - 参考文档链接回 `issue-70/docs/research/openhands-teamai-research-oss-options.md` 与 Linear LEW-70
