import csv
import sys

obvious_keywords = [
    'me-too', 'close comparator', 'classic pharmacophore', 'textbook', 
    'well-characterized', 'well-known', 'highly validated', 'classic herg', 'expected primary metabolic', 'typical', 'textbook cns', 'approved control'
]

non_obvious_keywords = [
    'subtle', 'unique', 'unexpected', 'rare', 'unconventional', 'surprising', 
    'counterintuitive', 'cryptic', 'unprecedented', 'idiosyncratic', 'pleiotropic', 'off-target', 'secondary pharmacology', 'complex ddi'
]

def classify_rationale(text):
    if not text: return 'unknown'
    text_lower = text.lower()
    obv = any(k in text_lower for k in obvious_keywords)
    non_obv = any(k in text_lower for k in non_obvious_keywords)
    
    if obv and non_obv: return 'mixed'
    if obv: return 'obvious'
    if non_obv: return 'non-obvious'
    return 'neutral'

with open('SM_V25_GLOBAL.csv', 'r', encoding='utf-8', errors='replace') as f:
    reader = csv.DictReader(f)
    
    counts = {'obvious': 0, 'non-obvious': 0, 'mixed': 0, 'neutral': 0, 'unknown': 0}
    obvious_examples = []
    non_obvious_examples = []
    
    for row in reader:
        rationale = row.get('Rationale V25', '')
        compound = row.get('compound', 'Unknown')
        
        c = classify_rationale(rationale)
        counts[c] += 1
        
        if c == 'obvious' and len(obvious_examples) < 2:
            obvious_examples.append((compound, rationale))
        elif c == 'non-obvious' and len(non_obvious_examples) < 3:
            non_obvious_examples.append((compound, rationale))

print("Classification Statistics:")
for k, v in counts.items():
    print(f"{k}: {v}")

print("\n--- Obvious Examples ---")
for comp, rat in obvious_examples:
    print(f"Compound: {comp}\nRationale: {rat}\n")

print("\n--- Non-Obvious Examples ---")
for comp, rat in non_obvious_examples:
    print(f"Compound: {comp}\nRationale: {rat}\n")

