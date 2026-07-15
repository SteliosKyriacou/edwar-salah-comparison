import pandas as pd

df = pd.read_csv("V25_big.csv")
df["Status categorized"] = df["Status categorized"].astype(str).str.lower().str.strip()
df = df[df["Status categorized"].isin(["approved", "failed"])].copy()

def map_outcome(row):
    if str(row["Status categorized"]).lower().strip() == "approved":
        return "Approved"
    else:
        reason = str(row.get("failure reason", "")).lower().strip()
        if "market failure" in reason:
            return "Market Failure"
        elif "scientific failure" in reason:
            return "Scientific Failure"
        else:
            return "Other Failure"
df["outcome"] = df.apply(map_outcome, axis=1)

score_col = "MedChem Score V25"
df["Score_num"] = pd.to_numeric(df[score_col], errors="coerce")

raw_scores = df["Score_num"]
score_bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
score_labels = ["0-10", "10-20", "20-30", "30-40", "40-50", "50-60", "60-70", "70-80", "80-90", "90-100"]

df["bin"] = pd.cut(df["Score_num"], bins=score_bins, labels=score_labels, include_lowest=True)

target_drugs = df[(df["bin"] == "0-10") & (df["outcome"] == "Scientific Failure")]

for idx, row in target_drugs.iterrows():
    print("="*80)
    print(f"Name: {row['Name']}")
    print(f"Indication: {row['Indication (highest phase)']}")
    print(f"Target: {row['Target Protein']}")
    print(f"MedChem Score: {row[score_col]}")
    print(f"MedChem Rationale V25: {row['Rationale V25']}")
    print(f"Bio Verdict: {row.get('Bio Verdict V25', '')}")
    print(f"Toxi Verdict: {row.get('Toxi Verdict V25', '')}")
