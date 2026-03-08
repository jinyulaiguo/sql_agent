import sys
import os
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_retrieval():
    try:
        from rag.retriever import retriever
        
        test_queries = [
            "查询所有的客户",
            "Show me all albums by AC/DC",
            "谁是销售冠军？",
            "统计每种流派的歌曲数量"
        ]
        
        for query in test_queries:
            print(f"\nQuery: {query}")
            results = retriever.retrieve_related_schemas(query, n_results=3)
            print(f"Related Tables: {results}")
            
    except Exception as e:
        logger.error(f"Failed to test retrieval: {e}")
        raise

if __name__ == "__main__":
    test_retrieval()
