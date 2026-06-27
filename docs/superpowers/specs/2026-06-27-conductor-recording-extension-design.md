# Conductor 内置录音扩展 PRD

## 1. Executive Summary

为 Conductor（macOS 多 agent 工作区应用）设计一个内置扩展，让产品经理在 Lincoln 需求调研工作流中，直接从当前工作区触发音频录制、落盘到标准目录，并在人工确认后自动推进到 `process-interview` 阶段。该扩展只负责“录音入口 + 文件落盘 + 触发转写”，不接管 Lincoln 后续 clarify、design、prototype 等阶段，从而消除当前手动放置录音文件、再手动运行命令的第一步断点。

## 2. Problem Statement

### Who has this problem?
使用 Lincoln 工作流进行需求调研的产品经理（PM）。

### What is the problem?
当前 Lincoln 流程要求 PM 在访谈后：
1. 手动把录音文件放到 `recordings/`
2. 运行 `claude process-interview <file>` 启动转写与摘要
3. 再进入后续 clarify → design → prototype → TDD → OpenSpec → GitHub 流程

第一步完全在 Conductor 外部完成，PM 在会议前/会议中没有统一入口准备和录制访谈。

### Why is it painful?
- **流程断点**：PM 需要在 Finder、终端、Conductor 之间切换，增加认知负担。
- **上下文丢失**：录音文件名、会议主题、设计 ID 等元数据容易在手动搬运中丢失或错配。
- **无法从 Conductor 发起**：Conductor 作为 PM 的日常工作台，缺少原生的访谈启动能力。
- **容易跳过 human_gate**：手动流程下，PM 可能在未确认的情况下直接触发转写，导致错误文件进入工作流。

### Evidence
- Lincoln README 当前步骤明确依赖 `cp ~/Downloads/xxx.m4a recordings/` 和手动命令。
- 2026-06-27 设计讨论中，PM 明确指出希望“由人类产品经理通过功能触发录制”，并坚持“人工确认后再触发 process-interview”。

## 3. Target Users & Personas

### Primary Persona: 产品经理 Lincoln 使用者
- **角色**：负责需求调研、用户访谈的产品经理
- **工作流**：在 Conductor 中维护多个 Lincoln feature branch，每个 branch 对应一个需求
- **目标**：在会议前后不离开 Conductor 即可完成录音与转写触发
- **痛点**：手动搬运录音文件、命名不规范、忘记触发 process-interview
- **技术熟练度**：中等，能使用 Conductor 和 Claude Code，但希望减少命令行操作

### Secondary Persona: 访谈参与者/协作者
- **角色**：临时参与需求访谈的设计师、工程师、业务方
- **需求**：能快速开始/停止录音，不需要理解 Lincoln 工作流细节
- ** differs**：不需要触后续流程，只关心录音是否成功保存

## 4. Strategic Context

### Business Goals
- 提升 Lincoln 工作流在 Conductor 中的闭环程度，减少 PM 在多个工具间切换。
- 强化 `human_gate` 原则，确保访谈内容经过 PM 确认后再进入 AI 处理阶段。
- 为后续 Conductor 扩展生态（如 Linear 扩展、屏幕录制）建立 MVP 范例。

### Why Now?
- Lincoln 模板已具备完整后端流程（process-interview → clarify → design → prototype → TDD → OpenSpec → GitHub）。
- 前端入口（录音触发）成为当前最明显的体验短板。
- Conductor 内置扩展形态已确定为优先方向，需要先产出设计文档以评估技术可行性。

## 5. Solution Overview

### High-Level Description
在 Conductor 应用内新增一个 **Lincoln 录音扩展**，为当前工作区提供录音能力：

1. **准备界面**：PM 输入/确认 session ID、design ID、会议主题。
2. **录音界面**：PM 点击开始录音，实时显示计时和音量提示；可随时暂停/继续/停止。
3. **结束后确认界面**：显示文件名、时长，支持回放、重命名、删除；PM 确认后调用 `claude process-interview <session-id>` 启动转写。

扩展**不直接修改** `.claude/workflow-state.yaml`，只生成标准 Lincoln artifact：
- `recordings/<session-id>.m4a`
- `interviews/<session-id>/metadata.json`

这些 artifact 由现有 `scripts/stage_loader.py` 和 Lincoln skill 接管。

### User Flow

```
PM 在 Conductor 中打开 Lincoln workspace
    ↓
点击扩展入口（如 toolbar 按钮 / 命令面板）
    ↓
【准备界面】输入 session ID、design ID、会议主题
    ↓
点击「开始录音」
    ↓
【录音界面】计时、音量提示、暂停/停止
    ↓
点击「停止录音」
    ↓
【确认界面】回放、重命名、删除、确认转写
    ↓
PM 点击「确认并转写」
    ↓
扩展调用 claude process-interview <session-id>
    ↓
现有 Lincoln 工作流接管（ingest → clarify → ...）
```

