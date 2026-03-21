import os
import json
from google import genai
from dotenv import load_dotenv
from tools.db import get_schema_description, sync_from_sheets
from tools.sheets_loader import load_dataframe

load_dotenv()
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

def run(question: str) -> dict:
    print("[Loader Agent] Syncing data...")
    sync_from_sheets()

    schema = get_schema_description()
    df     = load_dataframe()

    if df.empty:
        return {'error': 'No data found. Run main.py first to populate data.'}

    prompt = f"""
You are a data loader agent. Assess whether the question can be answered
with the available database.

DATABASE SCHEMA:
{schema}

USER QUESTION:
{question}

Reply in this exact JSON format only, no extra text, no markdown fences:
{{
    "answerable": true,
    "reason": "one sentence",
    "relevant_columns": ["col1", "col2"],
    "data_note": "any data quality observations"
}}
"""

    response      = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    response_text = response.text.strip().replace('```json', '').replace('```', '').strip()
    assessment    = json.loads(response_text)

    print(f"[Loader Agent] Answerable: {assessment['answerable']} — {assessment['reason']}")
    return {'df': df, 'schema': schema, 'assessment': assessment}