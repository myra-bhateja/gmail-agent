import time
from gmail_reader   import get_unread_emails
from llm_extractor  import extract_email_info
from sheets_writer  import write_email_row
from router         import route_email
from tools.db       import sync_from_sheets
import json, os
from datetime import datetime

LOG_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'data', 'agent_log.jsonl'
)
os.makedirs('data', exist_ok=True)

def write_log(event_type, message, detail='', status='info'):
    entry = {
        'time'      : datetime.now().strftime('%H:%M:%S'),
        'event_type': event_type,
        'message'   : message,
        'detail'    : detail,
        'status'    : status
    }
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')

def run_once(max_emails=10):
    """
    Runs the agent exactly once — processes unread emails
    and stops. Called from the dashboard Run button.
    Returns a summary dict.
    """
    write_log('agent_start', 'Manual run triggered from dashboard', status='info')

    emails = get_unread_emails(max_results=max_emails)

    if not emails:
        write_log('gmail_read', 'No new emails found', status='info')
        return {'processed': 0, 'errors': 0, 'message': 'No new unread emails found.'}

    write_log('gmail_read', f'Found {len(emails)} new email(s)', status='success')

    processed = 0
    errors    = 0

    for email in emails:
        try:
            subject = email['subject'][:50]
            write_log('llm_extract', 'Sending to Gemini AI', detail=subject, status='info')
            extracted = extract_email_info(email)
            write_log('llm_extract',
                f"Extracted — urgency: {extracted.get('urgency')} category: {extracted.get('category')}",
                detail=subject, status='success')

            route_email(email, extracted)
            write_log('route', f"Routed — action: {extracted.get('action_required')}",
                detail=subject, status='info')

            write_email_row(email, extracted)
            write_log('sheets_write', 'Written to Google Sheets', detail=subject, status='success')

            processed += 1
            time.sleep(4)

        except Exception as e:
            write_log('error', 'Error processing email', detail=str(e)[:100], status='error')
            errors += 1
            continue

    write_log('db_sync', 'Syncing to SQLite', status='info')
    sync_from_sheets()
    write_log('db_sync', 'Sync complete', status='success')

    return {
        'processed': processed,
        'errors'   : errors,
        'message'  : f'Processed {processed} email(s) with {errors} error(s).'
    }