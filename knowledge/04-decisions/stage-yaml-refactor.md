# Stage YAML 重构决策

## 元信息

- **决策编号**: DEC-001
- **日期**: 2026-07-11
- **相关需求**: [[p0-lc-framework]]
- **相关功能**: [[p0-lc-overall-framework]]
- **状态**: 已采纳

---

## 背景

在 P0 框架之前，Lincoln 的阶段定义采用文件夹结构：每个阶段是一个目录，内含多个元数据文件和提示词。这种结构在阶段数量增加后带来维护负担，也导致 Agent 启动时需要读取多个文件才能组装出当前阶段上下文。

## 问题

- 新增阶段需要创建目录并在多处注册。
- 阶段元数据与提示词混放，职责不清。
- 难以用单一 schema 校验阶段定义。
- 会话启动时读取文件次数多，注入逻辑复杂。

## 考虑的方案

| 方案 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| A. 保持文件夹结构 | 每个阶段一个目录，内含多个文件 | 文件组织直观 | 元数据分散，新增阶段成本高 |
| B. 单 YAML + 子目录提示词 | 阶段元数据收敛为 YAML，提示词保留子目录 | 结构清晰、可 schema 校验、扩展性好 | 需要一次重构 |
| C. 所有内容单文件 | 元数据 + 长 prompt 放在一个 Markdown/YAML | 文件最少 | prompt 过大，system prompt 膨胀 |

## 决策

采用 **方案 B**：阶段元数据使用单 YAML（`.claude/stages/<stage>.yaml`），阶段专属提示词保留在 `.claude/stages/<stage>/` 子目录下的 `AGENTS.md`、`CHECKLIST.md`、`PROMPT.md`、`SKILLS.md`。

## 理由

1. **降低阶段维护成本**：新增阶段只需添加一个 YAML 和一组提示词文件。
2. **可校验**：YAML 可以用 JSON Schema 统一校验，避免拼写或结构错误。
3. **职责分离**：YAML 负责导航和元数据，Markdown 负责执行细节。
4. **兼容 hooks**：`on-session-start.sh` 读取 YAML 后即可知道需要加载哪些提示词文件。

## 影响

- 需要一次性重构现有阶段目录。
- `scripts/stage_loader.py`、`lincoln-status.py`、`lincoln-audit.py` 等脚本需要适配新结构。
- 后续阶段扩展遵循同一约定。

## 相关链接

- [[p0-lc-overall-framework]]
- [[p0-lc-framework]]
- `.claude/stages/stage-manifest.yaml`
- `.claude/schemas/stage-definition.schema.json`
