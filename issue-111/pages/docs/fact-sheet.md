# Issue-111 事实清单

## 版本事实

- 当前版本：**v1.6.3**（`.version-bump.json`、`packages/lincoln/package.json` 一致）
- 最近 releases：v1.6.3（2026-08-15）、v1.6.2（2026-08-12）、v1.6.1（2026-08-11）、v1.6.0（2026-08-06）、v1.5.0（2026-08-05）

## v1.6.x 已合并 PR 与能力

| PR | 对应 issue | 能力 |
|---|---|---|
| #101 | #100 | Lincoln 全局插件分发：通过 `npm install -g @sushanglewis/lincoln` 安装，`lincoln install` 同步框架到 `~/.claude/`、`~/.codex/`、`~/.opencode/` |
| #102 | #102 | PM 阶段提示词、产物、工作流模板对齐 |
| #104 | #103 | 引导式 npm 安装与 release 自动化 |
| #107 | #106 | `lc-one-id` skill：通过稳定 ID（`feature/*`、`page/*`、`field/*`、`doc/*`）追溯上游产物 |
| #110/#109 | #108 | Markdown-first issue-package 文档、Mermaid 渲染、`--render-stage` 批量渲染 |

## 已关闭 issues（与介绍性文档相关）

- #100：全局插件分发 RFC
- #103：完善 npm 安装引导程序
- #106：优化 Lincoln 架构与提示词
- #108：issue-package 模板僵化（文档侧已由 #109/#110 解决）
- #83（v1.3.0）：上一次 README refresh

## CLI 命令清单（`packages/lincoln/src/commands/`）

- `lincoln --version` / `lincoln -v`
- `lincoln install` — 全局安装并同步框架
- `lincoln install --yes` — 非交互式安装
- `lincoln install --yes --harnesses claude-code,opencode`
- `lincoln update` — 更新 Lincoln
- `lincoln doctor --json` — 环境诊断
- `lincoln init-project` — 在项目中启用 `.lincoln.yaml`
- `lincoln migrate-project` — 从 vendored 模式迁移
- `lincoln use` — 使用/切换工作流
- `lincoln record` — 录音相关

## 文档现状

- `README.md`：已反映 v1.6.3 全局插件模型，但「Lincoln 能做什么」未补 v1.6.1–v1.6.3 能力。
- `README.en.md`：结构与中文版对齐，内容同步滞后风险。
- `SKILL.md`：严重过时，仍以 `npx lincoln-install` / `npx lincoln-update` 为主路径。
- `USAGE.md`：大体较新，但介绍性段落需复核。

## 更新要点

1. README「最新版本」callout 补 v1.6.1–v1.6.3 要点。
2. README「Lincoln 能做什么」补 lc-one-id、Markdown-first docs、Mermaid、stage 批量渲染。
3. SKILL.md 重写安装指引，以 `npm install -g @sushanglewis/lincoln` + `lincoln install --yes` 为主路径，旧 `npx` 命令标注 deprecated。
4. README.en.md 与中文版逐节镜像。
