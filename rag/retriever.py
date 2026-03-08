"""RAG 语义检索模块

基于 ChromaDB 向量数据库，通过 Embedding 相似度检索与用户问题相关的表。
"""

import chromadb
from chromadb.utils import embedding_functions
from config.settings import get_settings
from loguru import logger


class SchemaRetriever:
    """Schema 语义检索器"""

    def __init__(self):
        settings = get_settings()
        self.client = chromadb.PersistentClient(path=settings.chroma_db_dir)
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name="schema_collection",
            embedding_function=self.embedding_fn,
        )

    def retrieve_related_schemas(
        self, query: str, n_results: int = 5
    ) -> list[str]:
        """
        根据用户问题检索相关表名。

        Args:
            query: 用户的自然语言查询
            n_results: 返回的最大结果数

        Returns:
            list[str]: 相关表名列表
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
            )

            if results and results["ids"]:
                return results["ids"][0]
            return []
        except Exception as e:
            logger.error(f"RAG 检索错误: {e}")
            return []


retriever = SchemaRetriever()