### Key Features
- **音频录制**：仅录制音频（MVP），使用 macOS AVAudioRecorder 或类似 API。
- **文件落盘**：保存到当前 Conductor 工作区的 `recordings/<session-id>.m4a`。
- **元数据写入**：同步生成 `interviews/<session-id>/metadata.json`（时间戳、主题、design ID、分支名、录音文件名）。
- **人工确认**：录音结束后必须经 PM 确认才触发 `process-interview`。
- **Lincoln 兼容**：复用 Lincoln 现有配置，本地 whisper 优先。

## 6. Success Metrics

### Primary Metric
**录音到转写的平均人工操作步数**
- **Current**：4 步（下载/复制文件 → 打开终端 → 运行命令 → 检查输出）
- **Target**：2 步（点击停止 → 点击确认并转写）
- **Timeline**：MVP 发布后 2 周内评估

### Secondary Metrics
- **录音文件命名规范率**：目标 100%（扩展强制使用 session-id 命名）
- **metadata.json 生成成功率**：目标 ≥ 99%
- **human_gate 跳过率**：目标 0%（扩展流程强制确认）
- **首次麦克风授权成功率**：目标 ≥ 95%

### Guardrail Metrics
- **process-interview 误触发率**：不因为 UI 误触导致错误录音被转写（通过确认界面兜底）。
- **录音文件丢失率**：目标 0%（原子写盘 + 校验）。

## 7. User Stories & Requirements

### Epic Hypothesis
我们相信，为 Conductor 增加 Lincoln 录音扩展，可以让产品经理在会议前后不离开 Conductor 完成录音与转写触发，从而减少手动操作步数、降低文件命名错误率，并确保访谈内容经人工确认后再进入 AI 处理阶段。

### User Stories

#### Story 1: 从 Conductor 启动录音准备
**As a** 产品经理  
**I want to** 在 Conductor 中打开一个 Lincoln workspace 后，能通过扩展入口打开录音准备界面  
**So that** 我可以为即将开始的需求访谈准备 session 信息

**Acceptance Criteria:**
- [ ] 扩展入口在当前 Lincoln workspace 中可见（toolbar 或命令面板）
- [ ] 准备界面自动读取当前分支名，建议 session-id（格式 `YYYY-MM-DD-descriptive-name`）
- [ ] PM 可输入/修改 session ID、design ID、会议主题
- [ ] 字段校验：session ID 必填且符合 Lincoln 命名规范

#### Story 2: 录制音频
**As a** 产品经理  
**I want to** 在准备界面点击开始后录制会议音频  
**So that** 访谈内容被完整保存到当前工作区

**Acceptance Criteria:**
- [ ] 点击「开始录音」后，扩展请求麦克风权限（首次使用）
- [ ] 录音界面显示已录制时长（MM:SS 格式）
- [ ] 录音界面显示实时音量提示（可选，用于确认麦克风工作）
- [ ] 支持暂停/继续录音
- [ ] 支持停止录音，停止后进入确认界面
- [ ] 录音文件以 `recordings/<session-id>.m4a` 保存

#### Story 3: 确认并触发转写
**As a** 产品经理  
**I want to** 录音结束后回放、重命名或删除录音，并在确认后触发 process-interview  
**So that** 只有正确的访谈内容才会进入 Lincoln 工作流

**Acceptance Criteria:**
- [ ] 确认界面显示录音文件名和时长
- [ ] 支持播放回放（可选 MVP 内）
- [ ] 支持重命名录音文件（同步更新 metadata.json）
- [ ] 支持删除录音并取消流程
- [ ] 点击「确认并转写」后，扩展调用 `claude process-interview <session-id>`
- [ ] 点击确认前不可触发 process-interview

#### Story 4: 生成标准 Lincoln artifact
**As a** Lincoln 工作流  
**I want to** 在录音完成后获得标准格式的录音文件和 metadata.json  
**So that** 后续 stage_loader.py 和 skill 可以无缝接管

**Acceptance Criteria:**
- [ ] 生成 `interviews/<session-id>/metadata.json`，字段包括：
  - `session_id`
  - `design_id`
  - `topic`
  - `branch`
  - `recording_file`
  - `started_at`
  - `ended_at`
  - `duration_seconds`
  - `source`: `"conductor-recording-extension"`
- [ ] metadata.json 写入后立即调用 `scripts/stage_loader.py --stage ingest --action validate-entry` 校验入口条件
- [ ] 扩展不直接修改 `.claude/workflow-state.yaml`

