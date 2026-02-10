# Text-to-SQL Agent (Gemini 风格)

这是一个基于 LLM 的智能数据库查询助手。它可以理解用户的中文自然语言问题，结合 RAG（检索增强生成）技术查找相关的数据库表结构，自动生成 SQL 语句并在 MySQL 数据库中执行，最后用自然语言回答用户。

项目前端采用了仿 Google Gemini 的扁平化设计，支持流式对话和 Markdown 渲染。

## 📂 项目结构

```
day10/
├── agent/                  # Agent 核心逻辑
│   ├── base_agent.py       # ReAct 循环与 Agent 类
│   └── prompts.py          # System Prompt 定义
├── config/                 # 配置文件
│   └── settings.py         # 环境变量读取
├── data/                   # 数据文件
│   └── chinook_mysql.sql   # 测试用数据库脚本
├── frontend/               # Vue 3 前端项目
│   ├── src/
│   │   ├── components/     # Vue 组件 (ChatInterface, ChatMessage)
│   │   ├── style.css       # Gemini 风格样式
│   │   └── App.vue         # 主应用入口
├── models/                 # 数据模型 (Pydantic)
├── rag/                    # RAG 检索模块
│   ├── extractor.py        # Schema 提取器
│   ├── indexer.py          # 向量库构建
│   └── retriever.py        # 检索器
├── scripts/                # 工具脚本
│   ├── setup_database.py   # 数据库初始化
│   ├── build_rag_index.py  # RAG 索引构建
│   └── start_backend.sh    # (可选) 启动脚本
├── tools/                  # Agent 工具箱
│   └── core_functions.py   # 数据库操作工具 (List, Schema, Execute)
├── .env                    # 环境变量配置文件
├── api_server.py           # FastAPI 后端入口
├── main.py                 # 命令行交互入口
└── pyproject.toml          # Python 项目依赖
```

## 🛠️ 前置要求

在运行本项目之前，请确保您的环境中安装了以下软件：

1.  **Python 3.10+** (推荐使用 `uv` 管理依赖)
2.  **Node.js 18+** (用于前端)
3.  **MySQL 8.0 / MariaDB** (数据库服务)
4.  **DeepSeek API Key** (或其他兼容 OpenAI SDK 的 LLM)

## 🚀 快速启动

### 1. 环境配置

在项目目录下创建 `.env` 文件（参考 `.env.example`）：

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

### 2. 初始化数据与索引

```bash

# 1. 初始化数据库 (导入 Chinook 数据集)
uv run scripts/setup_database.py

# 2. 构建 RAG 向量索引
uv run scripts/build_rag_index.py
```

### 3. 启动服务

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

## ✨ 功能特性

*   **RAG 增强**: 即使有上百张表，Agent 也能通过语义检索快速找到相关表，避免 Token 溢出。
*   **安全执行**: 限制仅执行 `SELECT` 查询，防止数据被破坏。
*   **Gemini UI**: 现代化的前端界面，支持 Markdown 表格显示，交互流畅。
*   **智能纠错**: (开发中) Agent 能够根据报错信息尝试修正 SQL。

## 📚 技术栈

*   **LLM**: DeepSeek-V3 / OpenAI GPT-4
*   **Backend**: Python, FastAPI
*   **Vector Database**: ChromaDB (用于存储和检索表结构 Schema)
*   **Database**: MySQL 8.0
*   **ORM**: SQLAlchemy, Pydantic
*   **Frontend**: Vue 3, Vite
