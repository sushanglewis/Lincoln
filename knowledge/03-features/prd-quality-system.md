# PRD Quality System

## 元信息

- **来源需求**: GitHub issue #142
- **GitHub Issue**: [#142](https://github.com/sushanglewis/Lincoln/issues/142)
- **实现 PR**: #149–#153 及集成发布 PR
- **状态**: 已实施
- **标签**: lincoln, prd, quality, traceability, review, prototype, tdd

---

## 业务知识

### 背景与问题

Lincoln v1.8.4 的 PRD 门控主要验证 13 个标题、内容卫生、快照和人工 pass 标记。空章节或纯占位仍可能通过，单一 PM approved 也不能代表设计、研发和 QA 已能执行。

### 核心机制

- core-v2 用 15 章内容契约回答证据、指标、范围、业务行为、验收和发布问题。
- 稳定 REQ/US/AC/FLOW/TEST ID 把叙事 PRD 与结构化关系连接起来。
- pm/design/engineering/qa 对同一版本负责不同质量维度。
- clarify、prototype、TDD 分别形成需求基线、交付基线和测试闭环。

### 价值

团队可以区分“文档存在”和“需求可执行”，并在研发前发现缺指标、断链、缺页面、缺测试和未经评审的变更；旧 PRD 与轻量流程仍保持兼容。

---

## 技术知识

### 实现概述

- `lincoln_prd_quality.py`：core-v2 内容校验与 legacy 自动识别。
- `lincoln_traceability.py` + `prd-traceability.schema.json`：阶段化追溯校验。
- `lincoln_prd_review.py` + `prd-review.schema.json`：四方评审、版本重置与交付基线。
- `lincoln_prototype_traceability.py`：sidecar 与 HTML pageData 双向页面校验。
- 共享 `validate_stage.py` / `lc-workflow/validators/validate.py` 对 core-v2 强制新门控，对 legacy/轻量包跳过。
- full-prd/lightweight artifact profile 区分完整交付与有意裁剪。

### 关键决策

- Markdown 继续承载叙事，YAML 只承载关系与评审，避免 PRD 变成难以阅读的巨型表单。
- 新 sidecar 在 Stage/Workflow 中声明为 optional，以兼容存量包；core-v2 标记触发强制完整性校验。
- 确定性 CI 只验证可机器判断的底线，证据真实性、方案取舍和体验质量由四方评审负责。

### 相关文档

- [[p0-lc-overall-framework]]
- `docs/prd-quality-standard.md`
- `docs/designs/prd-quality-system-v1.11-spec.md`
- `docs/designs/prd-review-lifecycle.md`
