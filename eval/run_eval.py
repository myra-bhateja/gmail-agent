import os
import json
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_extractor import extract_email_info

SAVE_DIR     = os.path.join(os.path.dirname(__file__), 'sample_emails')
LABELS_FILE  = os.path.join(os.path.dirname(__file__), 'labels.json')
RESULTS_FILE = os.path.join(os.path.dirname(__file__), 'eval_results.json')

EVAL_FIELDS = ['urgency', 'category', 'action_required', 'sentiment']

def run_eval():
    if not os.path.exists(LABELS_FILE):
        print("No labels found. Run label_emails.py first.")
        return

    with open(LABELS_FILE, 'r') as f:
        ground_truth = json.load(f)

    email_files    = sorted(f for f in os.listdir(SAVE_DIR) if f.endswith('.json'))
    labelled_files = [f for f in email_files if f.replace('.json', '') in ground_truth]

    print(f"Running eval on {len(labelled_files)} labelled emails...\n")

    results        = []
    correct_counts = {field: 0 for field in EVAL_FIELDS}
    total          = len(labelled_files)

    for i, filename in enumerate(labelled_files):
        email_id = filename.replace('.json', '')
        filepath = os.path.join(SAVE_DIR, filename)

        with open(filepath, 'r', encoding='utf-8') as f:
            email = json.load(f)

        print(f"[{i+1}/{total}] {email['subject'][:50]}")

        try:
            claude_output = extract_email_info(email)
        except Exception as e:
            print(f"  ERROR: {e}")
            continue

        human_label  = ground_truth[email_id]
        field_results = {}

        for field in EVAL_FIELDS:
            human_val  = human_label.get(field, '').strip().lower()
            claude_val = claude_output.get(field, '').strip().lower()
            is_correct = (human_val == claude_val)

            field_results[field] = {
                'human'  : human_val,
                'claude' : claude_val,
                'correct': is_correct
            }

            if is_correct:
                correct_counts[field] += 1

        results.append({
            'email_id'     : email_id,
            'subject'      : email['subject'],
            'field_results': field_results
        })

    # Print report
    print(f"\n{'='*60}")
    print("EVAL REPORT")
    print(f"{'='*60}")
    print(f"Total emails evaluated: {total}\n")
    print("Accuracy per field:")

    overall_correct = 0
    overall_total   = 0

    for field in EVAL_FIELDS:
        acc = correct_counts[field] / total * 100
        bar = '█' * int(acc / 5) + '░' * (20 - int(acc / 5))
        print(f"  {field:<20} {bar}  {acc:.1f}%  ({correct_counts[field]}/{total})")
        overall_correct += correct_counts[field]
        overall_total   += total

    overall_acc = overall_correct / overall_total * 100
    print(f"\n  {'OVERALL':<20} {overall_acc:.1f}%")

    print(f"\n{'='*60}")
    print("MISMATCHES:")
    print(f"{'='*60}")

    any_mismatch = False
    for result in results:
        mismatches = {
            field: v for field, v in result['field_results'].items()
            if not v['correct']
        }
        if mismatches:
            any_mismatch = True
            print(f"\nEmail: {result['subject'][:60]}")
            for field, v in mismatches.items():
                print(f"  {field}: you said '{v['human']}', Gemini said '{v['claude']}'")

    if not any_mismatch:
        print("No mismatches — perfect score!")

    output = {
        'run_at'          : datetime.now().isoformat(),
        'total_emails'    : total,
        'accuracy'        : {f: correct_counts[f] / total for f in EVAL_FIELDS},
        'overall_accuracy': overall_acc / 100,
        'results'         : results
    }

    with open(RESULTS_FILE, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nFull results saved to eval/eval_results.json")

if __name__ == '__main__':
    run_eval()