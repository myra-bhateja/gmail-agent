import time
import schedule
from dotenv import load_dotenv
from gmail_reader   import get_unread_emails
from llm_extractor  import extract_email_info
from sheets_writer  import write_email_row
from router         import route_email
from tools.db       import sync_from_sheets

load_dotenv()

def run_agent():
    print("\n========================================")
    print("Agent running — checking for new emails...")
    print("========================================")

    emails = get_unread_emails(max_results=10)

    if not emails:
        print("No new emails found.")
        sync_from_sheets()
        return

    print(f"Found {len(emails)} new email(s). Processing...")

    for email in emails:
        try:
            print(f"\nProcessing: {email['subject'][:60]}")
            extracted = extract_email_info(email)
            route_email(email, extracted)
            write_email_row(email, extracted)
            time.sleep(4)        # ADD THIS — prevents hitting rate limit
        except Exception as e:
            print(f"Error processing '{email['subject']}': {e}")
            continue

    sync_from_sheets()
    print("\nDone. Waiting for next cycle...")

if __name__ == '__main__':
    print("Gmail Agent starting...")
    run_agent()

    schedule.every(5).minutes.do(run_agent)

    while True:
        schedule.run_pending()
        time.sleep(30)