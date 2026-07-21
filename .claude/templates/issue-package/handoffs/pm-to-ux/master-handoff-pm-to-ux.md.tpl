# PM→UX 交接总览: {design_id}

<!-- status: draft -->
<!-- version: v1.0 -->

> 本文档是人类 PM 向人类 UX 交接 issue #{issue_number} 的**入口文档**。
> 它只建立全局认知，不内嵌细节；细节通过下方链接跳转到对应产物。

---

## 1. 这个故事怎么走到今天

- **Issue**: #{issue_number}
- **分支**: `{branch}`
- **访谈/输入**: `{process_slug}/interviews/{session_id}/summary.md`
- **关键决策记录**: `{process_slug}/docs/decision-record-*.md`

### 已确认的决策

1.
2.

### 已排除的方案

1.
2.

---

## 2. UX 要做什么

### 任务范围

- 在 `{design_id}` 设计包内完成 PM→UX 交接所需的全部设计产物。
- 产物必须满足本节验收标准，方可由 PM 在 `product-design-docs` exit gate 中确认。

### 验收标准

- [ ] 已阅读本总览文档并理解全局上下文
- [ ] 已阅读 `feature-catalog.md` 并确认功能范围
- [ ] 已阅读 `scenarios.md` 与 `user-stories.md` 并确认角色与用户旅程
- [ ] 已阅读 `flows.md` 并确认关键流程
- [ ] 已阅读 `page-map.md` 并确认页面与页面关系
- [ ] 已阅读 `requirements.md` 与 `prd.md` 并确认需求规格
- [ ] 对「开放问题与待决策点」无阻塞性疑问，或已与 PM 对齐

---

## 3. 整体功能

详见: [`{process_slug}/designs/{design_id}/feature-catalog.md`](feature-catalog.md)

### 功能速览

| 功能编号 | 功能名称 | 优先级 |
|----------|----------|--------|
| F-001 | | 高 |
| F-002 | | 中 |

---

## 4. 角色与用户旅程

- 用户画像与场景: [`scenarios.md`](scenarios.md)
- 用户故事: [`{process_slug}/requirements/{session_id}/user-stories.md`](../../requirements/{session_id}/user-stories.md)

### 核心角色

1.
2.

### 核心旅程

1.
2.

---

## 5. 功能流程

详见: [`flows.md`](flows.md)

### 主流程

1.
2.

---

## 6. 页面与页面关系

详见: [`page-map.md`](page-map.md)

### 页面清单

| 页面 | 对应功能 | 上游页面 | 下游页面 |
|------|----------|----------|----------|
| | | | |

---

## 7. 需求规格

- 需求文档: [`{process_slug}/requirements/{session_id}/requirements.md`](../../requirements/{session_id}/requirements.md)
- PRD: [`{process_slug}/requirements/{session_id}/prd.md`](../../requirements/{session_id}/prd.md)

---

## 8. 开放问题与待 UX/PM 决策点

1.
2.

---

## 9. PM 回执

- [ ] PM 已确认 PM→UX 交接内容完整、无歧义

<!-- 准出时替换为: status: approved by PM -->
<!-- status: draft -->

---

## Agent-Agent 交接契约

- 契约文件: `{process_slug}/handoffs/pm-to-ux/pm-to-ux.handoff.yaml`
- UX Agent 必须**先读契约 YAML，再读本总览文档**，然后按契约 `context_pack` 顺序读取 Tier-2 文档。
