"""RAG 语义检索模块

基于 ChromaDB 向量数据库，通过 Embedding 相似度检索与用户问题相关的表。
"""

import chromadb
from chromadb.utils import embedding_functions
from config.settings import get_settings
from loguru import logger
from rank_bm25 import BM25Okapi
import jieba
import re


class SchemaRetriever:
    """Schema 混合检索器 (Vector + BM25)"""

    def __init__(self):
        settings = get_settings()
        self.client = chromadb.PersistentClient(path=settings.chroma_db_dir)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="BAAI/bge-base-zh-v1.5"
        )
        self.collection = self.client.get_or_create_collection(
            name="schema_collection",
            embedding_function=self.embedding_fn,
        )
        # 初始化 BM25 相关属性
        self.bm25 = None
        self.all_ids = []
        self.all_documents = []
        self._init_bm25()

    def _init_bm25(self):
        """从 ChromaDB 加载所有文档并初始化 BM25 索引"""
        try:
            # 获取所有存储的文档和 ID
            all_data = self.collection.get()
            if not all_data or not all_data["documents"]:
                logger.warning("ChromaDB 为空，跳过 BM25 初始化")
                return

            self.all_ids = all_data["ids"]
            self.all_documents = all_data["documents"]

            # 对所有文档进行分词
            tokenized_corpus = [self._tokenize(doc) for doc in self.all_documents]
            self.bm25 = BM25Okapi(tokenized_corpus)
            logger.info(f"BM25 索引初始化完成，包含 {len(self.all_ids)} 个文档")
        except Exception as e:
            logger.error(f"BM25 初始化失败: {e}")

    def _tokenize(self, text: str) -> list[str]:
        """针对数据库 Schema 的分词策略"""
        # 1. 处理驼峰命名和下划线命名 (e.g., CustomerId -> Customer Id, user_id -> user id)
        text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
        text = text.replace("_", " ")
        # 2. 结合 jieba 分词（适应中文注释）
        words = jieba.lcut(text.lower())
        # 3. 过滤掉无用字符和单字符（防止噪音）
        return [w for w in words if w.strip() and len(w) > 1]

    def retrieve_related_schemas(self, query: str, n_results: int = 5) -> list[str]:
        """
        混合检索：Vector + BM25，使用 RRF (Reciprocal Rank Fusion) 融合。

        Args:
            query: 用户的自然语言查询
            n_results: 返回最终结果的数量

        Returns:
            list[str]: 相关表名列表
        """
        try:
            # 1. 向量检索 (Vector Search)
            # 取多一点结果用于后续融合，防止 Top-K 溢出
            vector_res = self.collection.query(
                query_texts=[query],
                n_results=min(n_results * 2, 20),
            )
            vector_ids = vector_res["ids"][0] if vector_res and vector_res["ids"] else []

            # 2. 关键词检索 (BM25)
            bm25_ids = []
            if self.bm25:
                tokenized_query = self._tokenize(query)
                scores = self.bm25.get_scores(tokenized_query)
                # 获取排名前列的索引
                top_n_indices = sorted(
                    range(len(scores)), key=lambda i: scores[i], reverse=True
                )[: min(n_results * 2, 20)]
                # 只保留得分大于 0 的
                bm25_ids = [self.all_ids[i] for i in top_n_indices if scores[i] > 0]

            # 3. RRF 融合 (Reciprocal Rank Fusion)
            # RRF Score = sum(1 / (k + rank + 1))
            rrf_map = {}
            k = 60  # RRF 论文推荐的标准参数

            # 计算向量检索的排名得分
            for rank, table_id in enumerate(vector_ids):
                rrf_map[table_id] = rrf_map.get(table_id, 0) + 1.0 / (k + rank + 1)

            # 计算 BM25 检索的排名得分
            for rank, table_id in enumerate(bm25_ids):
                rrf_map[table_id] = rrf_map.get(table_id, 0) + 1.0 / (k + rank + 1)

            # 如果没有任何召回结果，返回空
            if not rrf_map:
                return []

            # 按融合得分从高到低排序，取前 n_results 个
            sorted_results = sorted(rrf_map.items(), key=lambda x: x[1], reverse=True)
            final_ids = [x[0] for x in sorted_results[:n_results]]

            logger.info(f"RAG 混合检索命中 (Vector={len(vector_ids)}, BM25={len(bm25_ids)}) -> Final: {final_ids}")
            return final_ids

        except Exception as e:
            logger.error(f"RAG 混合检索错误: {e}")
            # 出错时降级回原始检索结果（如果存在）或空
            return vector_ids[:n_results] if "vector_ids" in locals() else []


retriever = SchemaRetriever()
