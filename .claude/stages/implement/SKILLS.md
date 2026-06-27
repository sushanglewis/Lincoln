# implement 阶段技能与工具

## 主技能命令

本阶段无专门的 Agent 主动技能命令，由人类主导执行。

Agent 辅助时可使用的技能：

```
# 代码审查（人类请求时）
claude /code-review

# 安全审查（人类请求时）
claude /security-review
```

## GitHub MCP 使用

人类完成 PR 合并后，Agent 可使用 GitHub MCP 获取信息：

- **获取 PR 详情**：`mcp__plugin_ecc_github__get_pull_request`
  - 参数：`owner`, `repo`, `pull_number`
- **获取 PR 文件变更**：`mcp__plugin_ecc_github__get_pull_request_files`
  - 用于代码审查辅助
- **获取 PR 评论**：`mcp__plugin_ecc_github__get_pull_request_comments`
  - 用于审查意见汇总
- **更新 Issue**：`mcp__plugin_ecc_github__update_issue`
  - 参数：`owner`, `repo`, `issue_number`, `state`
  - 人类请求时协助更新 Issue 状态

## Validator 使用

入口校验：
```bash
python .claude/skills/interview-workflow/validators/validate.py \
  --phase entry \
  --check issues_ready \
  --args <session_id>
```

## 错误处理

| 错误场景 | 处理方式 |
|---------|---------|
| Issues 未就绪 | 暂停，提示人类先完成 `split` 阶段 |
| PR 审查发现问题 | Agent 提供建议，人类决定是否修改 |
| 合并冲突 | Agent 协助分析冲突，人类手动解决 |
| 测试失败 | Agent 协助分析失败原因，人类修复代码 |
| sync-queue 文件创建失败 | 提示人类手动创建，或重试 |

## 输入文件

- `.github/linked-issues.yaml` — Issue 映射关系
- GitHub Issues — 研发任务
- `requirements/<session_id>/requirements.md` — 需求文档（参考）
- `openspec/changes/<change_name>/` — OpenSpec 设计文档（参考）

## 输出文件

- 合并的 PR（由人类创建）
- `.github/lincoln-sync-queue/pr-{pr_number}.yaml` — 触发 sync-knowledge 的队列文件
