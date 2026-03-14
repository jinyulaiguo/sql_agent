# Text-to-SQL Agent 全面优化修改列表

> 基于对 day10 项目所有核心文件的逐行审查，按**底层架构 → 业务流程 → 生产级代码质量**三个维度整理。  
> 每项标注优先级：🔴 P0（必须修复） | 🟡 P1（强烈建议） | 🔵 P2（锦上添花）

---

## 一、底层架构层

### 1.1 🔴 并发模型重构 —— Agent 实例管理 ✅ 已修复

| 项目 | 说明 |
|------|------|
| **问题** | 曾经 `base_agent.py` 使用全局消息列表，导致多用户并发干扰。 |
| **现状** | **已修复**：`messages` 已改为 `stream_run()` 方法的局部变量，确保了请求间的状态隔离。 |

### 1.2 🔴 事件循环阻塞 —— async 函数中调用同步代码 ✅ 已修复

| 项目 | 说明 |
|------|------|
| **问题** | `api_server.py:27` 用 `async def chat_endpoint` 但直接调 `agent.run()`（同步阻塞），会阻塞整个 asyncio 事件循环，卡死其他所有请求 |
| **文件** | [api_server.py](file:///Users/zhouyi/01.python-program/ai-project/10.practiseLike09/day10/api_server.py) |
| **方案A** | 改为 `def chat_endpoint`（非 async），FastAPI 会自动放入线程池执行 |
| **方案B** | 保持 async，用 `await asyncio.to_thread(agent.run, request.message)` |
| **方案C**（终极） | **已实现**：全链路异步化：`agent.run` 改 async，数据库用 `aiomysql`/`asyncmy`，LLM 调用用 `AsyncOpenAI` |

### 1.3 🟡 数据库连接管理 —— Engine 碎片化 ✅ 已修复

| 项目 | 说明 |
|------|------|
| **问题** | `core_functions.py:12`、`extractor.py:29`、`db_tools.py:11` 各自 `create_engine()`，三个独立连接池，资源浪费 |
| **方案** | 统一抽取为 `config/database.py` 提供单例 `engine`，其他模块全部 import |

### 1.4 🟡 依赖注入缺失 —— 模块级单例问题

| 项目 | 说明 |
|------|------|
| **问题** | `extractor.py:102` `schema_extractor = SchemaExtractor()`、`retriever.py:35` `retriever = SchemaRetriever()` 、`indexer.py:63` `indexer = SchemaIndexer()` 都在模块加载时实例化，import 时就连库 |
| **副作用** | 单元测试无法 mock；任何 import 链都会触发 DB/ChromaDB 连接；模块间循环依赖风险 |
| **方案** | 改用工厂函数 + `@lru_cache`，或引入 FastAPI 的 `Depends()` 依赖注入 |

### 1.5 🔵 全链路异步化（长期目标） ✅ 已实现

| 项目 | 说明 |
|------|------|
| **内容** | **已实现**：`agent.stream_run()` 为异步生成器、使用 `AsyncOpenAI`、后端 API 采用 SSE 流式推送。 |
| **收益** | 10 倍以上吞吐量提升，前端可实时看到 Agent 思考过程 |

---

## 二、业务流程层

### 2.1 🟡 多轮对话支持 ✅ 已修复

| 项目 | 说明 |
|------|------|
| **现状** | **已实现**：引入了基于 Redis 的 `session_store.py` 和基于 MySQL 的持久化，支持上下文追问与历史回顾。 |
| **方案** | 引入 `session_id` 概念，服务端维护会话历史（内存/Redis），支持上下文连续对话，同时设置历史截断策略防止 Token 爆涨 |

### 2.2 🟡 RAG 检索质量提升 ✅ 已修复

| 项目 | 说明 |
|------|------|
| **现状** | **已实现**：已切换为 `bge-base-zh-v1.5` 中文向量模型，并引入了 BM25 + Vector 的双路召回与 RRF 融合。 |
| **方案** | 引入 BM25 + Vector 混合检索，并使用 RRF (Reciprocal Rank Fusion) 算法融合结果。 |

### 2.3 🟡 SQL 执行结果截断策略

| 项目 | 说明 |
|------|------|
| **问题** | `execute_sql_tool` 仅在 Python 层 `fetchmany(20)` 截断，但 MySQL 已经全量查出数据，大表会 OOM |
| **文件** | [core_functions.py](file:///Users/zhouyi/01.python-program/ai-project/10.practiseLike09/day10/tools/core_functions.py) |
| **方案** | 用 `sqlglot` AST 检查 SQL 是否有 LIMIT，如没有则**自动注入** `LIMIT 50`（在执行前改写 SQL） |

### 2.4 🟡 Agent 自纠错机制

| 项目 | 说明 |
|------|------|
| **现状** | SQL 执行报错后直接把 error 返回 LLM，但没有显式引导 LLM 修正（需要 LLM 自己发现错误并重试）|
| **方案** | 在 Prompt 中增加明确的错误修复指令模板；设计重试计数器（最多 retry 2 次）；在 tool result 中附带原始 SQL + 错误分析提示 |

### 2.5 🔵 查询缓存

| 项目 | 说明 |
|------|------|
| **内容** | 对相同/相似问题的 SQL 结果做缓存（Redis / 内存 LRU），避免重复调用 LLM 和 DB |
| **收益** | 大幅降低延迟和 API 调用费用 |

### 2.6 🔵 Agent 思考过程透明化 ✅ 已实现

| 项目 | 说明 |
|------|------|
| **内容** | **已实现**：后端通过 SSE 分阶段推送 `tool` 和 `content` 事件，前端通过 `ChatMessage.vue` 的 `<thought>` 标签解析实现动态折叠展示。 |
| **方案** | 后端 SSE 推送中间状态，前端用步骤条或思维链卡片渲染 |

---

## 三、生产级代码质量层

### 3.1 🔴 删除死代码 —— `db_tools.py` ✅ 已修复

| 项目 | 说明 |
|------|------|
| **问题** | `tools/db_tools.py` 整个文件从未被任何模块 import，是重构残留 |
| **危害** | 其 `execute_sql` 用字符串前缀检查 `startswith("select")`，安全性极差，留着会误导后续开发者 |
| **方案** | 直接删除此文件 |

### 3.2 🔴 消除冗余分支 ✅ 已修复

| 项目 | 说明 |
|------|------|
| **问题** | `base_agent.py:164-171` 三个 if-elif 分支做的事完全一样（都是 `func(**arguments)`） |
| **方案** | 替换为一行：`result = func(**arguments)` |

### 3.3 🔴 XSS 安全风险 —— v-html 渲染未经洗消的内容 ✅ 已修复

| 项目 | 说明 |
|------|------|
| **问题** | `ChatMessage.vue:73` 使用 `v-html` 渲染 Markdown 解析后的内容 |
| **方案** | **已实现**：引入 `DOMPurify` 库对 Markdown 解析后的 HTML 进行洗消 (Sanitize) 后再渲染 |
| **效果** | 有效防御通过 LLM 注入的恶意脚本，增强前端安全性 |

### 3.4 🟡 敏感信息泄漏 ✅ 已修复

| 项目 | 说明 |
|------|------|
| **现状** | **已修复**：API 层异常处理已统一化，不向前端暴露详细 Traceback；DB 错误信息已脱敏处理。 |
| **方案** | 移除默认密码，`.env` 未配置时直接报错终止；API 层返回统一错误消息（如 `"服务暂时不可用"`），详细错误只写日志 |

### 3.5 🟡 前端 API 地址硬编码

| 项目 | 说明 |
|------|------|
| **问题** | `ChatInterface.vue` 中写死 `http://localhost:8000/api/chat` 等地址 |
| **方案** | 使用 Vite 环境变量 `import.meta.env.VITE_API_BASE_URL`，并在 `vite.config.js` 中通过 `proxy` 实现跨域代理 |

### 3.6 🟡 日志规范化 ✅ 已修复

| 项目 | 说明 |
|------|------|
| **现状** | **已完成**：建立了独立的 `config/logging.py`，配置了 Loguru 的日志格式、级别及异步写入。 |
| **方案** | 新建 `config/logging.py`，统一配置 loguru：生产环境输出 JSON 格式到文件 + rotation，开发环境彩色终端输出 |

### 3.7 🟡 自动化测试

| 项目 | 说明 |
|------|------|
| **问题** | `tests/` 为空；`scripts/test_*.py` 是手动脚本，不是 pytest 测试，无法做 CI |
| **方案** | 补充以下测试用例（pytest）: |

**核心测试清单：**

```
tests/
├── test_sql_safety.py        # sqlglot 安全校验：SELECT/DROP/DELETE/UPDATE/注入/子查询
├── test_schema_extractor.py  # Schema 提取：表名列表、字段信息、外键关系、DDL
├── test_retriever.py         # RAG 检索：相关表召回率、空结果处理
├── test_agent_loop.py        # Agent 循环：正常流程、max_turns 超限、工具异常
├── test_prompt.py            # Prompt 构建：Few-shot 注入、动态 Schema
└── test_api.py               # API 接口：正常请求、空消息、超时
```

### 3.8 🟡 配置管理优化 —— 模型名称硬编码 ✅ 已修复

| 项目 | 说明 |
|------|------|
| **问题** | `base_agent.py` 中 `self.model` 曾硬编码为 `"deepseek-chat"` |
| **方案** | **已实现**：Agent 构造函数中统一使用 `settings.model_name` (来自 `.env` 配置文件) |
| **效果** | 提供更好的模型灵活性，无需修改代码即可切换大模型 |

### 3.9 🟡 前端遗留文件清理 ✅ 已修复

| 项目 | 说明 |
|------|------|
| **现状** | **已完成**：无效的 `HelloWorld.vue` 组件已被移除。 |

### 3.10 🔵 类型标注完善 ✅ 已实现

| 项目 | 说明 |
|------|------|
| **状态** | **已实现**：核心模块 `base_agent.py`、`api_server.py` 及 `models/` 均已补充类型标注。 |
| **方案** | 补充 `-> str` 返回类型、`Dict[str, Callable]` 类型标注 |

### 3.11 🔵 API 接口增强

| 项目 | 说明 |
|------|------|
| **内容** | 增加请求超时、速率限制、请求体大小限制、API 版本号 |
| **方案** | FastAPI middleware + `slowapi` 限流 |

### 3.12 🔵 Docker 化部署

| 项目 | 说明 |
|------|------|
| **内容** | 提供 `Dockerfile` + `docker-compose.yml`，包含 MySQL + ChromaDB + Backend + Frontend 一键启动 |

### 3.13 🟡 一键部署脚本

| 项目 | 说明 |
|------|------|
| **问题** | 部署时需要手动分步执行 `setup_database.py` → `build_rag_index.py` → 启动服务，步骤分散易遗漏 |
| **方案** | 新建 `scripts/init_all.py` 或 `Makefile`，一键完成建库 + 导数据 + 构建 RAG 索引 + 启动服务 |

### 3.14 🟡 中文注释动态化（消除 `chinook_zh.py` 硬编码） ✅ 已实现

| 项目 | 说明 |
|------|------|
| **问题** | `data/chinook_zh.py` 是手动维护的映射，结构变更后维护成本高 |
| **方案** | **已实现**：`schema_extractor` 已优先读取 MySQL `COMMENT` 字段。建议逐步将生产环境元数据迁入 DB 中。 |

### 3.15 🔴 RAG 数据隔离与安全防护 (P0 优先级)

| 项目 | 说明 |
|------|------|
| **风险** | 敏感表（如 `users`）可能被 RAG 召回并由 Agent 查询 |
| **方案** | **强烈推荐方案 B**：为 Agent 创建专属只读用户，在 MySQL 侧通过权限控制（最小特权原则）隐藏管理表 |

### 3.16 🔵 全链路性能监控与分析

| 项目 | 说明 |
|------|------|
| **内容** | 增加对 Agent 各步骤耗时、Token 消耗、SQL 执行吞吐量的监控 |
| **方案** | 扩展 `config/logging.py` 输出结构化指标日志，或集成 Prometheus 指标采集 |

---

## 四、修改优先级排序（建议执行顺序）

### 第一批（P0 必须修复 —— 正确性与安全）

| 序号 | 修改项 | 涉及文件 | 工作量 |
|------|--------|----------|--------|
| 1 | 修复并发 bug：messages 改为局部变量 | `base_agent.py` | ⭐ |
| 2 | 修复事件循环阻塞 | `api_server.py` | ⭐ |
| 3 | 删除死代码 `db_tools.py` | `tools/db_tools.py` | ⭐ |
| 4 | 消除冗余工具调用分支 | `base_agent.py` | ⭐ |
| 5 | 修复 XSS 风险（v-html + DOMPurify） | `ChatMessage.vue` | ⭐ |
| 6 | 移除硬编码密码 | `settings.py` | ⭐ |
| 7 | 统一错误处理，不泄漏内部信息 | `base_agent.py`, `api_server.py` | ⭐⭐ |
| 8 | **RAG 安全防护：MySQL 权限控制** | 数据库侧配置 + `settings.py` | ⭐ |

### 第二批（P1 强烈建议 —— 可用性与健壮性）

| 序号 | 修改项 | 涉及文件 | 工作量 |
|------|--------|----------|--------|
| 8 | 统一 Engine 管理 | 新建 `config/database.py` | ⭐⭐ |
| 9 | SQL 自动注入 LIMIT | `core_functions.py` | ⭐⭐ |
| 10 | 补充 pytest 自动化测试 | 新建 `tests/` | ⭐⭐⭐ |
| 11 | 前端 API 地址环境变量化 | `ChatInterface.vue`, `vite.config.js` | ⭐ |
| 12 | 使用 settings 中的 model_name | `base_agent.py` | ⭐ |
| 13 | 日志规范化 | 新建 `config/logging.py` | ⭐⭐ |
| 14 | 多轮对话支持 | `base_agent.py`, `api_server.py` | ⭐⭐⭐ |
| 15 | RAG 中文 Embedding 模型替换 | `indexer.py`, `retriever.py` | ⭐⭐ |
| 16 | 删除 `HelloWorld.vue` | `frontend/` | ⭐ |

### 第三批（P2 锦上添花 —— 体验与性能）

| 序号 | 修改项 | 涉及文件 | 工作量 |
|------|--------|----------|--------|
| 17 | Agent 思考过程 SSE 流式推送 | 全链路 | ⭐⭐⭐⭐ |
| 18 | 查询缓存 | 新模块 | ⭐⭐⭐ |
| 19 | RAG Re-ranking | `retriever.py` | ⭐⭐⭐ |
| 20 | 类型标注完善 | 全局 | ⭐⭐ |
| 21 | API 限流/超时 | `api_server.py` | ⭐⭐ |
| 22 | Docker 化 | 新建 `Dockerfile`, `docker-compose.yml` | ⭐⭐⭐ |
| 23 | 全链路异步化 | 全局重构 | ⭐⭐⭐⭐⭐ |

---

## 五、架构选型反思与重构建议

> 以下内容是对当前 ReAct + RAG 架构选型的深度分析，回答三个核心问题：  
> 1. ReAct Agent 是不是 Text-to-SQL 的最佳模式？  
> 2. 把数据库 Schema 放进 RAG 是不是最优解？  
> 3. 当前架构能支撑多少张表？

### 5.1 ReAct Agent 在 Text-to-SQL 场景下的适用性

#### 当前 ReAct 的调用链路

每次用户提问，Agent 至少跑 **3-4 轮 LLM 调用**：

```
第1轮 LLM → "我需要调 list_tables_tool" → 返回表名
第2轮 LLM → "我需要调 get_schema_tool" → 返回 DDL
第3轮 LLM → "我需要调 execute_sql_tool" → 返回结果
第4轮 LLM → 生成自然语言回答
```

**核心浪费**：前两步（找表 + 拿 Schema）几乎每次都一样，LLM 的"决策"没有增加任何价值。它不会跳过这些步骤，也不会改变调用顺序。让 LLM 去"思考"要不要调这两个工具，本质上是在**花钱买一个确定的答案**。

#### Text-to-SQL 领域主流架构对比

| 架构模式 | 原理 | 适用场景 | LLM 调用次数 | 准确率 |
|----------|------|----------|:------------:|:------:|
| **Direct Prompting** | 全量 Schema 塞 Prompt，一次生成 SQL | < 20 张表 | 1 次 | 中等 |
| **确定性 Pipeline** ⭐推荐 | 硬编码流水线：RAG→Schema→LLM 生成 SQL→执行 | 20-500 张表 | 1-2 次 | 高 |
| **ReAct Agent（当前）** | LLM 自主决定调什么工具 | 工具不确定、需动态决策 | 3-5 次 | 中高 |
| **Plan-and-Execute** | 先生成执行计划，再逐步执行 | 极复杂的多步分析查询 | 5+ 次 | 高 |
| **Multi-Agent** | 多个 Agent 分工（选表、写 SQL、校验） | 企业级大规模 | 多个 Agent | 最高 |

#### 推荐方案：确定性 Pipeline + 错误重试时 LLM 推理

```
用户提问
  ↓
[确定性] RAG 召回 Top-5 表 → 批量获取 Schema → 拼装 Context
  ↓
[LLM 调用 1] 生成 SQL（带 Few-shot + Schema Context）
  ↓
[确定性] sqlglot 校验 → MySQL 执行 → 拿到结果
  ↓
[LLM 调用 2] 自然语言总结
  ↓
若 SQL 报错 → [LLM 调用 3] 修正 SQL → 重新执行（最多 2 次）
```

**收益**：
- LLM 调用从 4 次降到 **1-2 次**，延迟降低 ~60%，API 费用降低 ~60%
- 确定性步骤不会出错，整体可靠性更高
- 只在真正需要推理的地方（SQL 生成、错误修正）使用 LLM

> **ReAct 不是不好，而是在 Text-to-SQL 这个流程高度确定的场景下大材小用。** 如果未来要扩展到"LLM 自主决定是否跨库查询、是否生成图表、是否发邮件"等不确定场景，ReAct 才真正发挥价值。

---

### 5.2 RAG 索引策略分析

#### 当前做法

`indexer.py` 将每张表的信息拼成一段文本后做 Embedding，**一张表 = 一个向量文档**：

```
Table: Customer
Description: 客户信息表
Columns:
- CustomerId (PK)
- FirstName
- LastName
- Fax
...
DDL: CREATE TABLE Customer (...)
```

#### 存在的三个问题

| 问题 | 说明 | 影响 |
|------|------|------|
| **粒度太粗** | 50 个字段的语义被"平均"成一个向量，单字段语义被稀释 | 用户问"传真号"时，`Fax` 字段信号太弱，表可能排不进 Top-5 |
| **语义鸿沟** | 用户说"销售冠军"，索引里是 `Employee`、`SupportRepId` 英文标识符 | 跨语言 + 业务术语映射几乎不可能命中 |
| **DDL 噪音** | `ENGINE=InnoDB DEFAULT CHARSET=utf8mb4` 等技术元数据参与向量化 | 干扰语义匹配，降低检索精度 |

#### 更优的索引策略

| 优化方向 | 做法 | 预期效果 |
|----------|------|----------|
| **多粒度索引** | 同时索引"表级文档"和"字段级文档"，检索时先匹配字段再回溯到表 | 解决字段级查询召回问题 |
| **业务语义增强** | 索引文档加入场景描述（如"Employee：销售人员，用于统计业绩和客户管理"） | 解决业务术语→表名映射 |
| **混合检索** | 向量检索 + BM25 关键词检索混合 | 兼顾语义匹配和精确匹配（如表名/字段名） |
| **去除技术噪音** | DDL 不参与向量化，只用 表名+描述+字段名+字段注释 | 提升向量质量 |
| **中文 Embedding** | 切换 `bge-base-zh-v1.5` 或 `paraphrase-multilingual-MiniLM-L12-v2` | 提升中文语义理解能力 |

#### Schema 不一定非要用 RAG

| 替代方案 | 原理 | 适用场景 |
|----------|------|----------|
| **全量塞 Prompt** | 所有表名+字段列表直接写进 System Prompt | < 20 张表（如 Chinook 的 11 张表） |
| **元数据目录表** | MySQL 中建一张"表目录"，LLM 先查目录再取 Schema | 中等规模，避免向量库依赖 |
| **Schema Linking** | NLP 提取问题中的实体，规则/字典映射到表名和字段 | 高精度需求场景 |
| **LLM 自选表** | 把所有表名+一句话描述给 LLM，让它选 | < 50 张表，准确率可能比 RAG 更高 |

> **对当前 Chinook 数据集（11 张表）**：RAG 的引入更多是技术演示价值。直接把 11 张表的 Schema 塞进 Prompt（约 2000 Token），简单、可靠、零额外依赖。

---

### 5.3 当前架构的表规模承载能力

#### 各组件瓶颈分析

| 组件 | 容量限制 | 说明 |
|------|:--------:|------|
| **ChromaDB 存储** | ✅ 无瓶颈 | 轻松存储上万条向量 |
| **Embedding 检索质量** | ⚠️ ~200 张表开始劣化 | `all-MiniLM-L6-v2` 384 维轻量模型，表多后语义空间拥挤，相似表竞争 Top-K |
| **Top-K=5 覆盖率** | ⚠️ **核心瓶颈** | 200 张表时 Top-5 只覆盖 2.5%，相关表排在第 6-10 名时就漏了 |
| **LLM Context Window** | ⚠️ 间接瓶颈 | 5 表 × 15 列 × DDL ≈ 3000-5000 Token；Top-K 调到 15 则翻倍 |
| **索引构建时间** | ✅ 无瓶颈 | 一次性构建，200 张表秒级完成 |

#### 不同规模推荐策略

| 表数量 | 推荐方案 | 是否需要 RAG |
|:------:|----------|:------------:|
| **< 20** | 全量 Schema 塞 Prompt，LLM 自己选表 | ❌ 不需要 |
| **20-100** | 当前 RAG 方案基本可用，优化 Embedding 和索引文档质量 | ✅ 基础 RAG |
| **100-500** | 多粒度索引 + 混合检索 + Re-ranking + Top-K=10~15 + 更强 Embedding | ✅ 增强 RAG |
| **500-2000** | 层级检索：先按业务域/Schema 分类，再域内细粒度检索 | ✅ 层级 RAG |
| **2000+** | Schema Linking + 知识图谱 + 专门元数据管理系统 | 🔄 RAG 不够 |

---

### 5.4 分阶段重构路线图

#### 短期（当前迭代）—— 赋予 Agent 自主性决策

- [x] **废弃固定的 Pipeline**：不再通过 Prompt 强制限定先 RAG 再 Schema 的流程，将各种底层工具交由 LLM 自主决定何时调用
- [x] **增强 Tool Descriptions**：在工具的文档注释（docstring）中极度清晰地写明每种工具的使用场景、入参和能查到的数据边界，通过工具描述（而非系统提示词）来引导 LLM 的行为
- [x] **复杂查询的动态规划**：对于复杂的提问（多表多次分析），引导 Agent 先写出完整的分析计划，进而自主通过多轮 function calling 根据上一步结果动态调整下一步动作

#### 中期（下个版本）—— 检索增强

- [x] RAG 索引文档去除 DDL 噪音，增加业务语义描述
- [x] Embedding 模型切换为 `bge-base-zh-v1.5` 或多语言模型
- [x] 引入 BM25 + 向量混合检索
- [x] 支持多轮对话上下文

#### 长期（生产级演进）—— 规模化

- [ ] 多粒度索引（表级 + 字段级）
- [ ] Cross-Encoder Re-ranking
- [x] 全链路异步化 + SSE 流式推送
- [ ] 层级检索支持 500+ 表规模
- [ ] 查询缓存 + 成本监控

---

## 六、第三版本规划（用户系统 + 个性化）

> 第二版本完成多轮对话后，第三版本重点解决用户身份和个性化问题。

### 6.1 🟡 用户系统与持久化历史 ✅ 已实现

| 项目 | 说明 |
|------|------|
| **现状** | **已实现**：完成了基于 JWT 的注册/登录方案，并在后端实现了 Redis/MySQL 双层对话持久化及其查询 API。 |

### 6.2 🔵 用户画像与个性化推荐

| 项目 | 说明 |
|------|------|
| **内容** | 新建 `user_profiles` 表，统计用户高频查询的表和关键词；在 System Prompt 中注入用户偏好，或在 RAG 检索时对用户常用表加权 |
| **效果** | 系统越用越"懂"用户，销售人员自动优先匹配销售相关的表 |

### 6.3 🔵 用户反馈驱动的检索优化

| 项目 | 说明 |
|------|------|
| **内容** | 前端每条回答增加 👍/👎 反馈按钮；后端新建 `query_feedback` 表，记录问题、召回表名、反馈类型（正确/错误） |
| **机制** | 正确反馈 → 对应"问题→表"映射权重+1；错误反馈 → 权重-1 或删除映射 |
| **效果** | RAG 检索时结合反馈权重对结果重新排序，系统通过用户使用自动进化，召回准确率持续提升 |

### 6.4 🔵 多数据库 / 多数据源支持

| 项目 | 说明 |
|------|------|
| **架构调整** | 废弃全局唯一 `engine`，改为基于 `source_id` 的连接池缓存抽象（`dict` 或 `@lru_cache`）；新建 `data_sources` 表存储用户的连接配置（支持 PostgreSQL、SQL Server、Oracle 等） |
| **流程适配** | 前端允许用户选择当前对话使用的数据源；Agent 注入 `db_type` 变量到 Prompt 引导方言；`sqlglot` 校验时传入对应的方言 `read=db_type` |
| **优势** | 核心组件（SQLAlchemy Inspector 提取 Schema，sqlglot 校验跨方言 AST）天生解耦，支持无缝拓展 90% 的关系型数据库 |

### 6.5 🔵 前端思维链展示（动态折叠） ✅ 已实现

| 项目 | 说明 |
|------|------|
| **现状** | **已实现**：`ChatMessage.vue` 已支持动态解析 `<thought>`、`<plan>` 等标签并实时提供可折叠的思维展示。 |
