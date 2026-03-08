# Text-to-SQL Agent (Gemini 风格)

这是一个基于 LLM 的智能数据库查询助手（概念验证 / 教学演示项目）。它可以理解用户的中文自然语言问题，结合 RAG（检索增强生成）技术查找相关的数据库表结构，自动生成 SQL 语句并在 MySQL 数据库中执行，最后用自然语言回答用户。

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
│   └── executor.py             # SQL 安全执行 + 结果格式化
├── rag/                        # RAG 向量检索层
│   ├── indexer.py              # Schema 向量索引构建 (ChromaDB)
│   └── retriever.py            # 语义相似度检索
├── security/                   # 安全层
│   └── sql_validator.py        # SQL AST 安全校验 (sqlglot)
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
│   ├── setup_database.py       # 数据库初始化 (导入 Chinook)
│   ├── build_rag_index.py      # RAG 索引构建
│   └── test_*.py               # 各模块手动测试脚本
├── docs/                       # 文档
│   └── optimization_list.md    # 优化修改清单
├── exceptions.py               # 自定义异常
├── api_server.py               # FastAPI 后端入口
├── main.py                     # 命令行交互入口
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

1. **Python 3.10+**（推荐使用 [uv](https://docs.astral.sh/uv/) 管理依赖）
2. **Node.js 18+**（用于前端）
3. **MySQL 8.0 / MariaDB**（数据库服务，需已启动）
4. **DeepSeek API Key**（或其他兼容 OpenAI SDK 的 LLM）

## 🚀 快速启动

### 1. 环境配置

在项目根目录下创建 `.env` 文件：

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

# 2. 初始化数据库 (导入 Chinook 数据集)
uv run scripts/setup_database.py

# 3. 构建 RAG 向量索引
uv run scripts/build_rag_index.py
```

### 4. 启动服务

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

- **RAG 增强**：通过 ChromaDB 语义检索快速定位相关表，避免将全库 Schema 塞入 Prompt 导致 Token 溢出
- **安全执行**：使用 sqlglot 将 SQL 解析为 AST，严格限制仅执行 `SELECT` 查询，拦截所有写操作
- **Gemini UI**：仿 Google Gemini 的前端界面，支持 Markdown 表格渲染
- **Few-shot 学习**：内置典型查询示例，提升复杂 SQL（多表 JOIN、聚合等）的生成准确率
- **中文注释增强**：对 Chinook 数据集提供完整的中文字段描述映射，帮助 LLM 理解数据含义

## 🏗️ 架构设计与处理流程

本项目采用 **ReAct (Reasoning and Acting) Agent 结合 RAG (Retrieval-Augmented Generation)** 架构，旨在演示 Text-to-SQL 系统的一种实现方式，解决大模型面对大量数据库表时的"幻觉"和"Token 上下文溢出"问题。

### 系统处理流程

整个系统的工作流是一个智能调度的循环过程（Agent Loop）：

1. **意图接收**：FastAPI 后端接收用户自然语言查询，调用 ReAct Agent 实例
2. **Schema 召回 (RAG)**：Agent 调用 `list_tables_tool`，系统利用 ChromaDB 通过语义向量相似度匹配，召回与当前问题最相关的 Top-5 张表
3. **结构解析**：Agent 调用 `get_schema_tool`，系统实时从 MySQL 中提取这几张表完整的 DDL 语句及字段注释
4. **SQL 生成与审阅**：LLM 基于表结构上下文生成 SQL，生成的 SQL 被 sqlglot 解析为 AST，实施安全准入检查（拦截 `DROP`、`UPDATE`、`DELETE` 等非读操作）
5. **数据获取与总结**：通过校验的 `SELECT` 语句在 MySQL 中执行，结果集（限 20 行）转化为 Markdown 表格，交还给 LLM 进行自然语言总结

### API 接口

| 方法 | 路径 | 说明 | 请求体 | 响应体 |
|------|------|------|--------|--------|
| POST | `/api/chat` | 发送问题并获取回答 | `{"message": "你的问题"}` | `{"response": "Agent 的回答"}` |
| GET | `/health` | 健康检查 | - | `{"status": "ok"}` |

## ⚠️ 已知限制

本项目为概念验证/教学演示，存在以下局限性：

- **不支持多轮对话**：每次提问都是独立会话，无法基于上一轮结果追问
- **不支持流式输出**：需等待 Agent 完整执行完毕后才返回结果
- **仅支持只读查询**：出于安全考虑，仅允许 `SELECT` 操作
- **Embedding 模型偏英文**：当前使用 `all-MiniLM-L6-v2`，中文语义匹配能力有限
- **表规模限制**：当前架构在 20-200 张表范围内效果较好，超出后检索召回率下降

> 详细的优化方案和重构建议见 [优化修改清单](docs/optimization_list.md)

## 📚 技术栈

| 类别 | 技术 |
|------|------|
| **LLM** | DeepSeek-V3 / OpenAI GPT-4（基于 OpenAI 兼容 SDK） |
| **Backend** | Python, FastAPI, Uvicorn |
| **Vector Database** | ChromaDB（Schema 语义检索，Embedding: all-MiniLM-L6-v2） |
| **Database** | MySQL 8.0（业务数据存储） |
| **ORM / Parse** | SQLAlchemy（数据库访问）, Pydantic（数据校验）, sqlglot（SQL AST 安全解析） |
| **工具库** | loguru（日志）, pandas（结果表格化） |
| **Frontend** | Vue 3 + Vite（组合式 API） |
| **包管理** | uv（Python）, npm（前端） |
