# Text-to-SQL Agent (Gemini 风格)

这是一个基于 LLM 的智能数据库查询助手。它可以理解用户的中文自然语言问题，结合混合检索 (Vector + BM25) 查找相关的数据库表结构，支持长上下文与多轮追问，自动生成 SQL 语句并在 MySQL 数据库中安全执行，最后用自然语言回答用户。

项目前端采用了仿 Google Gemini 的扁平化设计，支持 Markdown 渲染（含表格）。

## 📂 项目结构

```
day10/
├── agent/                      # Agent 编排层
│   ├── base_agent.py           # ReAct 循环与 Agent 类
│   ├── tools.py                # 工具函数（db/rag/security 的薄封装）
│   └── prompts.py              # System Prompt 定义
├── db/                         # 数据库访问层
│   ├── engine.py               # 统一的 SQLAlchemy Engine 单例
│   ├── schema_extractor.py     # 从 MySQL 提取表结构 + 中文注释
│   ├── executor.py             # SQL 安全执行 + 结果格式化
│   └── session_store.py        # 基于 Redis 的多轮会话存储处理
├── rag/                        # 混合检索层 (RAG)
│   ├── indexer.py              # Schema 构建向量索引与 BM25 词库
│   └── retriever.py            # BM25 + Vector 混合相似度检索及 RRF 融合
├── security/                   # 安全层
│   ├── sql_validator.py        # SQL AST 安全校验 (sqlglot)
│   └── auth.py                 # JWT 鉴权与密码哈希处理
├── models/                     # 数据模型层
│   ├── schemas.py              # 数据库 Schema 模型 (TableSchema, ColumnSchema)
│   └── api.py                  # API 请求/响应模型 (ChatRequest, ChatResponse)
├── config/                     # 配置层
│   ├── settings.py             # 环境变量读取 (Pydantic Settings)
│   └── logging.py              # 日志配置 (loguru)
├── data/                       # 数据文件
│   ├── chinook_mysql.sql       # 测试用数据库脚本 (Chinook 数据集)
│   ├── chinook_zh.py           # Chinook 中文字段注释映射
│   ├── few_shot_examples.json  # Few-shot 示例 (问题-SQL 对)
│   └── chromadb_store/         # 向量索引持久化目录 (自动生成)
├── frontend/                   # Vue 3 前端项目
│   └── src/
│       ├── components/         # Vue 组件 (ChatInterface, ChatMessage)
│       ├── style.css           # Gemini 风格样式
│       └── App.vue             # 主应用入口
├── scripts/                    # 工具脚本
│   ├── setup_database.py       # 业务数据库初始化 (导入 Chinook)
│   ├── init_auth_db.py         # 用户认证数据库初始化 (users/sessions 表)
│   ├── build_rag_index.py      # RAG 索引构建
│   └── test_*.py               # 各模块手动测试脚本
├── docs/                       # 文档
│   └── optimization_list.md    # 优化修改清单
├── .env.example                # 环境变量模板（复制为 .env 后填入真实值）
├── .gitignore                  # Git 忽略规则
├── exceptions.py               # 自定义异常
├── api_server.py               # FastAPI 后端入口
├── main.py                     # 命令行交互入口
├── start.sh                    # 🚀 一键启动脚本 (包括前后端)
└── pyproject.toml              # Python 项目依赖 (uv 管理)
```

### 模块依赖方向

```
api_server.py / main.py       ← 入口层
        ↓
    agent/                     ← 编排层（调度下面三个模块）
        ↓
   ┌────┼────────┐
   ↓    ↓        ↓
 rag/  db/    security/        ← 功能层（互不依赖）
   ↓    ↓        ↓
 models/ + config/             ← 基础层（数据模型 + 配置）
```

## 🛠️ 前置要求

在运行本项目之前，请确保您的环境中安装了以下软件：

