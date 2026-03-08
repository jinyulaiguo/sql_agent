
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Set up paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) # day10
sys.path.append(project_root)

# Load env
load_dotenv(os.path.join(project_root, ".env"))

def check_data():
    host = os.getenv("MYSQL_HOST")
    port = os.getenv("MYSQL_PORT")
    user = os.getenv("MYSQL_USER")
    password = os.getenv("MYSQL_PASSWORD")
    dbname = os.getenv("MYSQL_DB")

    connection_string = f"mysql+pymysql://{user}:{password}@{host}:{port}/{dbname}"
    engine = create_engine(connection_string)

    tables_to_check = ["Artist", "Album", "MediaType", "Genre", "Track", "Customer", "Invoice"]

    try:
        with engine.connect() as conn:
            print(f"Checking database: {dbname}")
            for table in tables_to_check:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    print(f"Table '{table}': {count} rows")
                except Exception as e:
                    print(f"Table '{table}': Error - {e}")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    check_data()
