import os
import json
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gmail_reader import get_unread_emails

SAVE_DIR = os.path.join(os.path.dirname(__file__), 'sample_emails')

def save_emails(count=20):
    os.makedirs(SAVE_DIR, exist_ok=True)

    print(f"Fetching {count} emails from Gmail...")
    emails = get_unread_emails(max_results=count)

    if not emails:
        print("No unread emails found. Send yourself some test emails first.")
        return

    for i, email in enumerate(emails):
        filename = f"email_{i+1:02d}.json"
        filepath = os.path.join(SAVE_DIR, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(email, f, indent=2, ensure_ascii=False)

        print(f"Saved: {filename} — {email['subject'][:60]}")

    print(f"\nDone. {len(emails)} emails saved to eval/sample_emails/")
    print("Next step: run label_emails.py to manually label them.")

if __name__ == '__main__':
    save_emails(count=20)