import unittest
import sqlite3
import pandas as pd
from io import StringIO

from modules.query_service import list_tables, list_columns, validate_sql, execute_sql
# from modules.data_loader import load_data, get_column_types, insert_data
from modules.schema_manager import create_table, infer_schema, resolve_schema, append_csv_to_table

class TestCLIModule(unittest.TestCase):

    def setUp(self):
        # Use an in-memory database so we don’t write files
        self.db = ":memory:"

        # Sample CSV content
        csv_content = """track_name,track_artist,track_popularity
        Easy On Me,Adele,pop,77
        cardigan,Taylor Swift,83
        SPOT!,"ZICO, JENNIE",k-pop,78
        Espresso,Sabrina Carpenter,pop,90
        """
        self.df = pd.read_csv(StringIO(csv_content))
        self.table_name = "spotify_table"

        # Create the table
        create_table(self.db, self.table_name, infer_schema(self.df))
        append_csv_to_table(self.db, self.table_name, self.df)

    def test_list_tables_and_columns(self):
        tables = list_tables(self.db)
        self.assertIn(self.table_name, tables)

        columns = list_columns(self.db, self.table_name)
        self.assertIn("track_name", columns)
        self.assertIn("track_artist", columns)
        self.assertIn("track_popularity", columns)

    def test_validate_sql(self):
        # Valid query
        sql = "SELECT track_name FROM spotify_table"
        valid, msg = validate_sql(self.db, sql)
        self.assertTrue(valid)
        self.assertIsNone(msg)

        # Invalid query (unknown table)
        sql_invalid = "SELECT * FROM unknown_table"
        valid, msg = validate_sql(self.db, sql_invalid)
        self.assertFalse(valid)
        self.assertIn("No valid table names", msg)

        # Invalid query (not SELECT)
        sql_invalid2 = "DROP TABLE spotify_data"
        valid, msg = validate_sql(self.db, sql_invalid2)
        self.assertFalse(valid)
        self.assertIn("Only SELECT", msg)
        
        # Invalid query (unknown column)
        sql_invalid3 = "SELECT track_url FROM spotify_table"
        valid, msg = validate_sql(self.db, sql_invalid3)
        self.assertFalse(valid)
        self.assertIn("Unknown column", msg)

    def test_execute_sql(self):
        sql = "SELECT track_name, track_popularity FROM spotify_data ORDER BY track_popularity DESC"
        df, err = execute_sql(self.db, sql)
        self.assertIsNone(err)
        self.assertEqual(len(df), 4)
        self.assertEqual(df.iloc[0]["track_name"], "Lover")  # highest popularity

        # Invalid SQL should return error
        sql_invalid = "SELECT * FROM unknown_table"
        df, err = execute_sql(self.db, sql_invalid)
        self.assertIsNotNone(err)
        self.assertIsNone(df)
        
        # Invalid column should return error
        sql_invalid2 = "SELECT track_url FROM spotify_table"
        df, err = execute_sql(self.db, sql_invalid2)
        self.assertIsNotNone(err)
        self.assertIsNone(df)

    def test_resolve_schema(self):
        # Matching schema should return "append"
        new_schema = infer_schema(self.df)
        action = resolve_schema(self.db, self.table_name, new_schema)
        self.assertEqual(action, "append")

        # Conflicting schema
        conflict_schema = {"track_name": "TEXT", "track_artist": "TEXT", "track_popularity": "REAL"}
        action = resolve_schema(self.db, self.table_name, conflict_schema)
        self.assertEqual(action, "conflict")

        # New table
        action_new = resolve_schema(self.db, "new_table", new_schema)
        self.assertEqual(action_new, "create")


if __name__ == "__main__":
    unittest.main()
