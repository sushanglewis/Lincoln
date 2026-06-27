# Lincoln Record Interview CLI

在当前 Lincoln workspace 内录制访谈音频并触发 `process-interview`。

## 安装依赖

```bash
cd tools/record-interview
python -m pip install -e ".[dev]"
```

确保系统已安装 `ffmpeg` 和 `claude` CLI。

## 使用

```bash
record-interview 2026-06-27-stakeholder-checkout \
  --design-id checkout-redesign \
  --topic "结算流程 redesign 需求访谈" \
  --branch "lincoln/2026-06-27-stakeholder-checkout-checkout-redesign"
```

Or, if not using the installed console script:

```bash
python -m record_interview 2026-06-27-stakeholder-checkout \
  --design-id checkout-redesign \
  --topic "结算流程 redesign 需求访谈" \
  --branch "lincoln/2026-06-27-stakeholder-checkout-checkout-redesign"
```

按回车开始录音，再次按回车停止。确认后自动触发 `claude process-interview`。

## 快捷键

- `Enter`：停止录音
- `Ctrl+C`：取消录音（不触发 process-interview）

## 测试

```bash
cd tools/record-interview
python -m pytest tests/ -v
```
