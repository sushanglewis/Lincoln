# 功能目录: issue-59

<!-- status: approved -->

## 功能清单

| 功能编号 | 功能名称 | 优先级 | 验收标准 |
|----------|----------|--------|----------|
| F-001 | 开场引导 hook 注入 | 高 | fresh repo / not_started 输出引导块;活跃阶段不输出;pytest 守卫 |
| F-002 | intake-prompt 摸排与判断 | 高 | 信号清单 + ≤8 次只读上限 + 禁深度扫描;五要素判断模型 |
| F-003 | Johari 认知象限确认 | 高 | 四象限策略映射;每轮 ≤3 问;收敛标准明文 |
| F-004 | 契约与 clarify 同步 | 中 | default.md/CLAUDE.md/clarify/lc-workflow/stage yaml 含开场引导与象限表述 |
| F-005 | README 双语言自然语言化 | 高 | 用户面向章节零命令调用(块与内联);双文件结构镜像;pytest 守卫 |
| F-006 | 测试与漂移守卫 | 高 | 269 基线全绿 + 新增约 13 例;harness 重新生成无漂移 |

## 非功能需求

- 性能:摸排为概览级,操作数硬上限,不引入深度扫描。
- 安全:摸排全程只读;唯一可写文件为 `.context/lc-intake.md`(gitignored)。
- 兼容性:stage 注册表/schema/command-map 不变;codex/opencode 由派生重新生成。

## 验收映射

- [ ] F-001 对应 requirements.md 验收标准 2
- [ ] F-002 对应验收标准 3
- [ ] F-003 对应验收标准 4、5
- [ ] F-004 对应验收标准 5、6
- [ ] F-005 对应验收标准 1
- [ ] F-006 对应验收标准 7
