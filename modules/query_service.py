import sqlite3
import pandas as pd

from modules.data_loader import load_data
from modules.schema_manager import append_csv_to_table, get_existing_table, create_table, resolve_schema, infer_schema

# List all tables in the database.
def list_tables(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [
        row[0] for row in cursor.fetchall()
        if not row[0].startswith("sqlite_") 
    ]
    conn.close()
    return tables

# List all columns in a specific table.
def list_columns(db_path, table_name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = [row[1] for row in cursor.fetchall()]
    conn.close()
    return columns

# Step 1: Validate SQL without executing destructive commands,
# returns True if valid SELECT or harmless query, false otherwise.

def validate_sql(db_path, sql):
    sql_lower = sql.strip().lower()
    if not sql_lower.startswith("select") and not sql_lower.startswith("pragma"):
        return False, "Only SELECT or PRAGMA statements are allowed in validation."
    tables = list_tables(db_path)
    valid_table_found = False
    for table in tables:
        if table.lower() in sql_lower:
            valid_table_found = True
            if '*' not in sql_lower:
                columns = list_columns(db_path, table)
                valid_column_found = any(col.lower() in sql_lower for col in columns)
                if not valid_column_found:
                    return False, f"No valid column names found in table '{table}'."
            break
    if not valid_table_found:
        return False, "No valid table names found in SQL query."

    return True, None
       
# Step 2: Execute validated SQL and return results as DataFrame
def execute_sql(db_path, sql):
    valid, msg = validate_sql(db_path, sql)
    if not valid:
        return None, f"Validation failed: {msg}"
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(sql, conn)
        conn.close()
        return df, None
    except Exception as e:
        return None, str(e)
    
import sqlite3
DB_PATH = "data/spotify.db"

# Interactive CLI for querying the database
def cli_loop(db_path):
    print("Welcome to the SQLite Query Service!")
    print("Commands: list tables | list columns | load <csv_file_path> | query | exit\n")

    while True:
        cmd = input(">>> ").strip()
        if cmd == "exit":
            break

        elif cmd == "list tables":
            print("Tables:", list_tables(db_path))
            
            
        elif cmd == "list columns":
            table_name = input("Enter table name: ").strip()
            print(f"Columns in {table_name}:", list_columns(db_path, table_name))

        elif cmd.startswith("query"):
            while True:
                sql = input("Enter SQL (or type 'back' to return): ").strip()
                if sql.lower() == "back":
                    break
                df, err = execute_sql(db_path, sql)
                if err:
                    print(err)
                else:
                    print(df)
                    break
                
        elif cmd.startswith("load"):
            cmd_parts = cmd.split()
            new_csv_path = cmd_parts[1]
            data = load_data(new_csv_path)
            table_name = f"{new_csv_path.split('/')[-1].split('.')[0]}_table"
            print(f"Data loaded successfully into {db_path}!")
            
            existing_table = get_existing_table(db_path, table_name)
            new_schema = infer_schema(data)
            action = resolve_schema(db_path, table_name, new_schema)
            if action == "create":
                create_table(db_path, table_name, new_schema)
                append_csv_to_table(db_path, table_name, data)
                print(f"Table '{table_name}' created successfully.")

            elif action == "append":
                print("Schema matches. Skipping insert to avoid duplicates.")
            
            elif action == "conflict":
                print(f"Schema conflict detected for table '{table_name}'!")


        else:
            print("Unknown command. Try commands: list tables | list columns | load <csv> | query | exit")

# if __name__ == "__main__":
#     db_path = "data/spotify.db"
#     sql = "SELECT track_name, track_popularity FROM spotify_data ORDER BY track_popularity DESC;"
#     df, err = execute_sql(db_path, sql)
#     if err:
#         print(err)
#     else:
#         print(df)
#     cli_loop(sql)