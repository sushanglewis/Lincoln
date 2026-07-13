# Lincoln 初始化安装执行指令

你是 Lincoln 的初始化助手。当前仓库可能尚未完成 Lincoln 环境配置，或者依赖清单已更新。请按以下步骤执行，并在每一步完成后向用户简要汇报。

## 1. 检查当前环境

运行：

```bash
python scripts/lincoln-setup.py check
```

- 列出所有缺失的 skills、CLI 工具、插件。
- 区分 required 与 optional/default_install。
- 如果检查通过且 `.context/lincoln-setup-state.yaml` 已标记完成，直接汇报“环境已就绪”，跳过剩余步骤。

## 2. 安装外部 skills

运行：

```bash
python scripts/lincoln-setup.py install-skills
```

- 默认会逐个询问用户确认。如果用户明确说“全部安装”，可追加 `--yes`。
- 该命令会：
  - 将 `superpowers`（上游 obra/superpowers，main 分支）clone 到 `~/.claude/skills/superpowers`
  - 将 `gsd`（上游 gsd-build/get-shit-done，main 分支）clone 到 `~/.claude/skills/gsd`
  - 安装 `oh-my-claudecode` 插件（如声明为 default_install）
- 如果目标目录已存在且 ref 匹配，自动跳过；如果 ref 不匹配或工作区 dirty，先向用户说明再决定。

## 3. 安装 CLI 工具

运行：

```bash
python scripts/lincoln-setup.py install-clis
```

- 默认逐个询问用户确认。
- 需要处理的 CLI 包括：
  - `openspec`：基于 Node.js，运行 `npm install -g @fission-ai/openspec`
  - `gh`：macOS 用 `brew install gh`，Linux 用包管理器
  - `ffmpeg`：macOS 用 `brew install ffmpeg`
  - Whisper 实现：优先 `faster-whisper`；如果失败，提供 `openai-whisper` 或 OpenAI API key 选项
- 安装失败后，给出对应平台的手动安装命令。

## 4. 配置仓库信息

运行：

```bash
python scripts/lincoln-setup.py init-repo-config --owner <owner> --name <repo>
```

- 从 git remote origin 自动推断 owner/name；如果推断失败，询问用户。
- 如果 `.github/openspec-config.yml` 已经包含真实值，命令会跳过并提示。

## 5. 运行项目初始化

运行：

```bash
bash scripts/init-project.sh
```

- 这会创建 products、oss、knowledge 等目录结构。
- 如果还有未满足的依赖，`init-project.sh` 会警告但不会强制退出。

## 6. 汇报状态

完成所有步骤后，向用户汇报：

- ✅ 已安装的 skills 与 CLI 工具
- ✅ `.github/openspec-config.yml` 中的仓库信息
- ⚠️ 仍缺失或需要手动处理的项目
- 📋 下一步：创建 issue 工作包或开始第一个 Lincoln 工作流

## 重要约束

- 不要假设用户已经允许安装全局工具；每次安装前必须获得确认（除非用户主动说 `--yes`）。
- 不要修改 `{process_slug}/recordings/` 中的任何文件。
- 不要创建 GitHub Issues 或 PR，除非人类明确请求。
- 如果某一步失败，暂停并报告失败原因与修复建议，不要继续后续步骤。
