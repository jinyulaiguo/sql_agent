import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Set up paths and load .env from day10 directory
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) # day10
load_dotenv(os.path.join(project_root, ".env"))

def drop_database():
    host = os.getenv("MYSQL_HOST")
    port = os.getenv("MYSQL_PORT")
    user = os.getenv("MYSQL_USER")
    password = os.getenv("MYSQL_PASSWORD")
    dbname = os.getenv("MYSQL_DB")
    
    connection_string = f"mysql+pymysql://{user}:{password}@{host}:{port}"
    engine = create_engine(connection_string)
    
    try:
        with engine.connect() as conn:
            print(f"Connected to MySQL at {host}:{port}")
            print(f"Dropping database '{dbname}' if exists...")
            conn.execute(text(f"DROP DATABASE IF EXISTS {dbname}"))
            print("Database dropped.")
            
    except Exception as e:
        print(f"Error dropping database: {e}")

if __name__ == "__main__":
    drop_database()
