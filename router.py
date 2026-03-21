def route_email(email: dict, extracted: dict):
    urgency  = extracted.get('urgency', 'low')
    category = extracted.get('category', 'other')
    action   = extracted.get('action_required', 'no')

    print(f"\n--- Routing: {email['subject'][:60]} ---")
    print(f"  Category : {category}")
    print(f"  Urgency  : {urgency}")
    print(f"  Action   : {action} — {extracted.get('action_description','none')}")

    if urgency   == 'high'                  : print("  HIGH URGENCY — review immediately")
    if category  == 'sales'                 : print("  Sales email — consider following up")
    if category  in ['spam','newsletter']   : print(f"  Low priority — {category}")
    if action    == 'yes'                   : print(f"  Action needed: {extracted.get('action_description','')}")