#### Story 5: 复用 Lincoln 转写配置
**As a** 产品经理  
**I want to** 扩展触发 process-interview 时复用 Lincoln 现有 whisper 配置  
**So that** 不需要为扩展单独配置转写服务

**Acceptance Criteria:**
- [ ] 扩展调用 `claude process-interview` 时，使用当前工作区已有的 `.claude/stages/process-interview/` 配置
- [ ] 优先使用本地 `faster-whisper`；若未安装或配置 API，则按 Lincoln 现有 fallback 逻辑处理
- [ ] 不引入新的转写服务依赖

## 8. Out of Scope

**MVP 不构建：**
- **屏幕录制** — 涉及更多权限、存储和合规问题，作为 V2。
- **摄像头录制** — 非需求访谈核心，延后评估。
- **云端缓存/同步** — MVP 保持本地存储，与 Lincoln 现有规范一致。
- **自动生成 Linear/GitHub Issue** — 由 Lincoln `split` 阶段统一处理。
- **实时转写** — 录音结束后再触发 process-interview，降低复杂度。
- **扩展直接修改 workflow state** — 只生成 artifact，state 由 stage_loader.py 接管。
- **跨 workspace 共享录音** — 录音文件归属当前 Lincoln feature branch。

## 9. Dependencies & Risks

### Dependencies
- **Conductor 扩展 API**：需要确认 Conductor 是否支持内置扩展/plugin API，以及可注入的 UI 入口点。
  - **可行性调研结论（2026-06-27）**：
    - Conductor.build 官方文档未提及 plugin/extension API。
    - 公开渠道未发现 Conductor.build macOS 应用的第三方 workspace 扩展机制。
    - GitHub 上 `useconductor/conductor` 仓库虽存在 plugin 接口，但它是独立的 MCP tool-hub 产品（npm 包 `@useconductor/conductor`），与 Conductor.build macOS 应用不是同一产品，不能复用。
    - **结论**：若无 Conductor 团队提供的私有/内部 API，当前无法在 Conductor.build macOS 应用内实现原生内置扩展。
- **macOS 麦克风权限**：扩展需要请求 `NSMicrophoneUsageDescription` 权限。
- **Lincoln 现有配置**：依赖 `scripts/init-project.sh` 已初始化 `recordings/`、`interviews/` 目录和 whisper 配置。
- **Claude Code CLI**：扩展需要能调用 `claude process-interview <session-id>`。

### Risks & Mitigations
- **Risk：Conductor 尚无公开扩展 API**
  - **Mitigation**：
    1. 优先联系 Conductor 团队确认是否存在私有/beta extension API。
    2. 若不可行，回退到以下替代方案（详见第 14 节）：
       - 独立 macOS 菜单栏录音小工具
       - 基于现有 `claude` CLI 命令的 wrapper
       - 通过 Conductor `scripts.run` 启动的本地录音服务
- **Risk：首次使用麦克风授权体验差**
  - **Mitigation**：在准备界面提前说明需要麦克风权限，并提供系统设置跳转按钮。
- **Risk：长时间录音文件过大**
  - **Mitigation**：采用 m4a（AAC）编码，1 小时约 30-50 MB；存储在本地 gitignored 目录。
- **Risk：PM 在录音中途关闭 Conductor 导致文件损坏**
  - **Mitigation**：周期性写入临时文件，停止时做最终封装；崩溃恢复时提示用户检查临时文件。
- **Risk：确认界面被跳过**
  - **Mitigation**：流程强制，停止录音后必须先进入确认界面，确认按钮为唯一的 process-interview 触发入口。

## 10. Open Questions

1. ~~Conductor 是否已有扩展/plugin API？接入点是什么？~~
   - **部分结论**：公开文档与渠道未找到 Conductor.build macOS 应用的扩展 API；`useconductor/conductor` 是另一款 MCP tool-hub 产品，不可复用。
   - **待确认**：是否联系 Conductor 团队询问私有/内部 API；若不可行，选择第 14 节中的 fallback 方案。
2. 录音扩展的 UI 应作为独立窗口、侧边面板还是命令面板命令？
3. 是否需要在录音开始时显示“正在录音”的视觉提示（如状态栏图标），以防误触？
4. 重命名录音文件时，是否需要同步更新 workflow-state.yaml 中的变量？（PRD 决定：不直接修改 state，仅更新 metadata.json）
5. 如果 PM 在录音过程中切换 workspace，录音应继续还是暂停？（建议：随 Conductor 行为而定，至少保证文件不丢）

## 11. Data Model

### `interviews/<session-id>/metadata.json`

