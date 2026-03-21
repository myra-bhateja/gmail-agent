import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

def extract_email_info(email: dict) -> dict:
    prompt = f"""
You are an email analysis assistant. Analyze the email below and extract key information.

EMAIL DETAILS:
From: {email['sender']}
Subject: {email['subject']}
Date: {email['date']}
Body: {email['body']}

Return ONLY valid JSON, no extra text, no markdown fences:
{{
    "intent": "one sentence describing what the sender wants",
    "urgency": "high / medium / low",
    "summary": "2-3 sentence summary",
    "action_required": "yes / no",
    "action_description": "what action is needed, or none",
    "category": "sales / support / meeting / newsletter / spam / personal / other",
    "sentiment": "positive / neutral / negative"
}}
"""

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )

    response_text = response.text.strip()
    response_text = response_text.replace('```json', '').replace('```', '').strip()

    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        return {
            "intent"            : "Could not extract",
            "urgency"           : "unknown",
            "summary"           : response_text[:200],
            "action_required"   : "unknown",
            "action_description": "none",
            "category"          : "other",
            "sentiment"         : "neutral"
        }