# Lincoln #14 录音功能优化 — 需求规格说明书

## 1. 背景与问题

Lincoln 的访谈录音工具目前是一个极简的 Python CLI：用户运行 `record-interview <session-id>`，按 Enter 开始/停止录音，录制结束后调用 `claude process-interview` 进行批量转写和总结。该流程存在以下问题：

1. **无 GUI 引导**：终端仅打印简单提示，用户无法直观确认麦克风、ffmpeg、Whisper 等依赖是否就绪；出错时只有 stderr 信息，缺乏修复指引。
2. **无实时反馈**：录制过程中看不到转写内容，也无法确认录音是否正常工作。
3. **无阶段总结**：只能得到一份最终总结，无法按会议阶段逐步沉淀内容。
4. **无发言人区分**：仅使用交替 Speaker A/B 标签，无法真实区分说话人。
5. **未感知 git worktree**：产物保存位置依赖当前工作目录，未与当前 git worktree 强绑定。

## 2. 目标

将 `tools/record-interview` 升级为基于终端 UI（TUI）的录音工具，实现：

- 录制前环境检查与明确的报错/修复指引。
- 录制过程中实时显示转写文本和说话人标签。
- 每 10 分钟自动生成一份阶段总结文档，使用标准命名规则落到当前 git worktree。
- 录制结束后，基于所有阶段总结文档生成最终会议纪要（`summary.md`）。
- 支持 MacBook 内置麦克风单声道录音场景下的发言人区分。

## 3. 用户角色

- **PM（主要用户）**：使用 MacBook 录制需求访谈/会议，需要低门槛、可视化、可追踪的录音与总结流程。
- **开发团队**：基于阶段总结和最终会议纪要推进后续实现。

## 4. 功能需求

### 4.1 TUI 入口与基础体验

| ID | 需求 | 优先级 | 验收标准 |
|---|---|---|---|
| F1 | 检测到 TTY 时启动 TUI；非 TTY 或 `--no-tui` 时保留原有 CLI 行为 | 必须 | `record-interview` 在 iTerm/Terminal 中进入 TUI；管道/脚本模式保持原逻辑 |
| F2 | 展示 Session ID、设计 ID、Topic 等基本信息 | 必须 | Setup 屏幕顶部显示当前 session 信息 |
| F3 | 支持 `q` 取消、`Enter` 开始/停止录制 | 必须 | 快捷键在屏幕底部常驻提示 |

### 4.2 录制前环境检查（Setup 屏幕）

| ID | 需求 | 优先级 | 验收标准 |
|---|---|---|---|
| F4 | 检查 ffmpeg 是否安装并在 PATH 中 | 必须 | 未安装时显示 `brew install ffmpeg` 或官方安装指引 |
| F5 | 检查麦克风权限/可用性 | 必须 | 无麦克风时显示权限修复步骤 |
| F6 | 检查 `faster-whisper` 是否可导入 | 必须 | 未安装时显示 `pip install faster-whisper` 及模型下载说明 |
| F7 | 检查 `pyannote.audio` 或备选 diarizer 是否可导入 | 必须 | 未安装时显示安装命令；支持切换 `diarize` 或启发式降级 |
| F8 | 检查总结提供者配置（`claude` CLI 或 OpenAI/Anthropic API Key） | 必须 | 无可用总结服务时显示配置 `~/.lincolnrc` 或环境变量指引 |
| F9 | 所有关键检查项通过后才允许开始录制 | 必须 | “开始录制”按钮在未通过前禁用 |

### 4.3 录制中实时反馈（Recording 屏幕）

| ID | 需求 | 优先级 | 验收标准 |
|---|---|---|---|
| F10 | 显示录制计时器 | 必须 | 格式 `MM:SS / 10:00`，且每 10 分钟重置阶段倒计时 |
| F11 | 显示音频电平指示器 | 必须 | 根据麦克风输入动态变化 |
| F12 | 显示“正在录音”状态（红色指示灯 / REC 标识） | 必须 | 视觉反馈明显 |
| F13 | **实时显示转写文本** | 必须 | 每处理完一个 chunk，最新转写文本追加到 transcript 区域 |
| F14 | 实时显示说话人标签（Speaker A/B/...） | 必须 | 每个 transcript segment 前带说话人标识 |
| F15 | 支持手动切换/标记说话人 | 应该 | 快捷键 `1`/`2`/`Space` 可修正当前说话人 |
| F16 | 显示距离下次阶段总结的倒计时 | 应该 | 例如“距阶段总结 03:42” |

### 4.4 阶段总结文档

| ID | 需求 | 优先级 | 验收标准 |
|---|---|---|---|
| F17 | 每 10 分钟（可配置）自动生成阶段总结 | 必须 | 文件名为 `phase-summary-{n}.md`，n 从 1 开始，左补零 |
| F18 | 阶段总结保存到当前 git worktree 的 `interviews/{session_id}/` | 必须 | 路径可通过 `git rev-parse --show-toplevel` 验证 |
| F19 | 阶段总结内容包含该 10 分钟的关键主题、决策、行动项、开放问题 | 必须 | 结构同最终总结 |
| F20 | 阶段总结需关联仓库知识并引用来源 | 应该 | 若 `docs/knowledge/` 有相关文档，总结中标注来源 |
| F21 | 阶段总结使用与最终总结相同的 LLM 提供者 | 必须 | 配置来自 `~/.lincolnrc` 或环境变量 |

