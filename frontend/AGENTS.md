# 前端应用架构设计

## 1. 职责

`frontend/` 是 Vue 3 单页应用边界，负责路由、跨模块状态、后端接口适配、错误提示和通用交互。前端只消费 FastAPI 公开的 REST/SSE 接口。

## 2. 技术边界

- 使用 Vue 3、TypeScript、Pinia、Vue Router 和 Element Plus。
- `src/api/` 集中管理接口地址、请求标识、响应解析和业务 API，页面组件不得散落后端地址或重复实现错误解析。
- `src/stores/` 管理跨组件业务状态和后台状态轮询。
- 页面只传递内部资源 ID，不传递本地绝对路径。
- 用户可见错误使用中文，并在后端提供时附带 `request_id`。

## 3. 开发环境联调

- 后端地址通过 `VITE_API_BASE` 配置，默认值为 `http://127.0.0.1:8000`。
- 所有请求生成 `X-Request-ID`；上传使用 `FormData`，不得手动设置 multipart 的 `Content-Type`。
- 文件下载通过统一客户端获取 Blob，以便保持一致的错误和请求标识处理。
- SSE 使用 `fetch` 流式读取并支持 `AbortController`，不使用只能发起 GET 的原生 `EventSource`。

## 4. 边界

- 不直接访问 SQLite、Chroma、Ollama、DeepSeek、MCP 或项目数据目录。
- 不在前端保存模型密钥和敏感配置。
- 不把失败或中止的临时流式回答当作正式历史。
