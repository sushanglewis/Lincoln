---
name: lc-setup
description: |
  Lincoln 环境初始化 skill。用于在仓库首次打开或依赖发生变化时，
  检查、安装并配置 Lincoln 所需的外部 skills、CLI 工具、插件以及仓库配置。
---

# lc-setup

## Purpose

Using [lc-setup] to .


## 触发条件

- 用户首次用 Claude Code 打开从 Lincoln template 创建的新仓库。
- `.claude/hooks/on-session-start.sh` 检测到 Lincoln setup 尚未完成。
- 用户复制 README 中的初始化提示词并发送给 Claude。
- 运行 `python scripts/lincoln-setup.py check` 发现缺失依赖。

## 职责

1. 检查 `.claude/skills/dependencies.yaml` 声明的依赖是否满足。
2. 安装缺失的外部 skills（`superpowers`、`gsd`）到 `~/.claude/skills/`，并确保 ref 正确。
3. 安装缺失的 CLI 工具（`openspec`、`gh`、`ffmpeg`、Whisper 实现）。
4. 安装 `oh-my-claudecode` 插件（可选但默认安装）。
5. 配置 `.github/openspec-config.yml` 的 `repository.owner` 和 `repository.name`。
6. 运行 `scripts/init-project.sh` 完成项目级初始化。
7. 安装任何全局工具或写入配置前，必须先向用户确认。

## 调用方式

优先使用 Skill 工具调用 `lc-setup`；如果环境不支持，可运行等效命令：

```bash
python scripts/lincoln-setup.py bootstrap
```

常用子命令：

```bash
python scripts/lincoln-setup.py check              # 仅检查
python scripts/lincoln-setup.py install-skills     # 安装外部 skills
python scripts/lincoln-setup.py install-clis       # 安装 CLI 工具
python scripts/lincoln-setup.py init-repo-config --owner <owner> --name <repo>
python scripts/lincoln-setup.py bootstrap          # 完整流程
```

## 产物

- `~/.claude/skills/` 下的外部 skill 目录。
- 安装到 PATH 的 CLI 工具。
- 更新后的 `.github/openspec-config.yml`。
- 写入 `.context/lc-setup-state.yaml` 的 setup 完成状态。
- 初始化后的项目目录结构（products、oss、knowledge 等）。

## 约束

- 不得跳过用户确认擅自安装全局工具。
- 遇到不支持的平台或安装失败时，给出清晰的手动替代命令。
- 安装完成后汇报状态：依赖是否就绪、配置是否写入、下一步动作。
- 如果 `.context/lc-setup-state.yaml` 已标记完成且依赖检查通过，可跳过重复安装。

## Prompts

- `prompts/main.md` — 给 Claude 的详细安装执行指令。
