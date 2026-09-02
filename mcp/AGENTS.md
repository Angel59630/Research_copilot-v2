# MCP 层架构设计

## 1. 模块职责

`mcp/` 存放项目内置 MCP Server。第一版仅包含 Arxiv Server，通过 stdio 被 FastAPI 后端启动和管理。

## 2. 约束

- MCP Server 是无业务状态的外部数据适配层。
- 不访问 SQLite、Chroma、会话或前端。
- 不负责论文入库、分组或向量化。
- stdout 仅用于 MCP 协议，诊断信息写入 stderr 并由宿主日志采集。
- 工具输入输出使用明确的结构化类型。
- 网络请求设置超时并遵守外部服务使用条款。
- MCP 错误返回稳定错误类别，不暴露本地敏感路径。
