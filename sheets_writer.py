import os
from datetime import datetime
from googleapiclient.discovery import build
from tools.sheets_loader import get_google_credentials
from dotenv import load_dotenv

load_dotenv()

SHEET_ID = os.getenv('SHEET_ID')

def ensure_header_row(service):
    result = service.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range="A1:K1"
    ).execute()

    if 'values' not in result:
        headers = [[
            'Timestamp', 'Date', 'From', 'Subject',
            'Intent', 'Urgency', 'Category', 'Sentiment',
            'Action Required', 'Action Description', 'Summary'
        ]]
        service.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range="A1",
            valueInputOption='RAW',
            body={'values': headers}
        ).execute()

def write_email_row(email: dict, extracted: dict):
    creds   = get_google_credentials()
    service = build('sheets', 'v4', credentials=creds)
    ensure_header_row(service)

    row = [[
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        email.get('date', ''),
        email.get('sender', ''),
        email.get('subject', ''),
        extracted.get('intent', ''),
        extracted.get('urgency', ''),
        extracted.get('category', ''),
        extracted.get('sentiment', ''),
        extracted.get('action_required', ''),
        extracted.get('action_description', ''),
        extracted.get('summary', '')
    ]]

    service.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range="A1",
        valueInputOption='RAW',
        insertDataOption='INSERT_ROWS',
        body={'values': row}
    ).execute()

    print(f"Logged: [{extracted.get('urgency','?').upper()}] {email['subject'][:50]}")