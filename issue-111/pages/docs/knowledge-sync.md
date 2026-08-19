# Issue-111 知识同步记录

## 业务知识

- Lincoln v1.6.x 已切换到全局 npm 插件模型：`npm install -g @sushanglewis/lincoln` + `lincoln install --yes`。
- 旧版 `npx lincoln-install` / `npx lincoln-update` 已弃用，迁移命令为 `lincoln migrate-project`。
- Lincoln 当前核心能力包括：阶段驱动工作流引擎、产物追溯（lc-one-id）、Markdown-first issue-package 文档、`--render-stage` 批量渲染、Mermaid 本地渲染。

## 技术知识

- `README.md` / `README.en.md` 是项目主要介绍入口，需与 `.version-bump.json` 版本锁步。
- `SKILL.md` 是 skill 市场元数据文件，安装指引必须与全局 CLI 一致。
- 文档内相对链接需保持存活；中英 README 标题结构需对齐。

## 关联

- Issue: #111
- PR: 待填充
- 事实清单：见 `issue-111/pages/docs/fact-sheet.md`