### 4.5 最终会议纪要

| ID | 需求 | 优先级 | 验收标准 |
|---|---|---|---|
| F22 | 停止录制后，读取 `interviews/{session_id}/phase-summary-*.md` | 必须 | 仅读取该 session 目录下的阶段总结文件 |
| F23 | 基于所有阶段总结生成 `summary.md` | 必须 | 文件保存到 `interviews/{session_id}/summary.md` |
| F24 | `summary.md` 结构包含：关键主题、决策、行动项、开放问题 | 必须 | 符合现有 `summary.md` 校验规则 |
| F25 | `summary.md` 作为 Lincoln 下一阶段（clarify）的输入 | 必须 | `clarify` 阶段入口 `summary_ready` 校验通过 |

### 4.6 错误处理与恢复

| ID | 需求 | 优先级 | 验收标准 |
|---|---|---|---|
| F26 | 所有用户-facing 错误必须带修复指引 | 必须 | 使用 `GuidanceError` 体系，TUI 弹窗/区域显示 `remediation` |
| F27 | 转写服务不可用时给出明确降级路径 | 必须 | 提示安装 faster-whisper 或配置 OPENAI_API_KEY |
| F28 | 录制中断时保留已生成产物 | 必须 | 已保存的 audio chunk、metadata、transcript segment 不丢失 |
| F29 | 允许 `--no-confirm` 跳过 Summary 屏幕直接生成总结 | 应该 | 非交互式 CI/脚本场景可用 |

### 4.7 git worktree 感知

| ID | 需求 | 优先级 | 验收标准 |
|---|---|---|---|
| F30 | 自动检测当前目录所在 git worktree 根目录 | 必须 | 使用 `git rev-parse --show-toplevel` |
| F31 | 非 git 环境回退到现有目录标记探测 | 必须 | 存在 `recordings/`、`interviews/`、`.claude/` 时继续工作 |
| F32 | 所有产物写入 worktree 根目录下 | 必须 | 录制文件、阶段总结、最终总结均在该根目录 |

## 5. 非功能需求

| ID | 需求 | 优先级 | 验收标准 |
|---|---|---|---|
| NF1 | 测试覆盖率 ≥ 80% | 必须 | `pytest --cov` 通过 |
| NF2 | 单文件 ≤ 800 行，函数 ≤ 50 行 | 必须 | 代码审查 checklist |
| NF3 | 支持 macOS（Apple Silicon / Intel） | 必须 | 在目标环境手动验证 |
| NF4 | 不依赖 Node.js，纯 Python TUI | 必须 | 依赖仅 `textual` 等 Python 包 |
| NF5 | 可配置阶段总结间隔（默认 600 秒） | 应该 | 通过 `LINCOLN_PHASE_INTERVAL_SECONDS` 调整 |
| NF6 | 可配置 chunk 大小（默认 5 秒） | 应该 | 通过 `LINCOLN_CHUNK_SECONDS` 调整 |

## 6. 数据与命名规范

### 6.1 Session ID

- 格式：`YYYY-MM-DD-descriptive-name`
- 小写、连字符分隔。

### 6.2 目录结构

```
{worktree_root}/
  recordings/{session_id}.m4a
  interviews/{session_id}/
    metadata.json
    transcript.md
    raw-insights.md
    phase-summary-01.md
    phase-summary-02.md
    ...
    summary.md
```

### 6.3 阶段总结文件名

- `phase-summary-{n}.md`
- `n` 从 1 开始，左补零至两位（`01`、`02`...）。

### 6.4 metadata.json 扩展字段

- `phased_summaries`: 数组，元素包含 `index`、`file`、`start_time`、`end_time`。
- `transcription_model`: 使用的转写模型。
- `diarization_model`: 使用的 diarization 模型。
- `summarization_model`: 使用的总结模型。

## 7. 界面原型（基于 TDD 细化）

界面原型见 `designs/lincoln-recording-v2/untitled.pen` 与配套说明，包含：

1. **Setup 屏幕**：环境检查列表 + 修复指引 + 开始按钮。
2. **Recording 屏幕**：计时器、音频电平、实时 transcript、阶段总结倒计时、停止按钮。
3. **Summary 屏幕**：录音信息、阶段总结列表、重录/生成总结按钮。

## 8. 依赖与配置

- Python 包：`textual`、`pydantic`、`pyyaml`。
- 可选：`faster-whisper`、`pyannote.audio`、`diarize`、`openai`、`anthropic`。
- 外部 CLI：`ffmpeg`、`git`、`claude`（可选）。
- 配置文件：`~/.lincolnrc`（YAML）。

## 9. 验收清单

- [ ] Setup 屏幕在未安装 ffmpeg 时给出可操作的修复指引。
- [ ] Recording 屏幕在 10 分钟内至少更新 3 条实时转写 segment。
- [ ] 录制 11 分钟后，`interviews/{session_id}/` 下存在 `phase-summary-01.md` 与 `phase-summary-02.md`。
- [ ] `summary.md` 基于上述阶段总结生成，且被 `clarify` 阶段入口校验通过。
- [ ] 所有测试覆盖率 ≥ 80%。
