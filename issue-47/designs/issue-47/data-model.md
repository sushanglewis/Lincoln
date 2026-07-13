# 数据模型: issue-47

## 实体

### HarnessManifest(新增,`.claude/harnesses/<name>.yaml`)

每个目标 harness 一份清单,声明能力、产物目标与生成规则。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| name | string | 必填 | harness 标识:`claude-code` / `codex` / `opencode` |
| capabilities | map | 必填 | 能力矩阵:`hooks` / `skills` / `agents` / `commands` / `state_injection`(bool) |
| targets | list | 必填 | 产物目标列表,见 Target |
| command_map | map | 必填 | `lc-*` 命令 → 执行动作(脚本或 prompt 引用) |
| degradation | map | 可选 | 能力缺失时的降级策略说明(注入到生成内容) |

### Target(HarnessManifest.targets[])

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| kind | enum | 必填 | `agents_md` / `prompt` / `agent` / `command` / `plugin` / `skill` |
| source | string | 必填 | `.claude/` 内来源路径(glob 或文件) |
| output | string | 必填 | 输出路径模板(支持 `{home}`、`{project}`、`{name}` 占位) |
| scope | enum | 必填 | `project` / `user`(如 `~/.codex/prompts/` 为 user) |
| transform | enum | 必填 | 转换器:`frontmatter` / `concat` / `copy` / `command-template` |

### CommandMap 条目

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| name | string | `lc-` 前缀 | 命令名,如 `lc-status` |
| description | string | 必填 | 一句话说明(写入各 harness 命令 frontmatter) |
| action | string | 必填 | 执行体,如 `python3 scripts/lincoln-status.py` |
| args_hint | string | 可选 | 参数提示(如 `[--format table]`) |

### GeneratedArtifact(产物头注释,非独立文件)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| generated_by | string | 固定 | `scripts/lincoln_harness_adapter.py` |
| source | string | 必填 | 来源 `.claude/` 路径 |
| harness | string | 必填 | 目标 harness 名 |
| note | string | 固定 | "自动生成,请勿手改" |

## 关系

- HarnessManifest 与 Target:一对多。
- HarnessManifest 与 CommandMap 条目:一对多;三个 harness 的 CommandMap 键集必须一致(CI 校验)。
- Target 与 GeneratedArtifact:一对多(一个 target glob 可展开多个产物)。

## 约束

- 产物文件一律不提交 git(`.gitignore` 增加 `.opencode/`、根 `AGENTS.md` 若生成);CI 以"重新生成零 diff"验证一致性。
- `command_map` 键名必须全部以 `lc-` 开头(生成器校验)。
- 既有状态协议不变:`{process_slug}/workflow-stage.yaml` schema 2.0 不新增字段。
