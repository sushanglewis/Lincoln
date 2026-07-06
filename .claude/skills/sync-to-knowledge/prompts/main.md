# sync-to-knowledge

You are executing the Lincoln workflow step `sync-knowledge`: after a PR is merged, review the code and issue, then update the project Obsidian vault with both business and technical knowledge.

## Goal

Ensure every merged issue leaves behind a complete, linked feature note in `knowledge/`.

## Input

- `issue_number`: the GitHub Issue number
- `pr_number`: the merged Pull Request number

## 子技能准备

在执行本 prompt 时：
1. 调用 `gsd-docs-update` 生成或更新知识文档，确保文档内容与代码库一致。
2. 若同步失败，调用 `gsd-forensics` 进行失败复盘，找到根因后再继续。

## Steps

1. Read `.github/openspec-config.yml` for the target repository.
2. Fetch the issue and PR details using `gh` or GitHub MCP.
3. Find the linked requirement and OpenSpec change from the issue body.
4. Read the related files:
   - `{process_slug}/requirements/<session>/requirements.md`
   - `{process_slug}/openspec/changes/<change>/design.md`
   - `{process_slug}/openspec/changes/<change>/tasks.md`
5. Review the merged PR diff.
6. Create or update `knowledge/03-features/<feature-slug>.md` using the feature-note template.
7. Ensure the feature note has both:
   - `业务知识` section: background, user needs, acceptance criteria, value
   - `技术知识` section: implementation overview, code locations, design decisions, dependencies, API/data models
8. Create/update supporting notes:
   - `knowledge/01-interviews/<session>.md` if not exists
   - `knowledge/02-requirements/<requirement-id>.md`
   - `knowledge/04-decisions/<decision-id>.md` for any architecture decisions
9. Use Obsidian wikilinks (`[[...]]`) to connect notes.
10. Check for conflicts with existing knowledge. If a conflict is found, pause and ask the human PM.

## Output Artifacts

- `knowledge/03-features/<feature-slug>.md`
- `knowledge/02-requirements/<requirement-id>.md`
- `knowledge/01-interviews/<session>.md`
- `knowledge/04-decisions/<decision-id>.md` (if applicable)
- Updated `knowledge/00-index.md`

## Rules

- A feature note without both business and technical sections is invalid.
- Every note must link back to its source interview, requirement, issue, and PR.
- Do not overwrite human edits without noting the changes.
- After completion, summarize what was updated in the vault.
