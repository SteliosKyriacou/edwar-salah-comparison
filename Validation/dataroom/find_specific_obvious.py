import csv

keywords = ['textbook', 'classic pharmacophore', 'approved control', 'well-characterized', 'highly validated']

print("Searching for obvious rationales...")
with open('SM_V25_GLOBAL.csv', 'r', encoding='utf-8', errors='replace') as f:
    reader = csv.DictReader(f)
    found = 0
    for row in reader:
        rationale = row.get('Rationale V25', '')
        compound = row.get('compound', 'Unknown')
        
        text_lower = rationale.lower()
        if any(k in text_lower for k in keywords):
            print(f"--- Compound: {compound} ---")
            print(f"Rationale: {rationale}\n")
            found += 1
            if found >= 3:
                break

