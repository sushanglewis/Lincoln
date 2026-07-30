# plan-tdd-development

You are executing the Lincoln workflow step `tdd-development-plan`: turn the confirmed product design and prototype into a TDD development plan.

## Goal

Create `{process_slug}/pages/docs/tdd-plan.html` as the bridge from product design to OpenSpec and GitHub Issues.

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
6. Run `python scripts/stage_loader.py --stage tdd-development-plan --action record-artifacts`.

## Rules

- Keep the plan executable by an engineer without requiring extra product decisions.
- Every task slice must map back to a design artifact and acceptance criterion.
- Do not generate OpenSpec artifacts in this step.
- After completion, tell the user to run: `claude propose-with-openspec <session_id> <design_id> <change_name>`.
