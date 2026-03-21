import os
import json
import pandas as pd
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

def run(question: str, query_result) -> dict:
    print("[Analyst Agent] Interpreting results...")

    if isinstance(query_result, pd.DataFrame):
        result_str = query_result.to_string(index=False)
    elif isinstance(query_result, pd.Series):
        result_str = query_result.to_string()
    else:
        result_str = str(query_result)

    prompt = f"""
You are a data analyst. Interpret the query result and provide a clear,
actionable insight for a non-technical audience.

QUESTION: {question}

QUERY RESULT:
{result_str}

Reply in this exact JSON format only, no extra text, no markdown fences:
{{
    "insight": "2-3 sentence plain English answer",
    "key_findings": ["finding 1", "finding 2", "finding 3"],
    "recommendation": "one actionable recommendation",
    "chart_suggestion": "bar / pie / line / scatter"
}}
"""

    response      = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    response_text = response.text.strip().replace('```json', '').replace('```', '').strip()
    analysis      = json.loads(response_text)

    print("[Analyst Agent] Done.")
    return analysis