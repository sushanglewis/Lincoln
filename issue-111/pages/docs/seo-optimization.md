# Lincoln GitHub SEO 优化方案

## 当前问题诊断

| 项目 | 当前状态 | 问题 |
|---|---|---|
| 仓库描述 | `A repository for product-manager` | 过于模糊，不含任何核心关键词，不利于 GitHub 内部搜索和搜索引擎抓取 |
| Topics | 无 | 缺失分类标签，降低被 GitHub 推荐和相关项目引流的机会 |
| Homepage URL | 空 | 缺少对外文档/落地页入口，削弱外链和品牌集中性 |
| README H1 | `Lincoln — AI-Native 研发工作流与产研协作体系` | 中文为主，GitHub 搜索以英文为主，需要英文 README 作为默认入口 |
| README 前段 | 已包含 AI-Native、Agent Harness、SOP、人机协作 | 关键词较全，但可进一步结构化 |
| 多语言 | 有 README.en.md | 需确保 GitHub 默认展示英文版以提升国际搜索可见性 |

## 关键词策略

### 核心关键词（高优先级）

- AI-Native R&D workflow
- agent harness
- Claude Code workflow
- product-engineering collaboration
- repeatable SOP
- AI-native development workflow

### 长尾/场景关键词

- agentic workflow framework
- AI product management workflow
- Claude Code project template
- AI team collaboration tool
- knowledge distillation for AI teams
- OpenSpec workflow

### 竞品/生态关键词

- Claude Code, Codex, OpenCode
- OpenSpec
- Obsidian knowledge base
- GitHub Issues workflow

## 仓库元数据优化

### 1. 仓库描述（Repository description）

建议文案（160 字符以内，英文优先）：

```
Lincoln — AI-Native R&D workflow system for product-engineering collaboration, agent harnesses, and repeatable SOPs.
```

备选（强调 Claude Code 生态）：

```
Lincoln — AI-Native workflow system for Claude Code/Codex/OpenCode. Stage-driven, human-gated, SOP-based product-engineering collaboration.
```

### 2. Topics（建议 8–10 个）

```
ai-native, agent-harness, claude-code, agentic-ai, workflow-engine, product-engineering, repeatable-sop, codex, opencode, openspec, knowledge-management
```

### 3. Homepage URL

建议指向英文 README 或未来独立文档站点：

```
https://github.com/sushanglewis/Lincoln/blob/main/README.en.md
```

未来可替换为 GitHub Pages 或独立官网。

### 4. Social Preview / Open Graph

建议上传 1280×640 的 social preview 图片，包含：
- 品牌名 Lincoln
- 一句话价值主张
- 视觉风格与项目定位一致

## README SEO 优化建议

### 已做的优化

- README.en.md 存在且结构完整
- 版本记录已集中到文档底部
- 核心能力以最终形态描述，不堆砌版本号
- SKILL.md 已更新为全局插件安装路径

### 建议进一步调整

1. **将 README.en.md 设为默认 README**
   - GitHub 默认展示仓库根目录 `README.md`。
   - 当前 `README.md` 是中文版，对国际搜索不利。
   - **方案 A**：将英文版重命名为 `README.md`，中文版改为 `README.zh.md`。
   - **方案 B**：在 `README.md` 顶部添加显眼的英文入口，并保证前 160 字符为英文核心描述。

2. **优化 README 开头摘要**
   - 当前英文 README 第一段较长。
   - 建议在第一段后增加一句 120–160 字符的 "TL;DR" 或独立价值主张句，便于 GitHub/搜索引擎抓取：

   ```markdown
   Lincoln is an AI-Native R&D workflow system that brings stage-driven discipline, human gates, and repeatable SOPs to Claude Code, Codex, and OpenCode — from requirements to shipped knowledge.
   ```

3. **增强 H2/H3 关键词覆盖**
   - 在 `## What Lincoln Can Do` 下确保每个 H3 都包含一个核心概念：
     - `Stage-Driven Workflow Engine`
     - `Artifact Traceability (lc-one-id)`
     - `Preset SOP Workflow Templates`
     - `Markdown-First Issue Work Packages`
   - 当前已较好，可将 `Issue Work Packages (HTML Portal)` 改为 `Markdown-First Issue Work Packages`。

4. **添加 "Why Lincoln" / "Who is it for" 小节**
   - 增加场景化关键词，如：
     - "For AI-native product teams"
     - "For vibe-coding indie makers"
     - "For teams using Claude Code at scale"

5. **增加安装/使用关键词密度**
   - 在 README 中自然出现：
     - `Claude Code workflow`
     - `agent harness plugin`
     - `npm install -g @sushanglewis/lincoln`

## 内容/链接策略

### 内部链接

- README 中链接到 USAGE.md、CONTRIBUTING.md、CLAUDE.md、RELEASE.md（已做）。
- 确保 issue-111 等工作包门户不被搜索引擎索引（过程文档留分支，不影响主站 SEO）。

### 外部链接/Backlinks

- 在以下位置提及 Lincoln 并链接回仓库：
  - 个人/团队技术博客
  - Claude Code / Codex / OpenCode 社区讨论
  - X/Twitter、LinkedIn 项目发布帖
  - 中文技术社区（知乎、掘金、V2EX）
  - Awesome Claude Code / Awesome Agent Harness 等列表

### Release Notes SEO

- RELEASE.md 中每个版本标题使用 `## Lincoln v1.6.3 — Markdown-first docs and batch rendering` 形式，包含关键词。
- 在 Release 页面添加简短 summary，便于 GitHub 索引。

## 执行清单

### 需要仓库管理员手动执行（Agent 无权限或需显式授权）

- [ ] 更新仓库描述
- [ ] 添加 Topics
- [ ] 设置 Homepage URL
- [ ] 上传 Social Preview 图片

### 可通过 PR 执行的代码/文档改动

- [ ] 决定 README 默认语言策略（A：英文为默认；B：保留中文默认但优化顶部摘要）
- [ ] 在 README 顶部增加英文 TL;DR 价值主张句
- [ ] 微调 H3 标题增强关键词
- [ ] 考虑添加 `.github/ISSUE_TEMPLATE` 和 `.github/PULL_REQUEST_TEMPLATE`（提升项目专业度和参与度）
- [ ] 添加 `CITATION.cff`（如果被学术界引用，增加权威性）

## 预期效果

- 仓库在 GitHub 搜索 `AI-Native workflow`、`Claude Code workflow`、`agent harness` 等词时排名提升。
- Topics 带来相关项目推荐流量。
- 英文 README 作为默认入口，提升国际用户发现和 star 转化率。
- 清晰的描述和 social preview 提升点击率和品牌认知。
