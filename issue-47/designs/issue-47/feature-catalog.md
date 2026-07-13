# 功能目录: issue-47

## 功能清单

| 功能编号 | 功能名称 | 优先级 | 验收标准 |
|----------|----------|--------|----------|
| F-001 | 适配生成器核心 | 高 | manifest 驱动的生成器(`scripts/lincoln_harness_adapter.py`),读 `.claude/` 输出各 harness 产物;幂等;失败原子回滚 |
| F-002 | codex 适配 | 高 | 生成 `AGENTS.md` + `~/.codex/prompts/lc-*.md`;`lc-status` 端到端可运行 |
| F-003 | opencode 适配 | 高 | 生成 `.opencode/agent/*.md` + `.opencode/command/lc-*.md`;frontmatter 符合 spike 确认的 schema |
| F-004 | `lc-*` 命令映射与重命名 | 高 | 命令映射表落地;Claude Code 侧旧命令移除;安装时检测旧名并提示迁移 |
| F-005 | 安装链路集成 | 高 | `lincoln-setup.py bootstrap --harness <name>` 串联依赖安装 + 适配生成;README 提示词同步 |
| F-006 | 轻量门控统一 | 中 | 三 harness 的门控统一经 `stage_loader.py`;弱 harness 命令提示词含门控执行约束 |
| F-007 | CI 漂移校验(轻量) | 中 | 一个脚本/测试:重新生成全部产物并要求零 diff;接入 static-check |
| F-008 | 文档与迁移说明 | 中 | README/CLAUDE.md 多 harness 安装说明 + `lc-*` 迁移指引 |

## 非功能需求

- 性能: 生成器全量输出 < 5s(本地文件读写为主)。
- 安全: 生成器只写白名单目录(项目 `AGENTS.md`、`.opencode/`、`~/.codex/prompts/`);不执行产物中的任何内容。
- 兼容性: macOS/Linux;Python ≥ 3.10;不新增第三方依赖(沿用 PyYAML)。

## 验收映射

- [ ] F-001 → design-review 验收标准"生成器幂等;CI 漂移校验通过"
- [ ] F-002 → "codex 安装后 AGENTS.md 生成;lc-status 可调用"
- [ ] F-003 → "opencode 安装后 agent/command 生成;命令可调用"
- [ ] F-004 → "Claude Code lc-* 生效,旧命令移除,263 测试零回归"
- [ ] F-005 → "bootstrap --harness 端到端安装成功"
- [ ] F-006 → "门控在 codex/opencode 上以 stage_loader.py 可执行"
- [ ] F-007 → "漂移校验接入 CI 且通过"
- [ ] F-008 → "README/CLAUDE.md 多 harness 说明完成"
