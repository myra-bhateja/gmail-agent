import os
import pandas as pd
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

SHEET_ID   = os.getenv('SHEET_ID')
SHEET_NAME = 'Email Agent Log'

def get_google_credentials():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    SCOPES = [
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/spreadsheets'
    ]

    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds

def load_dataframe() -> pd.DataFrame:
    creds   = get_google_credentials()
    service = build('sheets', 'v4', credentials=creds)

    result = service.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range="A1:K1000"
    ).execute()

    rows = result.get('values', [])
    if len(rows) < 2:
        return pd.DataFrame()

    headers = rows[0]
    data    = [row + [''] * (len(headers) - len(row)) for row in rows[1:]]
    df      = pd.DataFrame(data, columns=headers)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    return df

def get_schema_description(df: pd.DataFrame) -> str:
    lines = [f"The dataset has {len(df)} rows and {len(df.columns)} columns.\n"]
    lines.append("Columns:")
    for col in df.columns:
        sample_vals = df[col].dropna().unique()[:5].tolist()
        lines.append(f"  - '{col}': sample values: {sample_vals}")
    return '\n'.join(lines)