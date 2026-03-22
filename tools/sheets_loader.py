import os
import pandas as pd
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

SHEET_ID   = os.getenv('SHEET_ID')
SHEET_NAME = 'Email Agent Log'

def get_google_credentials():
    import json
    import tempfile
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    SCOPES = [
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/spreadsheets'
    ]

    creds = None

    # Try token from environment variable first (Render)
    token_env = os.getenv('GOOGLE_TOKEN')
    if token_env:
        try:
            creds = Credentials.from_authorized_user_info(
                json.loads(token_env), SCOPES
            )
        except Exception as e:
            print(f"Could not load token from env: {e}")

    # Try token from local file (local dev)
    if not creds and os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # Refresh if expired
    if creds and not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                print("Token refreshed successfully.")
            except Exception as e:
                print(f"Token refresh failed: {e}")
                creds = None

    # If still no valid creds — this only works locally
    if not creds or not creds.valid:
        creds_env = os.getenv('GOOGLE_CREDENTIALS')
        if creds_env:
            try:
                with tempfile.NamedTemporaryFile(
                    mode='w', suffix='.json', delete=False
                ) as f:
                    f.write(creds_env)
                    temp_path = f.name
                flow = InstalledAppFlow.from_client_secrets_file(
                    temp_path, SCOPES
                )
                os.unlink(temp_path)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                raise Exception(f"Could not create credentials from env: {e}")
        elif os.path.exists('credentials.json'):
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES
            )
            creds = flow.run_local_server(port=0)
        else:
            raise Exception(
                "No credentials available. "
                "Set GOOGLE_TOKEN and GOOGLE_CREDENTIALS on Render."
            )

    # Save locally if possible
    try:
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    except Exception:
        pass

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