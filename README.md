## DataSheetAI Project
A natural language to SQL pipeline that lets user query CSV file using plain English. Load a CSV, ask a question, and get back a SQL query with results

This project is themed around music and movies, and comes with two sample datasets in the data folder to get started:
- `spotify.csv` - Spotify music tracks with artist, popularity and genre
- `movie.csv` - Movie dataset with titles, genres, ratings and starring actor/actress

### System Overview
This project converts CSV files into a SQLite databse, uses an LLM to convert natural language questions into SQL queries, validates and executes those queries, and returns results via a CLI interface

<img width="1384" height="1424" alt="image" src="https://github.com/user-attachments/assets/6270adb1-f313-4fe5-b649-d8e992dbafe3" />

<sub>Generated with assistance from Claude AI</sub>

### Defined Modules
**1. Data Loader** (data_loader.py)

This module handles reading CSV files and loading them into SQLite

- `load_data(file_path)` - Reads a CSV into a pandas DataFrame
- `get_column_types(data)` - Infers SQLite column types (INTEGER, REAL, TEXT) from pandas dtypes
- `insert_data(data, db_path, table_name)` - Creates a table and inserts rows into SQLite
  
**2. Schema Manager** (schema_manager.py) 

This module manages table creation and checks schema before inserting data

- `infer_schema(df)` - Maps DataFrame dtypes to SQLite types
- `get_existing_table(db, table_name)` - Returns the existing schema for a table, or None if it doesn't exist
- `compare_schemas(existing, new)` - Returns "create", "append", or "conflict" based on schema comparison
- `create_table(db_path, table_name, schema)` - Creates a new table with an auto-incrementing id primary key
- `append_csv_to_table(db_path, table_name, df)` - Appends a DataFrame to an existing table
- `resolve_schema(db_path, table_name, new_schema)` - Check existing table and return the right action

    **Schema resolution logic**

    | Situation | Action |
    | -------- | -------- |
    | Table does not exist    | "create"     |
    | Table exists and schemas match    | "append"     |
    | Table exists but schemas doesn't match    | "conflict"     |


**3. LLM Interface** (llm_interface.py)

This module converts plain English questions into SQL using OpenAI's API

- `build_schema_context(schema_dict)` - Formats the DB schema into a readable string for the LLM
- `build_prompt(user_query, schema_dict)` - Constructs the full prompt for the LLM
- `call_llm(prompt)` - Calls the OpenAI API and returns sql and explanation
- `generate_sql(user_query, schema_dict)` - End-to-end function that builds prompt, calls LLM, returns sql and its explanation


**4. Query Service** (query_service.py)

This module validates and executes SQL queries against the SQLite database

- `list_tables(db_path)` - Lists all tables created by users
- `list_columns(db_path, table_name)` - Lists columns for a given table
- `validate_sql(db_path, sql)` - Checks that the SQL is a SELECT, references a real table, and uses real column names
- `execute_sql(db_path, sql)` - Validates then executes the SQL, returning a DataFrame or an error message
- `cli_loop(db_path)` - Interactive shell for ongoing queries after the initial run

**5. CLI Interface** (cli_service.py)

This module acts as the entry point that connects all modules together. It accepts a user question and a CSV path as command-line arguments, runs the full pipeline, prints the generated SQL and explanation, executes the query, and then drops into an interactive CLI loop.

### How to run the project

#### Prerequisite
Create a `.env` file in the modules folder with this line of code:
```
OPENAI_API_KEY = "your_key_here"
```
#### Basic Run
```
python modules/cli_service.py "<your question>" <path/to/your/file>.csv
```
#### Sample Run
```
python modules/cli_service.py "Give me top 5 songs by Taylor Swift" data/spotify.csv
```
#### Sample output:
```
Data loaded successfully into data/music_movie.db!
Table 'spotify_table' created successfully.
Schema Manager Done!
Generating SQL...

Generated SQL: SELECT track_name, track_artist, playlist_genre, track_popularity
FROM spotify_table
WHERE lower(track_artist) LIKE '%taylor swift%'
ORDER BY track_popularity DESC, track_name ASC
LIMIT 5;

Explanation: Selects the top 5 Taylor Swift tracks by descending track_popularity (case-insensitive match on track_artist) and returns their name, artist, genre, and popularity.

                        track_name  ... track_popularity
0    Fortnight (feat. Post Malone)  ...               84
1                            Lover  ...               84
2  I Can Do It With a Broken Heart  ...               83
3                         cardigan  ...               83
4                        Anti-Hero  ...               81

[5 rows x 4 columns]

Welcome to the SQLite Query Service!
Commands: list tables | list columns | load <csv_file_path> | query | exit
>>> list tables
Tables: ['spotify_table']
>>> list columns
Enter table name: spotify_table
Columns in spotify_table: ['id', 'track_name', 'track_artist', 'playlist_genre', 'track_popularity']
>>> load data/movie.csv
Data loaded successfully into data/music_movie.db!
Table 'movie_table' created successfully.
>>> list tables
Tables: ['spotify_table', 'movie_table']
>>> list columns
Enter table name: movie_table
Columns in movie_table: ['id', 'name', 'genre', 'score', 'star']
>>> query
Enter SQL (or type 'back' to return): SELECT name, score FROM movie_table WHERE lower(star) LIKE '%emma stone%' ORDER by score DESC LIMIT 5
                  name  score
0             The Help    8.0
1               Easy A    7.0
2  Battle of the Sexes    6.7
3             Movie 43    4.3
```
This will:

1. Load the CSV into `data/music_movie.db`
2. Create or validate the table schema
3. Generate a SQL query from your question
4. Print the SQL and a plain-English explanation
5. Execute the query and print the results
6. Drop into an interactive CLI for further queries

**Interactive CLI commands** (after the initial query runs):

| Command | Description |
| -------| ---------|
|list tables | Show all tables in the database|
|list columns |Show columns for a specific table|
|load <csv_path> |Load a new CSV file into the database|
|query | Enter a custom SQL query|
|exit |Exit the CLI|

> **Note:** The table name is derived from your CSV filename. For example, spotify.csv becomes spotify_table in the database.
   
### How to run tests
Tests use Python's built-in unittest framework and are located in the unit_tests/ directory.
#### Run all tests:
```
python -m pytest unit_tests/
```
#### Run a specific test file:
```
python -m unittest unit_tests/test_data_loader.py
python -m unittest unit_tests/test_schema_manager.py
python -m unittest unit_tests/test_query_service.py
python -m unittest unit_tests/test_llm_interface.py
```

#### What each test covers:
| Test File | What It Tests |
| -------| ---------|
| `test_data_loader.py` | CSV loading, dtype-to-SQLite type mapping, row insertion | 
| `test_schema_manager.py` | Schema creation, matching, conflict detection | 
| `test_query_service.py` | Table/column listing, SQL validation rules, query execution | 
| `test_llm_interface.py` | Prompt building, JSON parsing, LLM call mocking|
