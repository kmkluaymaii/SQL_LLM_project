from dotenv import load_dotenv
from openai import OpenAI
import os
import json

# Draw api key from .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Convert schema into a readable string for the LLM
def build_schema_context(schema_dict):
    schema_str = ""
    for table, cols in schema_dict.items():
        col_str = ", ".join([f"{col} ({dtype})" for col, dtype in cols.items()])
        schema_str += f"- {table} ({col_str})\n"
    return schema_str

# Create the prompt for the LLM
def build_prompt(user_query, schema_dict):
    schema_context = build_schema_context(schema_dict)
    prompt = f"""You are an AI assistant tasked with converting user queries into SQL statements. 
    The database uses SQLite and contains the following table: {schema_context} 
    Your task is to: 
      1. Generate a SQL query that accurately answers the user's question. 
      2. Ensure the SQL is compatible with SQLite syntax. 
      3. Provide a short comment explaining what the query does. 
    Output Format: - SQL Query - Explanation
    Here is the user question: "{user_query}"
    """
    return prompt

# Call the LLM and enforce JSON output
def call_llm(prompt):
    """Call OpenAI model and enforce JSON output."""
    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You convert natural language to SQL. "
                        "Always respond ONLY in valid JSON with keys: sql and explanation. "
                        "Do not include markdown, backticks, or extra text."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=1
        )

        output = response.choices[0].message.content.strip()

        # ---- Parse JSON safely ----
        try:
            parsed = json.loads(output)
            sql = parsed.get("sql", "").strip()
            explanation = parsed.get("explanation", "").strip()
        except json.JSONDecodeError:
            return {
                "sql": "",
                "explanation": f"Failed to parse JSON. Raw output:\n{output}"
            }

        return {
            "sql": sql,
            "explanation": explanation
        }

    except Exception as e:
        return {
            "sql": "",
            "explanation": f"LLM error: {str(e)}"
        }


def generate_sql(user_query, schema_dict):
    prompt = build_prompt(user_query, schema_dict)
    response = call_llm(prompt)
    return response["sql"], response["explanation"]

if __name__ == "__main__":
    schema_dict = {
        "spotify_data": {
            "track_name": "TEXT",
            "track_artist": "TEXT",
            "playlist_genre": "TEXT",
            "track_popularity": "INTEGER"
        }
    }

    user_query = "What are the top 5 most popular songs by Taylor Swift?"

    print("Generating SQL...")

    sql, explanation = generate_sql(user_query, schema_dict)

    # Ensure response is received before printing
    if sql:
        print("\n--- Generated SQL ---")
        print(sql)
    else:
        print("\nNo SQL generated.")

    if explanation:
        print("\n--- Explanation ---")
        print(explanation)
    else:
        print("\nNo explanation provided.")