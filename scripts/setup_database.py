
import sys
import os
import requests
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Set up paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) # day10
sys.path.append(project_root)

# Load env
load_dotenv(os.path.join(project_root, ".env"))

def download_chinook_sql():
    url = "https://raw.githubusercontent.com/lerocha/chinook-database/master/ChinookDatabase/DataSources/Chinook_MySql.sql"
    output_path = os.path.join(project_root, "data", "chinook_mysql.sql")
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print(f"Downloading Chinook SQL from {url}...")
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(output_path, "wb") as f:
            f.write(response.content)
        print("Download successful.")
        return output_path
    except Exception as e:
        print(f"Failed to download: {e}")
        return None

def setup_database():
    host = os.getenv("MYSQL_HOST")
    port = os.getenv("MYSQL_PORT")
    user = os.getenv("MYSQL_USER")
    password = os.getenv("MYSQL_PASSWORD")
    dbname = os.getenv("MYSQL_DB")
    
    if not password or password == "your_password":
        print("Error: Please set a valid MYSQL_PASSWORD in .env")
        return

    connection_string = f"mysql+pymysql://{user}:{password}@{host}:{port}"
    engine = create_engine(connection_string)
    
    try:
        with engine.connect() as conn:
            print(f"Connected to MySQL at {host}:{port}")
            # Create DB if not exists
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {dbname}"))
            print(f"Database '{dbname}' ensured exists.")
            
            # Switch to DB
            conn.execute(text(f"USE {dbname}"))
            
            # Check for tables
            result = conn.execute(text("SHOW TABLES"))
            tables = result.fetchall()
            if tables:
                print(f"Tables already exist: {[t[0] for t in tables]}")
                return

            print("Importing Chinook data...")
            sql_path = download_chinook_sql()
            if not sql_path:
                return
            
            # Read and execute SQL file
            with open(sql_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Fix unsupported N' syntax (SQL Server style) for MySQL
            content = content.replace(", N'", ", '").replace("(N'", "('")
            
            # Helper to split SQL statements more robustly
            # We split by ';\n' which covers most standard SQL dumps where statements end with a newline
            # This avoids breaking on semicolons inside strings (e.g. 'Artist Name; Other Info')
            statements = content.split(';\n')
            
            for stmt in statements:
                stmt_stripped = stmt.strip()
                if not stmt_stripped:
                    continue
                    
                # Skip database creation/switching commands causing permission errors
                # Handle backticks and case sensitivity
                stmt_upper = stmt_stripped.upper()
                if "DROP DATABASE" in stmt_upper or "CREATE DATABASE" in stmt_upper or stmt_upper.startswith("USE"):
                    print(f"Skipping administrative statement: {stmt_stripped[:50]}...")
                    continue
                    
                try:
                    conn.execute(text(stmt))
                except Exception as e:
                    print(f"Error executing statement: {e}")
                    print(f"Failed SQL (snippet): {stmt[:200]}")
                    raise e # Stop on error
            
            conn.commit()
            print("Import completed.")
            
    except Exception as e:
        print(f"Database configuration or connection error: {e}")

if __name__ == "__main__":
    setup_database()
