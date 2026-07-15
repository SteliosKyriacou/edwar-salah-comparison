import pandas as pd
import numpy as np

# Load the dataset
df = pd.read_csv('SM_V25_GLOBAL.csv', on_bad_lines='skip')

print(f"Total compounds: {len(df)}")

# Define keywords for obvious vs non-obvious
obvious_keywords = [
    'me-too', 'close comparator', 'classic pharmacophore', 'textbook', 
    'well-characterized', 'well-known', 'highly validated', 'classic hERG', 'expected primary metabolic', 'typical'
]

non_obvious_keywords = [
    'subtle', 'unique', 'unexpected', 'rare', 'unconventional', 'surprising', 
    'counterintuitive', 'complex DDI', 'cryptic', 'unprecedented', 'idiosyncratic', 'pleiotropic'
]

def classify_rationale(text):
    if not isinstance(text, str): return 'unknown'
    text_lower = text.lower()
    obv = any(k in text_lower for k in obvious_keywords)
    non_obv = any(k in text_lower for k in non_obvious_keywords)
    
    if obv and non_obv: return 'mixed'
    if obv: return 'obvious'
    if non_obv: return 'non-obvious'
    return 'neutral'

# Apply classification to Rationale V25
df['rationale_class'] = df['Rationale V25'].apply(classify_rationale)

# Get statistics
stats = df['rationale_class'].value_counts()
print("\nClassification Statistics:")
print(stats)

# Get some examples of obvious
print("\n--- Obvious Examples ---")
for idx, row in df[df['rationale_class'] == 'obvious'].head(2).iterrows():
    print(f"Compound: {row['compound']}, Target: {row['target_class']}")
    print(f"Rationale: {row['Rationale V25']}\n")

# Get some examples of non-obvious
print("\n--- Non-Obvious Examples ---")
for idx, row in df[df['rationale_class'] == 'non-obvious'].head(3).iterrows():
    print(f"Compound: {row['compound']}, Target: {row['target_class']}")
    print(f"Rationale: {row['Rationale V25']}\n")

