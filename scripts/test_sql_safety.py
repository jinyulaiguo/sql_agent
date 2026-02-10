import sys
import os
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

from tools.core_functions import execute_sql_tool

def test_safety():
    print("--- Testing SQL Safety & Error Handling ---")

    # 1. Valid Query
    logger.info("Test 1: Valid SELECT")
    res = execute_sql_tool("SELECT * FROM Genre LIMIT 2")
    print(f"Result:\n{res}\n")

    # 2. Syntax Error
    logger.info("Test 2: Syntax Error")
    res = execute_sql_tool("SELECT * FROM Genre WHERE LIMIT 2") # Invalid SQL
    print(f"Result:\n{res}\n")

    # 3. Dangerous Query (DROP)
    logger.info("Test 3: DROP TABLE")
    res = execute_sql_tool("DROP TABLE Genre")
    print(f"Result:\n{res}\n")

    # 4. Dangerous Query (DELETE)
    logger.info("Test 4: DELETE FROM")
    res = execute_sql_tool("DELETE FROM Genre WHERE GenreId=1")
    print(f"Result:\n{res}\n")

    # 5. Non-SELECT (UPDATE)
    logger.info("Test 5: UPDATE")
    res = execute_sql_tool("UPDATE Genre SET Name='New Rock' WHERE GenreId=1")
    print(f"Result:\n{res}\n")

if __name__ == "__main__":
    test_safety()
