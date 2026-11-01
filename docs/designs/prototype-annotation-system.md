# Axure 式原型标注系统实施说明

- Issue：#155
- 目标版本：v1.12.0
- 状态：已实施

## 根因

旧实现只有 `hotspots[{target,title,text}]`：

1. 校验只检查数组存在，一句泛化说明即可通过。
2. 缺少页面、交互、状态、异常、数据的结构化内容模型。
3. 目标不存在时运行时静默跳过，产物可能没有角标却仍通过。
4. 只有短 popover，没有页面级阅读和演示机制，无法承载完整评审说明。

## 方案

### 内容层

每页新增 `annotations`，包含 overview、sections、interactions、states、exceptions、data。保留 traceability 的 REQ/US/FLOW 元数据，展示文案与追溯 ID 分离。

### 展示层

`prototype.js` 将结构化说明映射为：

- 页面元素数字角标。
- 页面结构/交互/状态与异常/数据四分类抽屉。
- 上一条/下一条演示和元素高亮。
- 状态页面导航、键盘 Escape/左右键操作。

旧 hotspots 继续用 driver.js popover；结构化页面可附带旧 hotspots 作为补充。

### 质量层

`lincoln_prototype_annotations.py` 对全部 HTML 原型检查内容、目标、状态、恢复、数据、链接和业务语言。共享 Stage/Workflow 新增 `prototype_annotations_complete`，只对 core-v2 强制，legacy 自动跳过。

### 兼容与边界

- 不改变 PRD、traceability 或评审 sidecar 格式。
- 不新增运行时网络请求，所有说明嵌入 pageData，静态托管可用。
- 旧原型不强制回填；重新生成 core-v2 页面时采用新契约。
- 输入框等不能包含子按钮的元素，角标锚定到父容器，说明高亮仍指向真实元素。

## 验证

- 金标准与缺状态、缺目标、缺恢复、技术化叙述等反例。
- 渲染契约、共享 registry 和 Stage/Workflow drift 测试。
- 真实浏览器验证角标、抽屉、四类页签、分步演示、高亮和状态内容。
