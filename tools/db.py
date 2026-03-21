import os
import sqlite3
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.path.join('data', 'emails.db')
os.makedirs('data', exist_ok=True)

def get_connection():
    return sqlite3.connect(DB_PATH)

def sync_from_sheets():
    from tools.sheets_loader import load_dataframe
    print("[DB] Syncing from Google Sheets...")
    df = load_dataframe()

    if df.empty:
        print("[DB] No data to sync.")
        return 0

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(' ', '_')
    )

    conn = get_connection()
    df.to_sql('emails', conn, if_exists='replace', index=False)
    conn.close()
    print(f"[DB] Synced {len(df)} rows into emails table.")
    return len(df)

def get_schema_description() -> str:
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("PRAGMA table_info(emails)")
        columns = cursor.fetchall()
        cursor.execute("SELECT COUNT(*) FROM emails")
        row_count = cursor.fetchone()[0]
    except Exception:
        conn.close()
        return "No data yet. Run the Gmail agent first to populate the database."

    conn.close()

    if not columns:
        return "No data yet."

    lines = [f"Table: emails ({row_count} rows)\n", "Columns:"]
    for col in columns:
        lines.append(f"  - {col[1]} ({col[2]})")
    return '\n'.join(lines)

def run_query(sql: str) -> pd.DataFrame:
    conn = get_connection()
    try:
        df = pd.read_sql_query(sql, conn)
        return df
    finally:
        conn.close()