import chromadb
from chromadb.utils import embedding_functions
from config.settings import get_settings
from rag.extractor import SchemaExtractor
from loguru import logger
import os

class SchemaIndexer:
    def __init__(self):
        settings = get_settings()
        # Ensure the directory exists
        os.makedirs(settings.chroma_db_dir, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=settings.chroma_db_dir)
        
        # Use default embedding function (all-MiniLM-L6-v2)
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        
        self.collection = self.client.get_or_create_collection(
            name="schema_collection",
            embedding_function=self.embedding_fn
        )
        self.extractor = SchemaExtractor()

    def index_schemas(self):
        """Extract schemas and index them into ChromaDB."""
        schemas = self.extractor.extract_all_schemas()
        
        ids = []
        documents = []
        metadatas = []

        for schema in schemas:
            table_name = schema.name
            # Create a rich text representation for embedding including descriptions
            text_rep = f"Table: {table_name}\n"
            if schema.description:
                text_rep += f"Description: {schema.description}\n"
            
            text_rep += "Columns:\n"
            for col in schema.columns:
                desc = f" ({col.description})" if col.description else ""
                text_rep += f"- {col.name}{desc}\n"

            if schema.ddl:
                text_rep += f"DDL: {schema.ddl}"
            
            ids.append(table_name)
            documents.append(text_rep)
            metadatas.append({"table_name": table_name})

        if ids:
            logger.info(f"Indexing {len(ids)} tables into ChromaDB...")
            self.collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            logger.info("Indexing complete.")
        else:
            logger.warning("No tables found to index.")

indexer = SchemaIndexer()
