import os
import base64
from tools.sheets_loader import get_google_credentials
from googleapiclient.discovery import build

def get_unread_emails(max_results=10):
    creds   = get_google_credentials()
    service = build('gmail', 'v1', credentials=creds)

    results = service.users().messages().list(
        userId='me',
        labelIds=['INBOX', 'UNREAD'],
        maxResults=max_results
    ).execute()

    messages = results.get('messages', [])
    emails   = []

    for msg in messages:
        full_msg = service.users().messages().get(
            userId='me',
            id=msg['id'],
            format='full'
        ).execute()

        headers = full_msg['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender  = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
        date    = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
        body    = extract_body(full_msg['payload'])

        emails.append({
            'id'     : msg['id'],
            'subject': subject,
            'sender' : sender,
            'date'   : date,
            'body'   : body[:3000]
        })

        service.users().messages().modify(
            userId='me',
            id=msg['id'],
            body={'removeLabelIds': ['UNREAD']}
        ).execute()

    return emails

def extract_body(payload):
    body = ''
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data  = part['body'].get('data', '')
                body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            elif 'parts' in part:
                body += extract_body(part)
    else:
        data = payload['body'].get('data', '')
        if data:
            body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
    return body