# Research Copilot 整体架构设计

## 1. 文档职责

本文档是项目根目录的整体架构说明，描述系统边界、模块划分、依赖方向、数据所有权和跨模块流程。

- 产品需求以 `Requirement.md` 为准。
- 各模块内部设计以模块目录中的 `AGENTS.md` 为准。
- 根目录文档不记录协作规则、个人偏好或修改历史。
- 模块设计不得扩大 `Requirement.md` 已确认的第一版范围。

## 2. 系统定位

系统是 Windows 本地运行的单用户 AI 论文研究助手，由 Vue 桌面端 Web 界面、FastAPI 后端和项目内置 Arxiv MCP Server 组成。

```text
Vue 3 前端
    │ REST / SSE
    ▼
FastAPI 后端
    ├─ 论文、分组、导入、会话、RAG
    ├─ SQLite / 本地 PDF / Chroma
    ├─ DeepSeek OpenAI 兼容接口
    ├─ Ollama bge-m3
    └─ MCP Client
           │ stdio
           ▼
      Arxiv MCP Server
           │
           ▼
      Arxiv API / PDF
```

## 3. 顶层模块

| 模块 | 路径 | 核心职责 |
|---|---|---|
| 后端应用 | `backend/` | 提供 REST、SSE、后台任务和业务编排 |
| 论文模块 | `backend/papers/` | 论文记录、元数据、标签、文件下载与删除 |
| 分组模块 | `backend/groups/` | 一级分组、多对多关系和“未分类”虚拟视图 |
| 导入模块 | `backend/ingestion/` | 本地与 Arxiv 导入、解析、分块和向量化任务 |
| RAG 模块 | `backend/rag/` | 受控 LangGraph 检索、评估、改写、生成和引用校验 |
| 会话模块 | `backend/conversations/` | 多会话、消息、SSE 生命周期、模型选择、压缩和导出 |
| 基础设施模块 | `backend/infrastructure/` | 配置、数据库、Chroma、模型适配器、MCP Client、日志和健康检查 |
| 前端应用 | `frontend/` | Vue 应用壳、路由、跨模块状态和通用交互约定 |
| 论文库界面 | `frontend/paper-library/` | 上传、列表、搜索筛选、元数据编辑和任务状态 |
| 分组界面 | `frontend/groups/` | 分组管理、成员关系和未分类视图 |
| Arxiv 导入界面 | `frontend/arxiv-import/` | Arxiv 搜索、结果选择和直接导入 |
| 问答界面 | `frontend/chat/` | 会话、模型选择、SSE、富文本、压缩和导出 |
| MCP 层 | `mcp/` | 项目内 MCP Server 的公共边界 |
| Arxiv MCP | `mcp/arxiv/` | Arxiv 查询、元数据标准化和 PDF 下载工具 |

## 4. 依赖方向

允许的主要依赖方向：

```text
frontend 功能模块
        │
        ▼
backend 对应 API / 应用服务
        │
        ├────────► infrastructure 端口与适配器
        │
        └────────► 其他业务模块公开接口
                         │
                         ▼
                    mcp/arxiv
```

约束：

- 前端不得直接访问 SQLite、Chroma、Ollama、DeepSeek 或 MCP。
- MCP 模块不得访问业务数据库，也不得持有会话状态。
- 业务模块不得直接读取环境变量；统一通过 `backend/infrastructure/` 暴露的配置对象。
- 业务模块不得自行创建日志格式；统一使用基础设施日志上下文和 `request_id`。
- 跨模块调用必须通过公开服务或端口接口，不直接依赖其他模块的存储实现。
- RAG 不负责持久化会话；会话模块负责调用 RAG 并保存最终结果。
- 导入模块负责处理流水线，但论文记录生命周期归论文模块所有。

## 5. 数据所有权

