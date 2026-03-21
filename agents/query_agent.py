import os
from google import genai
from dotenv import load_dotenv
from tools.sql_executor import execute_sql
from tools.db import get_schema_description

load_dotenv()
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

MAX_RETRIES = 3

def run(question: str, df=None, schema: str = None) -> dict:
    db_schema     = get_schema_description()
    error_context = ""
    sql           = ""

    for attempt in range(1, MAX_RETRIES + 1):
        print(f"[Query Agent] Attempt {attempt}/{MAX_RETRIES}...")

        prompt = f"""
You are a SQL agent working with a SQLite database.
Write a single SELECT query to answer the question.

DATABASE SCHEMA:
{db_schema}

USER QUESTION:
{question}

{f"PREVIOUS ERROR — fix this: {error_context}" if error_context else ""}

Rules:
- Single valid SQLite SELECT statement only
- Use only column names from the schema above
- No markdown fences, no explanation — raw SQL only

Example:
SELECT urgency, COUNT(*) as count FROM emails GROUP BY urgency ORDER BY count DESC
"""

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        sql = response.text.strip().replace('```sql', '').replace('```', '').strip()

        execution = execute_sql(sql)

        if execution['success']:
            print(f"[Query Agent] Success. SQL: {sql}")
            return {
                'sql'    : sql,
                'code'   : sql,
                'result' : execution['result'],
                'success': True
            }
        else:
            error_context = execution['error']
            print(f"[Query Agent] Failed: {error_context[:100]}")

    return {
        'sql'    : sql,
        'code'   : sql,
        'result' : None,
        'success': False,
        'error'  : error_context
    }