<!-- status: approved -->
# ingest 阶段跳过说明（issue-139）

- 日期：2026-10-16
- 决策：本 issue 无访谈录音，`ingest` 阶段跳过；首个激活阶段为 `clarify`。
- 依据：interview-to-knowledge 的 ingest 依赖 `{recording_path}`；issue-139 的输入为 GitHub issue #139 文本，无音频输入。
- 记录方式：`workflow-stage.yaml` 中 ingest 节点标记 completed，本文件作为决策留痕。