| 数据 | 所有模块 | 存储 |
|---|---|---|
| 论文、标签、论文标签关系 | papers | SQLite |
| 原始 PDF、分页文本 | papers；由 ingestion 写入 | 本地文件 |
| 分组、论文分组关系 | groups | SQLite |
| 导入任务与处理状态 | ingestion | SQLite |
| 文本块向量与页码元数据 | ingestion 写入，rag 读取 | Chroma |
| 会话、消息、引用、压缩摘要 | conversations | SQLite |
| 可选模型和运行参数 | infrastructure | `config.py` / `.env` |
| 接口与任务日志 | infrastructure | 控制台 / 轮转文件 |
| Arxiv 临时查询结果 | mcp/arxiv 返回，不长期持有 | 内存 |

## 6. 跨模块流程

### 6.1 本地 PDF 导入

```text
paper-library
→ ingestion API
→ papers 创建论文记录并保存 PDF
→ ingestion 后台解析、分页、分块
→ infrastructure 调用 Ollama
→ ingestion 写入 Chroma
→ papers / ingestion 更新处理状态
```

### 6.2 Arxiv 导入

```text
arxiv-import
→ ingestion API
→ infrastructure MCP Client
→ mcp/arxiv 查询或下载
→ papers 创建独立论文记录
→ ingestion 进入统一后台处理流程
```

### 6.3 问答

```text
chat
→ conversations 创建用户消息并启动 SSE
→ rag 根据论文或分组解析检索范围
→ infrastructure 读取 Chroma并调用 DeepSeek
→ rag 校验引用并返回流式事件与最终结果
→ conversations 持久化完成的回答和引用
```

### 6.4 上下文压缩

```text
chat 手动触发或 conversations 自动检测
→ conversations 选取累计摘要与较早消息
→ infrastructure 调用配置的压缩模型
→ conversations 原子更新摘要和压缩位置
→ 原始消息保持不变
```

## 7. 跨模块一致性规则

- 论文删除由应用服务编排：先锁定论文，清理会话、关系、向量和文件，再删除论文记录；失败必须记录并返回 `request_id`。
- 分组删除由分组模块发起，会话模块删除对应分组会话，论文记录保持不变。
- “未分类”始终由无普通分组关系的查询结果计算，不存储实体。
- 每次导入创建独立论文记录，不做跨记录去重。
- 引用只接受本轮实际检索文本块中的论文名称和 PDF 物理页码。
- 所有外部接口、SSE、后台任务、模型、向量库和 MCP 调用进入统一日志链路。
- 日志不得包含问题、回答、论文正文、PDF 内容或凭据。
- 第一版不写自动化测试，仅按 `Requirement.md` 执行手工验收。

## 8. 配置与安全

- 项目根目录 `config.py` 是全部可调参数的统一入口。
- `.env` 仅保存敏感值，业务模块不得直接解析。
- 前端只能读取允许公开的模型标识、显示名称和上下文窗口。
- 本地文件路径必须由后端根据内部 ID 解析，API 不接受任意绝对路径。
- Markdown 渲染必须过滤不可信 HTML 和脚本。
- 健康检查不得泄露密钥、论文内容或本地敏感路径。

## 9. 前后端接口契约

- 开发环境中，Vue 通过 `VITE_API_BASE` 访问 FastAPI；未配置时使用 `http://127.0.0.1:8000`。
- 普通业务使用 REST，前端请求统一携带 `X-Request-ID`，后端在响应头和错误体中返回同一标识。
- 错误体统一包含错误码、中文消息、`request_id` 和可选安全详情；前端向用户展示请求标识以便关联日志。
- 论文资源接口使用 `/api/papers/{paper_id}` 路径参数，`paper_id` 按 UUID 校验；文件路径不由前端传入。
- PDF 上传后由前端轮询论文状态，等待、解析和向量化状态继续轮询，完成、失败或中断后停止。
- PDF 下载通过鉴权一致的请求封装读取 Blob，不在第一版提供内嵌阅读或页码跳转。
- 浏览器只通过后端公开接口访问论文、文件和处理状态，不直接访问本地存储、SQLite、Chroma 或 Ollama。
