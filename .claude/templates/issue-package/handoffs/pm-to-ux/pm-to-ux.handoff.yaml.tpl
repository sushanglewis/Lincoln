contract_version: "1.0.0"
issue_number: "{issue_number}"
feature_slug: "{design_id}"
from_stage: "product-design-docs"
to_stage: "product-prototype"
from_agent: "lc-pm"
to_agent: "lc-designer"
handoff_type: "pm-to-ux"

human_master_doc:
  path: "{process_slug}/handoffs/pm-to-ux/master-handoff-pm-to-ux-v{major}.{minor}.md"
  version: "v{major}.{minor}"

based_on:
  - path: "{process_slug}/requirements/{session_id}/requirements.md"
    version: "v1.0"
  - path: "{process_slug}/requirements/{session_id}/user-stories.md"
    version: "v1.0"
  - path: "{process_slug}/requirements/{session_id}/prd.md"
    version: "v1.0"
  - path: "{process_slug}/designs/{design_id}/feature-catalog.md"
    version: "v1.0"
  - path: "{process_slug}/designs/{design_id}/scenarios.md"
    version: "v1.0"
  - path: "{process_slug}/designs/{design_id}/flows.md"
    version: "v1.0"
  - path: "{process_slug}/designs/{design_id}/page-map.md"
    version: "v1.0"

context_pack:
  tier_0:
    - path: "{process_slug}/handoffs/pm-to-ux/pm-to-ux.handoff.yaml"
      reason: "本契约本身；UX Agent 必须从此开始"
  tier_1:
    - path: "{process_slug}/handoffs/pm-to-ux/master-handoff-pm-to-ux-v{major}.{minor}.md"
      reason: "人类主文档，建立全局认知"
  tier_2:
    - feature: "<feature-name>"
      links:
        - path: "{process_slug}/requirements/{session_id}/requirements.md#{anchor}"
          reason: "需求"
        - path: "{process_slug}/requirements/{session_id}/user-stories.md#{anchor}"
          reason: "用户故事"
        - path: "{process_slug}/designs/{design_id}/feature-catalog.md#{anchor}"
          reason: "功能定义"
        - path: "{process_slug}/designs/{design_id}/flows.md#{anchor}"
          reason: "流程"
        - path: "{process_slug}/designs/{design_id}/page-map.md#{anchor}"
          reason: "页面关系"

reading_rules:
  - "必须从 tier_0 开始，按 tier_1 → tier_2 顺序读取"
  - "tier_2 按 feature 分组，每个 feature 最多 2 跳"
  - "禁止直接读取 tier_3 原始访谈/录音，除非 tier_2 链接明确要求"

open_questions:
  - id: "Q001"
    question: ""
    owner: "pm"
    status: "open"

approval:
  pm_confirmed: false
  approved_at: ""
  approved_by: ""

notes: |
  本契约由 `scripts/stage_loader.py --action handoff-report` 自动刷新状态字段。
  任何 `based_on` 文档版本升级后，必须重新生成本契约并更新 `based_on` 中的 version。
