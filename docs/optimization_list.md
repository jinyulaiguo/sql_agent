# Text-to-SQL Agent 优化清单 (Optimization List)

## 1. RAG 检索优化 (Retrieval)
- [ ] **语义增强**: "销售冠军" 等业务术语无法召回 `Employee` 表。
    - *方案*: 在 `config/chinook_zh.py` 中为 `Employee` 表增加业务场景描述（如："包含销售人员信息，负责处理客户支持和发票"）。
- [ ] **多语言模型**: 当前使用 `all-MiniLM-L6-v2` (主要针对英文)。
    - *方案*: 切换到 `paraphrase-multilingual-MiniLM-L12-v2` 以获得更好的中文理解能力。
- [ ] **重排序 (Re-ranking)**: 检索回来的 Top-K 结果排序可能不精准。
    - *方案*: 引入 Cross-Encoder 模型对检索结果进行二次排序。

## 2. SQL 生成优化 (Generation)
- [ ] **Few-shot Learning**: 复杂查询（如多表 JOIN）可能生成错误。
    - *方案*: 构建一个 `examples.json`，存储 "问题-SQL" 对，在 Prompt 中动态插入相似示例。
- [ ] **Self-Correction**: 生成的 SQL 可能语法错误。
    - *方案*: 捕获 SQL 执行错误，将错误信息回传给 LLM 进行自我修正。

## 3. 体验优化 (UX)
- [ ] **流式输出**: SQL 生成和解释过程较长。
    - *方案*: 实现流式 API，让用户实时通过 WebSocket 看到思考过程。
