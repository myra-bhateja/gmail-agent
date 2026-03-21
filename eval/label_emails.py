import os
import json

SAVE_DIR    = os.path.join(os.path.dirname(__file__), 'sample_emails')
LABELS_FILE = os.path.join(os.path.dirname(__file__), 'labels.json')

VALID_URGENCY   = ['high', 'medium', 'low']
VALID_CATEGORY  = ['sales', 'support', 'meeting', 'newsletter', 'spam', 'personal', 'other']
VALID_ACTION    = ['yes', 'no']
VALID_SENTIMENT = ['positive', 'neutral', 'negative']

def prompt_choice(question, valid_options):
    options_str = ' / '.join(valid_options)
    while True:
        answer = input(f"  {question} [{options_str}]: ").strip().lower()
        if answer in valid_options:
            return answer
        print(f"  Invalid. Please choose from: {options_str}")

def label_all_emails():
    if os.path.exists(LABELS_FILE):
        with open(LABELS_FILE, 'r') as f:
            labels = json.load(f)
        print(f"Resuming — {len(labels)} emails already labelled.\n")
    else:
        labels = {}

    email_files = sorted(f for f in os.listdir(SAVE_DIR) if f.endswith('.json'))

    if not email_files:
        print("No emails found. Run save_emails.py first.")
        return

    total = len(email_files)

    for i, filename in enumerate(email_files):
        email_id = filename.replace('.json', '')

        if email_id in labels:
            continue

        filepath = os.path.join(SAVE_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            email = json.load(f)

        print(f"\n{'='*60}")
        print(f"Email {i+1}/{total}: {filename}")
        print(f"{'='*60}")
        print(f"From    : {email.get('sender', '')}")
        print(f"Subject : {email.get('subject', '')}")
        print(f"Date    : {email.get('date', '')}")
        print(f"\nBody preview:\n{email.get('body', '')[:500]}")
        print(f"{'='*60}")

        label = {
            'urgency'        : prompt_choice('Urgency', VALID_URGENCY),
            'category'       : prompt_choice('Category', VALID_CATEGORY),
            'action_required': prompt_choice('Action required', VALID_ACTION),
            'sentiment'      : prompt_choice('Sentiment', VALID_SENTIMENT),
        }

        labels[email_id] = label

        with open(LABELS_FILE, 'w') as f:
            json.dump(labels, f, indent=2)

        print(f"  Saved. ({len(labels)}/{total} done)")

    print(f"\nAll {total} emails labelled. Saved to eval/labels.json")
    print("Next step: run run_eval.py")

if __name__ == '__main__':
    label_all_emails()