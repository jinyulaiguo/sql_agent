import sys
import os
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def build_index():
    try:
        from rag.indexer import indexer
        logger.info("Starting schema indexing...")
        indexer.index_schemas()
        logger.info("Schema indexing finished successfully.")
    except Exception as e:
        logger.error(f"Failed to build index: {e}")
        raise

if __name__ == "__main__":
    build_index()
