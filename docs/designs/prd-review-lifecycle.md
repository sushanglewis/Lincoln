# PRD 四方评审与版本生命周期

> 适用范围：Lincoln 完整 PRD 工作流。本文定义 `prd-review.yaml` 的独立契约；Stage、Workflow 和 validator registry 的统一接线由集成切片负责。

## 1. 目标与不变量

PRD 的“已写完”不等于“可交付”。`prd-review.yaml` 将 PM、设计、研发、QA 的质量责任记录为可机器校验的签收，满足以下不变量：

1. 一份评审文件只对应一个 `prd_version`，版本格式与 PRD 的 `vX.Y` 标记一致。
2. `pm`、`design`、`engineering`、`qa` 四个角色必须全部存在，且对**同一版本**均为 `approved`，才能形成最终交付基线。
3. 任一 `pending` 或 `changes_requested` 都会阻断交付；旧版本的批准不能用于新版本。
4. PRD 内容发生实质变化时必须升版，并通过 `reset-for-version` 使旧签收失效；不得直接改写旧签收来冒充重审。
5. 评审不替代 human gate、需求/原型/测试追溯校验或不可变 PRD 快照。所有证据必须指向同一版本。

建议将文件放在 `{process_slug}/pages/docs/prd-review.yaml`，与主线 PRD 一起纳入 issue 工作包。

## 2. 角色责任

| 角色 | 签收前必须确认的重点 |
| --- | --- |
| `pm` | 问题证据、目标用户、业务价值、成功指标、范围/非目标、优先级和开放决策完整且一致。 |
| `design` | 用户流程、业务状态、交互与异常路径可体验，HTML 原型覆盖需求，设计与 PRD 无冲突。 |
| `engineering` | 业务规则无歧义，技术可行性、数据/接口、依赖、非功能需求与发布约束可执行。 |
| `qa` | 验收标准可测试，边界/异常/回归场景可识别，需求—原型—测试追溯完整。 |

`actor` 记录实际评审人或可审计的团队身份；`notes` 记录决策依据、待修复项或关联讨论。`changes_requested` 是明确的阻断决定，不应只写在聊天中。

## 3. 文件契约

```yaml
schema_version: 1.0.0
prd_version: v1.0
reviews:
  pm:
    status: approved
    actor: pm-alice
    reviewed_at: '2026-11-01T10:00:00Z'
    notes: 范围与指标已确认
  design:
    status: changes_requested
    actor: designer-bob
    reviewed_at: '2026-11-01T10:05:00Z'
    notes: 补充无数据与提交失败状态
  engineering:
    status: pending
    actor: null
    reviewed_at: null
    notes: ''
  qa:
    status: pending
    actor: null
    reviewed_at: null
    notes: ''
```

- `status` 仅允许 `pending`、`approved`、`changes_requested`。
- `pending` 的 `actor`、`reviewed_at` 必须为 `null`；其余两种状态必须提供非空 `actor` 和 UTC ISO8601 时间。
- 时间只接受以 `Z` 结尾的 UTC 时间，例如 `2026-11-01T10:05:00Z`；禁止本地无时区时间和 `+08:00` 等偏移。
- Schema：`.claude/schemas/prd-review.schema.json`。

## 4. CLI

记录一个角色；首次写入会创建其余三个角色的 `pending` 项。未传 `--reviewed-at` 时，决定类状态使用当前 UTC 时间。

```bash
python3 scripts/lincoln_prd_review.py record \
  --file issue-145/pages/docs/prd-review.yaml \
  --prd-version v1.0 --role pm --status approved \
  --actor pm-alice --notes '范围与指标已确认'

python3 scripts/lincoln_prd_review.py record \
  --file issue-145/pages/docs/prd-review.yaml \
  --prd-version v1.0 --role design --status changes_requested \
  --actor designer-bob --notes '补充异常路径'
```

校验最终交付基线。任何缺审、修改请求或版本漂移均以非零状态退出：

```bash
python3 scripts/lincoln_prd_review.py validate \
  --file issue-145/pages/docs/prd-review.yaml --prd-version v1.0
```

PRD 升版后显式重置。该命令把 `prd_version` 改为目标版本，并将四方状态、`actor`、`reviewed_at`、`notes` 重置为初始值；随后必须重新评审：

```bash
python3 scripts/lincoln_prd_review.py reset-for-version \
  --file issue-145/pages/docs/prd-review.yaml --prd-version v1.1
```

`record` 检测到版本漂移会失败并保留原文件，调用方必须先确认 PRD 已升版，再执行重置；不会在记录评审时自动清空其他角色的决定。

## 5. 阶段生命周期与 freeze 语义

### 5.1 clarify：需求基线

1. PM 与相关者澄清问题、证据、用户、指标、范围、故事、业务规则和验收标准，形成带 `vX.Y` 的 PRD。
2. 四方可从本阶段开始评审并尽早提出修改请求。若修改 PRD 的实质内容，先升版、重置评审，再重审受影响内容。
3. 人类 PM 确认需求且本阶段既有质量门通过后，使用 `lincoln_prd.py freeze` 冻结该版本快照，形成**需求基线**。这里的 freeze 表示需求讨论有可追溯起点，不等于最终四方交付签收。
4. 后续所有设计、原型和测试证据引用该版本；如果基线变化，旧快照保留，新版本重新走评审与冻结。

### 5.2 product-prototype：交付基线

1. 设计、研发和 QA 用 HTML 原型、字段/UI 规格和流程反向检查 PRD，关闭所有 `changes_requested`。
2. PRD 未变化时，四方在同一版本完成签收；`validate --prd-version vX.Y` 必须通过。
3. 若原型暴露 PRD 缺口并需要修改叙事 PRD，必须升版、重置、四方重审，并重新执行受影响的追溯/原型校验。
4. 四方同版本批准与原型阶段质量门均完成后，对当前版本重新 freeze，形成**交付基线**。同一版本已有快照时不得覆盖；因此，凡需重新冻结的 PRD 内容修复必须先升版。

### 5.3 tdd-development-plan：反向验证、重审与重冻结

1. 工程和 QA 用测试场景反向挑战业务规则、验收标准、异常流程、非功能需求及原型追溯。
2. 测试只补足可执行性且 PRD 无需变化时，保留当前版本，记录人类 PM 的缺口处置决定，并让交叉验证证据继续指向该版本。
3. 任何需要修改 PRD 的修复都必须：升版 → `reset-for-version` → 修复并重新运行受影响的原型/追溯/测试校验 → 四方重审并全部批准 → 对新版本 freeze。
4. 新交付基线建立前，旧版本的评审通过和交叉验证 pass 均视为失效；不得沿用旧批准绕过 TDD 发现的缺口。

## 6. 完成定义

一个可交付 PRD 版本至少同时具备：

- 当前 PRD、追溯关系、原型/测试交叉验证和 `prd-review.yaml` 的版本完全一致；
- 四方全部 `approved`，无未解决的 `changes_requested`；
- 当前阶段要求的 human gate 和质量校验通过；
- 当前版本的不可变快照存在，后续修复通过新版本而不是覆盖历史完成。
