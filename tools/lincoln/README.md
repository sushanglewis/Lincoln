# Lincoln TUI

Lincoln TUI 是 Lincoln 工作流的终端录音入口。它提供一个基于键盘的交互界面，让产品经理可以快速录制访谈、查看录音状态，并在停止后获得下一步处理命令。

## 功能

- **Ready Screen**：启动前确认 session、topic、design、branch
- **菜单选择器**：↑/↓ 切换选项，Enter 确认，q / Esc 退出
- **实时录音界面**：显示录音时长和音量条（bar / dot / wave 三种样式）
- **停止确认**：自动给出 `claude process-interview <sessionId>` 命令
- **配置分层**：CLI 参数 > 项目级 `.lincolnrc` > 用户级 `~/.lincolnrc` > 默认值

## 安装

```bash
cd tools/lincoln
npm install
npm run build
npm link
```

安装后，全局可用：

```bash
lincoln --help
```

## 使用

### 基本用法

```bash
lincoln 2026-06-28-checkout-interview \
  --topic "结算流程 redesign 需求访谈" \
  --design-id checkout-redesign \
  --branch lincoln/2026-06-28-recording-checkout-redesign
```

### 使用项目级配置 `.lincolnrc`

```bash
# 在项目根目录创建 .lincolnrc
cat > .lincolnrc <<EOF
topic: "结算流程 redesign 需求访谈"
design-id: checkout-redesign
branch: lincoln/2026-06-28-recording-checkout-redesign
audio-meter-style: wave
EOF

# 直接运行
lincoln 2026-06-28-checkout-interview
```

### 用户级配置

```bash
cat > ~/.lincolnrc <<EOF
topic: "默认访谈主题"
design-id: default-design
branch: main
EOF
```

配置优先级：**CLI 参数 > `.lincolnrc` > `~/.lincolnrc` > 默认值**。

## 快捷键

| 按键 | Ready Screen | Recording Screen | Stopped Screen |
|------|--------------|------------------|----------------|
| ↑ / ↓ | 移动菜单选择 | — | — |
| Enter | 确认选中项（开始录音 / 退出） | 停止录音 | 退出 |
| q / Esc | 退出 | 取消录音并退出 | 退出 |
| Ctrl+C | 退出 | 取消录音并退出 | 退出 |

## 界面说明

### Ready Screen

```
╭────────────────────────────────────────╮
│ ● ● ●        Lincoln Recorder          │
│                                        │
│ Session: 2026-06-28-checkout-interview │
│ Topic: 结算流程 redesign 需求访谈      │
│ Design: checkout-redesign              │
│ Branch: lincoln/...                    │
│                                        │
│ ▸ 开始录音 [Enter]                     │
│   退出     [q / Esc]                   │
╰────────────────────────────────────────╯
```

### Recording Screen

录音中显示当前时长和实时音量条。

### Stopped Screen

```
Stopped
Session 2026-06-28-checkout-interview saved.

Run this command in your terminal to generate knowledge artifacts:
claude process-interview 2026-06-28-checkout-interview

[any key] Exit
```

复制命令并在同一终端运行，即可触发访谈转写和摘要。

## CLI 选项

```
lincoln [session-id] [options]

Options:
  --topic       访谈主题
  --design-id   设计 ID
  --branch      Lincoln feature 分支名
  --session-id  显式指定 session ID
  --no-tui      不使用终端 UI 运行
  --help, -h    显示帮助
```

## 开发

```bash
cd tools/lincoln

# 安装依赖
npm install

# 开发模式（监听）
npm run dev

# 类型检查
npm run typecheck

# 运行测试
npm test

# 构建
npm run build
```

## 测试

使用 Vitest + `ink-testing-library`：

```bash
npm test
```

测试覆盖：

- 配置加载与合并
- Ready Screen 渲染和菜单选择
- 按键处理（Enter、q、Esc、方向键）
- 录音生命周期（start、stop、cancel）
- 停止后命令显示
- `useRecorder` hooks 依赖稳定性

## 架构

```
tools/lincoln/
├── src/
│   ├── main.ts              # CLI 入口
│   ├── config/              # 配置加载
│   ├── components/          # Ink UI 组件
│   ├── hooks/               # 通用 React hooks
│   └── recording/           # 录音子进程控制
├── tests/                   # Vitest 测试
├── package.json
├── tsconfig.json
└── README.md
```

## 与 lincoln-record 的关系

Lincoln TUI 本身不直接访问音频设备。它通过子进程启动 `tools/lincoln-record` Rust CLI，由后者完成本地录音与转写（whisper-rs + Metal 加速、说话人分离）。

TUI 只负责呈现界面和管理用户输入。停止录音后，TUI 打印命令，由用户手动触发 `claude process-interview`，避免嵌套 Claude Code 会话。

## 依赖

- Node.js >= 20
- `lincoln-record`（Rust 本地录音转写 CLI，见 `tools/lincoln-record/`，需用 cargo 构建）
- `claude` CLI（用于后续 `process-interview` 步骤）

## 许可证

MIT
