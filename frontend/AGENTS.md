# 前端应用架构设计

## 1. 模块职责

`frontend/` 是 Vue 3 桌面端应用边界，负责应用壳、路由、全局错误处理、API 基础客户端、SSE 客户端和跨模块界面规范。

## 2. 技术约束

- Vue 3、TypeScript、Vite、Element Plus、Vue Router、Pinia。
- 仅中文界面，论文原始元数据保持原语言。
- 目标为宽度不低于 1280px 的桌面浏览器。
- 不实现完整移动端适配。
- 不引入 PDF.js、Vitest 或 Playwright。

## 3. 功能模块

- `paper-library/`：论文上传、管理、搜索和任务状态。
- `groups/`：分组、成员和未分类视图。
- `arxiv-import/`：Arxiv 搜索与导入。
- `chat/`：会话、SSE、模型、富文本、压缩和导出。

## 4. 共享约定

- 所有后端请求通过统一 API 客户端，自动处理 `request_id`。
- 前端不保存或展示 API Key。
- Pinia 仅保存界面和会话状态，后端数据以 API 为事实来源。
- 错误提示使用中文摘要并展示 `request_id`。
- 删除论文、分组和会话必须使用明确的二次确认。
- Markdown 渲染必须过滤不可信 HTML 和脚本。
- 功能模块不得直接访问其他模块的内部 store 或组件，通过公开组合函数、事件或路由参数协作。
