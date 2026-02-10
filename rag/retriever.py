import chromadb
from chromadb.utils import embedding_functions
from config.settings import get_settings
from loguru import logger

class SchemaRetriever:
    def __init__(self):
        settings = get_settings()
        self.client = chromadb.PersistentClient(path=settings.chroma_db_dir)
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name="schema_collection",
            embedding_function=self.embedding_fn
        )

    def retrieve_related_schemas(self, query: str, n_results: int = 5) -> list[str]:
        """
        Retrieve schema information relevant to the query.
        Returns a list of table names.
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            if results and results['ids']:
                # Results is a dictionary with lists, we take the first list (for the single query)
                return results['ids'][0]
            return []
        except Exception as e:
            logger.error(f"Error retrieving schemas: {e}")
            return []

retriever = SchemaRetriever()
