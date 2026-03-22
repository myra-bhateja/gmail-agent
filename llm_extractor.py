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
    
def generate_reply(email: dict, extracted: dict) -> str:
    prompt = f"""
You are a professional email assistant. Write a concise, polite reply
to the email below. Keep it under 100 words. Do not use placeholders
like [Your Name] — just write the body of the reply.

EMAIL DETAILS:
From: {email.get('sender', '')}
Subject: {email.get('subject', '')}
Body: {email.get('body', '')[:1000]}

CONTEXT:
Category: {extracted.get('category', '')}
Urgency: {extracted.get('urgency', '')}
Action required: {extracted.get('action_required', '')}
Action description: {extracted.get('action_description', '')}
Sentiment: {extracted.get('sentiment', '')}

Write only the reply body. No subject line, no greeting header,
no sign-off name. Start directly with the reply content.
"""

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    return response.text.strip()