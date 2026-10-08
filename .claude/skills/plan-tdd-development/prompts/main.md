# plan-tdd-development

You are executing the Lincoln workflow step `tdd-development-plan`: turn the confirmed product design and prototype into a TDD development plan, then reverse-drive the PRD with test scenarios so gaps close before development.

## Goal

Create `{process_slug}/pages/docs/tdd-plan.html` as the bridge from product design to OpenSpec and GitHub Issues, and produce `{process_slug}/pages/docs/prd-cross-validation.html` so every test scenario (正常/边界/异常) challenges the PRD — SDD tests reverse-drive PRD completeness.

## Input

- `session_id`: the interview session identifier
- `design_id`: the product design identifier

## 子技能准备

在执行本 prompt 前：
1. 调用 `superpowers:writing-plans` 规划 `tdd-plan.html` 结构。
2. 遵循 `superpowers:test-driven-development` 方法论：确保每个任务切片都是“先写失败测试 → 最小实现 → 重构”序列。
3. 在 `tdd-plan.html` 的 Markdown source 头部加入：
   `> **Required sub-skill:** Use superpowers:test-driven-development for all implementation`

## Steps

### Phase 1 — TDD 计划

1. Verify that `{process_slug}/pages/docs/ui-spec.html` contains `<!-- prototype-status: approved -->` or `[x] PM 已确认原型`.
2. Confirm `{process_slug}/designs/<design_id>/prototype.pen`, `{process_slug}/pages/docs/fields.html`, and the design review package exist.
3. Read the confirmed design docs and inspect the `.pen` through Pencil tools if visual structure is needed.
4. Write `{process_slug}/pages/docs/tdd-plan.html` using `.claude/templates/issue-package/page-doc.html.tpl`. It must embed Markdown in `<script type="text/markdown" id="docSource">` with a `<!-- version: v1.0 -->` marker and meta tags (`doc-title`, `nav-group`, `doc-version`, `doc-uid`). Content must include:
   - Source links to `requirements.html`, `design-review.html`, `fields.html`, `ui-spec.html`, and `prototype.pen`
   - Acceptance criteria mapping
   - Test scenarios grouped by user workflow
   - Red/green/refactor implementation sequence
   - Unit, integration, contract, UI, and regression test boundaries
   - Data fixtures and validation cases
   - Task slices suitable for OpenSpec tasks and GitHub Issues
   - Risks, dependencies, and out-of-scope items
5. Add `<!-- status: ready-for-openspec -->` when the plan is complete.

### Phase 2 — PRD 交叉验证（测试反向驱动 PRD）

6. **场景回问**：从 tdd-plan 的测试场景（正常、边界、异常）逐一回问 `{process_slug}/pages/docs/prd.html`：该场景涉及的业务规则与验收标准在 PRD 中是否有明确答案？逐项记录「场景 → PRD 答案（章节 + 条文）」，PRD 无答案者标记为缺口。
7. **对齐闭环**：建立业务流程步骤 ↔ 原型页面双向对齐矩阵——PRD 业务流程图中的每个步骤至少有 1 个原型页面承载；每个原型页面归属于某流程步骤或用户故事。任一侧对不上即为缺口（流程中断或原型多余）。
8. **渲染报告**：写 `{process_slug}/pages/docs/prd-cross-validation.md`（顶部含 `<!-- version: v1.0 -->`），用 `lincoln_render.py` 渲染为 `{process_slug}/pages/docs/prd-cross-validation.html`：

   ```bash
   python scripts/lincoln_render.py \
     --stage tdd-development-plan \
     --target {process_slug}/pages/docs/prd-cross-validation.html \
     --title "PRD 交叉验证报告" \
     --markdown {process_slug}/pages/docs/prd-cross-validation.md
   ```

   报告必须含：场景 → PRD 答案映射表、缺口清单、决策记录表（缺口 / 闭环方式 / PM 决策 / 理由）、PRD 修订回执。
9. **闭环缺口**：每个缺口由人类 PM 决策二选一——
   - **修复**：修订 `prd.md`，bump `<!-- version: vX.Y -->`，运行 `python scripts/lincoln_prd.py freeze` 重新冻结，然后重跑 Phase 2；
   - **接受**：在决策记录表中记录理由与影响，经人类 PM 明确认可。

   全部缺口闭环后，在报告 markdown 末尾追加 `<!-- cross-validation: pass prd-version: vX.Y -->`（vX.Y = 当前 PRD 版本）并重新渲染。未闭环前禁止写入该标记。
10. Run `python scripts/stage_loader.py --stage tdd-development-plan --action record-artifacts`.

## Output Artifacts

- `{process_slug}/pages/docs/tdd-plan.html`
- `{process_slug}/pages/docs/prd-cross-validation.html`（含场景→PRD 答案映射、缺口清单、决策记录、闭环标记）

## Rules

- Keep the plan executable by an engineer without requiring extra product decisions.
- Every task slice must map back to a design artifact and acceptance criterion.
- Do not generate OpenSpec artifacts in this step.
- 交叉验证发现的 PRD 缺口不得自行编造业务答案，必须交回人类 PM 决策（修复或接受）。
- pass 标记中的版本必须与当前 PRD 版本一致；PRD 后续任何改动都会使标记失效，须重跑 Phase 2。
- After completion, tell the user to run: `claude propose-with-openspec <session_id> <design_id> <change_name>`.