1.  **Python 3.10+**（推荐使用 [uv](https://docs.astral.sh/uv/) 管理依赖）
2.  **Node.js 18+**（用于前端）
3.  **MySQL 8.0 / MariaDB**（数据库服务，需已启动）
4.  **Redis**（用于多轮对话上下文缓存，建议开启）
5.  **DeepSeek API Key**（或其他兼容 OpenAI SDK 的 LLM）

## 🚀 快速启动

### 1. 环境配置

复制 `.env.example` 为 `.env` 并填入真实值：

```bash
cp .env.example .env
```

然后编辑 `.env`，填入你的实际配置：

```ini
# MySQL 配置
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=your_user
MYSQL_PASSWORD=your_password
MYSQL_DB=sql_rag_db

# LLM 配置 (DeepSeek)
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

### 2. 安装依赖

```bash
# 安装 Python 依赖
uv sync

# 安装前端依赖
cd frontend && npm install && cd ..
```

### 3. 初始化数据与索引

```bash
# 1. 创建数据库（如尚未创建）
mysql -u your_user -p -e "CREATE DATABASE IF NOT EXISTS sql_rag_db CHARACTER SET utf8mb4;"

# 2. 初始化业务数据库 (导入 Chinook 数据集)
uv run scripts/setup_database.py

# 3. 初始化用户认证数据库
uv run scripts/init_auth_db.py

# 4. 构建 RAG 向量索引
uv run scripts/build_rag_index.py
```

### 4. 启动服务

**推荐运行方式：一键启动**

项目根目录下提供了一个 `start.sh` 一键启动脚本，它会自动配置源、检查并释放被占用的端口、检查 Redis 状态，然后在后台同时启动 FastAPI 后端和 Vite 前端。

```bash
chmod +x start.sh
./start.sh
```

*(如果出现终端持续挂起，那是脚本在后台运行，按 `Ctrl+C` 即可一键安全停止所有的前后端服务)*

---

**手动分步启动（如果不用 start.sh）：**

**终端 1: 启动后端 (FastAPI)**
```bash
uv run api_server.py
# 服务将运行在 http://localhost:8000
```

**终端 2: 启动前端 (Vue + Vite)**
```bash
cd frontend
npm run dev
# 服务将运行在 http://localhost:5173
```

现在，打开浏览器访问前端显示的地址即可开始对话！

## 🧪 命令行模式 (可选)

如果你不想启动前端，也可以通过命令行直接测试：

```bash
uv run main.py
```

## 💬 示例问答

以下是一些可以直接尝试的查询示例（基于 Chinook 音乐数据库）：

| 问题 | 说明 |
|------|------|
| 统计每种流派的歌曲数量，按数量从高到低排序 | 分组聚合 + 排序 |
| 查找 'Iron Maiden' 乐队的所有专辑 | 多表 JOIN 查询 |
| 列出购买金额最高的 3 位客户 | 聚合 + TOP-N |
| 查询时长超过 5 分钟的 Rock 歌曲 | 多条件过滤 |
| 哪位员工处理的发票总金额最高？ | 跨多表关联统计 |

## ✨ 功能特性

-   **用户系统与认证**：基于 JWT 实现用户注册、登录，确保数据隔离与安全。
-   **会话历史管理**：用户登录后可查看并恢复历史对话，支持多会话并行。
-   **混合检索 (Hybrid RAG)**：结合 ChromaDB 语义向量 (`bge-base-zh-v1.5`) 与 BM25 关键词检索，双路召回并使用 RRF 算法融合，大幅提升中文场景与业务命名精确匹配的准确率
-   **多轮对话支持**：基于 Redis 会话存储管理和上下文截断压缩策略，实现长效的多轮追问及意图继承能力
-   **全链路异步流式响应 (SSE)**：后端基于 `AsyncOpenAI` 和 FastAPI 实现 SSE 流式推送，响应更及时，提升用户体验
-   **全链路安全防护**：重构组件连接池与 Agent 局域状态隔离，杜绝并发污染；后端使用 `sqlglot` 将 SQL 解析为 AST 拦截写操作；前端引入 `DOMPurify` 洗消防御 XSS 攻击，确保渲染安全
-   **Gemini UI 与折叠思考流**：仿 Google Astro/Gemini 界面设计，支持 Markdown 渲染。具备动态提取 `<plan>`、`<thought>` 等思考过程并将其在前端折叠的功能，界面清爽
-   **Few-shot 学习**：内置典型查询示例，提升复杂 SQL（多表 JOIN、聚合等）的生成准确率
-   **中文注释增强**：对 Chinook 数据集提供完整的中文字段描述映射，帮助 LLM 理解数据含义

## 🏗️ 架构设计与处理流程

本项目采用 **ReAct (Reasoning and Acting) Agent 结合 RAG (Retrieval-Augmented Generation)** 架构，旨在演示 Text-to-SQL 系统的一种实现方式，解决大模型面对大量数据库表时的"幻觉"和"Token 上下文溢出"问题。

### 系统处理流程

整个系统的工作流是一个智能调度的循环过程（Agent Loop）：

1.  **意图接收**：FastAPI 后端接收用户自然语言查询，调用 ReAct Agent 的 `stream_run` 异步方法
2.  **Schema 召回 (RAG)**：Agent 调用 `list_tables_tool`，系统利用 ChromaDB 通过语义向量相似度匹配，召回与当前问题最相关的 Top-5 张表
3.  **结构解析**：Agent 调用 `get_schema_tool`，系统实时从 MySQL 中提取这几张表完整的 DDL 语句及字段注释
4.  **SQL 生成与审阅**：LLM 基于表结构上下文生成 SQL，生成的 SQL 被 sqlglot 解析为 AST，实施安全准入检查（拦截 `DROP`、`UPDATE`、`DELETE` 等非读操作）
5.  **数据获取与总结**：通过校验的 `SELECT` 语句在 MySQL 中执行，结果集（限 20 行）转化为 Markdown 表格，交还给 LLM 进行自然语言总结
6.  **双层持久化存储**：实时通话消息首先由 `session_store.py` 写入 Redis 以保证极速响应；当 SSE 数据流结束时，系统会自动将完整的对话上下文同步至 MySQL 数据库，实现长效持久化和多终端同步

### API 接口 (v1)

| 方法 | 路径 | 说明 | 请求体内容 |
|------|------|------|------------|
| POST | `/api/v1/auth/register` | 用户注册 | `username`, `password` |
| POST | `/api/v1/auth/login` | 用户登录 | `username`, `password` |
| GET | `/api/v1/sessions` | 获取当前用户会话列表 | - |
| GET | `/api/v1/sessions/{id}` | 获取特定会话详情 | - |
| POST | `/api/chat` | 发送问题（流式 SSE） | `message`, `session_id` |
| GET | `/health` | 健康检查 | - |

## ⚠️ 已知限制

本项目存在以下局限性或待优化点：

-   **大规模表极光召回局限**：在超大规模表场景 (>500张) 下，可能需要引入基于业务域过滤的更细颗粒度（字段级）检索

> 详细的优化方案和重构建议见 [优化修改清单](docs/optimization_list.md)

## 📚 技术栈

| 类别 | 技术 |
|------|------|
| **LLM** | DeepSeek-V3 / OpenAI GPT-4（基于 OpenAI 兼容 SDK） |
| **Backend** | Python, FastAPI, Uvicorn |
| **Vector Database** | ChromaDB（向量检索, bge-base-zh-v1.5） + rank-bm25（关键词匹配） |
| **Database** | MySQL 8.0（业务数据存储） |
| **Cache Store** | Redis（会话和历史状态维持） |
| **ORM / Parse** | SQLAlchemy（数据库访问）, Pydantic（数据校验）, sqlglot（SQL AST 安全解析） |
| **工具库** | loguru（日志）, pandas（结果表格化）, jieba（分词） |
| **Frontend** | Vue 3 + Vite（组合式 API） |
| **包管理** | uv（Python）, npm（前端） |