```json
{
  "session_id": "2026-06-27-stakeholder-checkout",
  "design_id": "checkout-redesign",
  "topic": "结算流程 redesign 需求访谈",
  "branch": "lincoln/2026-06-27-stakeholder-checkout-checkout-redesign",
  "recording_file": "recordings/2026-06-27-stakeholder-checkout.m4a",
  "started_at": "2026-06-27T10:00:00Z",
  "ended_at": "2026-06-27T10:45:00Z",
  "duration_seconds": 2700,
  "source": "conductor-recording-extension",
  "created_by": "conductor-recording-extension"
}
```

### Conductor 配置项（建议）

在 `.conductor/settings.toml` 中可选配置：

```toml
[lincoln.recording]
enabled = true
recordings_dir = "recordings"
interviews_dir = "interviews"
format = "m4a"
# 是否启用音量可视化
volume_indicator = true
# 录音中断时保留临时文件的最大时长（秒）
max_temp_file_age = 86400
```

## 12. 与 Lincoln Workflow 的集成边界

```
┌─────────────────────────────────────────────────────────────┐
│                    Conductor 应用                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           Lincoln 录音扩展                             │  │
│  │  准备界面 → 录音界面 → 确认界面 → 触发 process-interview │  │
│  └───────────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────────┘
                        │ 生成 artifact
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              当前 Lincoln workspace（工作树）                │
│  recordings/<session-id>.m4a                                 │
│  interviews/<session-id>/metadata.json                       │
└───────────────────────┬─────────────────────────────────────┘
                        │ stage_loader.py 校验
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Lincoln skill / workflow                        │
│  process-interview → clarify → design → prototype → TDD ...  │
└─────────────────────────────────────────────────────────────┘
```

**边界原则：**
- 扩展只负责录音入口、文件落盘、触发 process-interview。
- 扩展不读写 `.claude/workflow-state.yaml`。
- 扩展不接管 clarify 及后续阶段。
- 所有 stage entry/exit 校验继续通过 `scripts/stage_loader.py` 执行。

## 13. 附录：界面文案草案

### 准备界面
- 标题：开始 Lincoln 访谈录音
- Session ID：输入框（自动建议）
- Design ID：输入框
- 会议主题：输入框
- 按钮：开始录音

### 录音界面
- 标题：正在录音
- 计时：00:00
- 音量提示：[可视化条]
- 按钮：暂停 / 停止

### 确认界面
- 标题：确认录音
- 文件：`recordings/<session-id>.m4a`
- 时长：45:00
- 按钮：播放 / 重命名 / 删除 / 确认并转写

## 14. 技术可行性 fallback 方案

若 Conductor.build macOS 应用**无原生扩展 API**，可考虑以下替代架构，按推荐优先级排列：

### 方案 A：独立 macOS 菜单栏录音小工具（推荐 fallback）
- 独立 Swift/SwiftUI 应用，常驻菜单栏。
- PM 点击菜单栏图标开始录音，选择当前 Conductor workspace（或自动检测前台 workspace）。
- 录音保存到对应 workspace 的 `recordings/<session-id>.m4a`。
- 结束后弹出确认窗口，点击确认后调用 `claude process-interview <session-id>`。
- **优点**：不依赖 Conductor 内部 API，开发可控。
- **缺点**：PM 需要在两个应用间切换；无法嵌入 Conductor UI。

### 方案 B：基于 `claude` CLI 命令的 wrapper
- 在 Conductor workspace 内提供一个本地命令，例如 `claude record-interview <session-id>`。
- 该命令启动一个 TUI（如使用 `ink` 或 `blessed`）或外部录音进程。
- 录音完成后，在同一终端内提示确认，确认后调用 `claude process-interview <session-id>`。
- **优点**：完全在 Conductor 工作流内，无需 macOS app 开发。
- **缺点**：TUI 体验不如原生 UI；需要 PM 熟悉命令行。

### 方案 C：通过 Conductor `scripts.run` 启动本地录音服务
- 在 `.conductor/settings.toml` 中配置一个 `run` 脚本，启动一个本地 HTTP/WebSocket 录音服务。
- PM 在浏览器或独立小窗口中访问该服务进行录音。
- 服务将录音文件写入 `recordings/`，并提供「确认并转写」按钮调用 `claude process-interview`。
- **优点**：利用 Conductor 已有脚本机制；跨 workspace 可复用。
- **缺点**：需要常驻一个服务进程；首次配置较复杂。

### 方案 D：MCP server 形态
- 将录音能力封装为 MCP server，作为外部工具供 Conductor 中的 Claude Code 调用。
- **问题**：MCP server 通常无法请求 macOS 麦克风权限或操作本地 UI，不适合作为录音入口。
- **结论**：不推荐。

### 下一步
- 首选：联系 Conductor 团队确认是否有私有/内部 extension API。
- 若一周内无明确答复，建议启动方案 A 的 PoC（独立菜单栏录音小工具），因为它与 Conductor 解耦，交付风险最低。
