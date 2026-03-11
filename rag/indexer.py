"""RAG 向量索引构建模块

将数据库 Schema 信息提取、文本化后，通过 Embedding 模型存入 ChromaDB。
"""

import os
import chromadb
from chromadb.utils import embedding_functions
from config.settings import get_settings
from db.schema_extractor import SchemaExtractor
from loguru import logger


class SchemaIndexer:
    """Schema 向量索引构建器"""

    def __init__(self):
        settings = get_settings()
        os.makedirs(settings.chroma_db_dir, exist_ok=True)

        self.client = chromadb.PersistentClient(path=settings.chroma_db_dir)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="BAAI/bge-base-zh-v1.5"
        )
        self.collection = self.client.get_or_create_collection(
            name="schema_collection",
            embedding_function=self.embedding_fn,
        )
        self.extractor = SchemaExtractor()

    def index_schemas(self):
        """提取所有表的 Schema 并索引到 ChromaDB"""
        schemas = self.extractor.extract_all_schemas()

        ids = []
        documents = []
        metadatas = []

        for schema in schemas:
            table_name = schema.name
            # 构建用于 Embedding 的富文本（不含 DDL 技术噪音）
            text_rep = f"Table: {table_name}\n"
            if schema.description:
                text_rep += f"Description: {schema.description}\n"

            text_rep += "Columns:\n"
            for col in schema.columns:
                desc = f" ({col.description})" if col.description else ""
                text_rep += f"- {col.name}{desc}\n"

            ids.append(table_name)
            documents.append(text_rep)
            metadatas.append({"table_name": table_name})

        if ids:
            logger.info(f"正在将 {len(ids)} 张表索引到 ChromaDB...")
            self.collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )
            logger.info("索引构建完成。")
        else:
            logger.warning("未找到可索引的表。")


indexer = SchemaIndexer()
