import json
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

# Load .env
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Load agent instructions
BASE = os.path.join(os.path.dirname(__file__), "..")
with open(os.path.join(BASE, "Agents/edward-medchem-rationalist/INSTRUCTIONS.md")) as f:
    EDWARD_PROMPT = f.read()
with open(os.path.join(BASE, "Agents/salah-biological-rationalist/INSTRUCTIONS.md")) as f:
    SALAH_PROMPT = f.read()

llm = ChatGoogleGenerativeAI(model="gemini-3-pro-preview", temperature=0.0)

# First molecule from EDWARD_V22_MASTER_MODERN.csv
SMILES = "CN(C)CCCC1(C2=C(CO1)C=C(C=C2)C#N)C3=CC=C(C=C3)F"
TARGET = "SSRI"
INDICATION = "CNS"

print("=" * 70)
print("RERUN: Citalopram (Edward x Salah V22 Coordinated Audit)")
print("=" * 70)

# 1. SALAH
print("\n>>> Running Salah (Biological Rationalist)...")
salah_input = f"Evaluate the biological risk: Target {TARGET}, Indication {INDICATION} for molecule {SMILES}."
salah_resp = llm.invoke([SystemMessage(content=SALAH_PROMPT), HumanMessage(content=salah_input)])

salah_content = salah_resp.content
if isinstance(salah_content, list):
    salah_content = "".join([str(c.get('text', '')) if isinstance(c, dict) else str(c) for c in salah_content])

salah_clean = salah_content.replace("```json", "").replace("```", "").strip()
start_s = salah_clean.find('{')
end_s = salah_clean.rfind('}') + 1
salah_data = json.loads(salah_clean[start_s:end_s])

print("\n--- SALAH OUTPUT ---")
print(json.dumps(salah_data, indent=2))

# 2. EDWARD
print("\n>>> Running Edward (MedChem Rationalist) with Salah's advisory...")
edward_input = f"""
Molecule SMILES: {SMILES}
Target Class: {TARGET}
Indication: {INDICATION}

BIO-ADVISORY FROM SALAH (Biological/Clinical Expert):
Verdict: {salah_data['salah_verdict']}
Biological Rationale: {salah_data['biological_rationale']}
Penalty for Historical Target Stigma: {salah_data['target_stigma_penalty']} points

TASK: Provide your final MedChem audit as Edward. Integrate the Biological Advisory above into your rationale and final Edward Score.
"""
edward_resp = llm.invoke([SystemMessage(content=EDWARD_PROMPT), HumanMessage(content=edward_input)])

edward_content = edward_resp.content
if isinstance(edward_content, list):
    edward_content = "".join([str(c.get('text', '')) if isinstance(c, dict) else str(c) for c in edward_content])

edward_clean = edward_content.replace("```json", "").replace("```", "").strip()
start_e = edward_clean.find('{')
end_e = edward_clean.rfind('}') + 1
edward_data = json.loads(edward_clean[start_e:end_e])

print("\n--- EDWARD OUTPUT ---")
print(json.dumps(edward_data, indent=2))

# 3. COMPARISON
print("\n" + "=" * 70)
print("COMPARISON: Original CSV vs. New Rerun")
print("=" * 70)

csv_values = {
    "Edward Score V22": 12,
    "Salah Verdict": "ELITE",
    "P1 Prob": 0.95,
    "P2 Prob": 0.90,
    "P3 Prob": 0.85,
    "TCSP": 0.73,
}

new_values = {
    "Edward Score V22": edward_data.get("edward_score"),
    "Salah Verdict": salah_data.get("salah_verdict"),
    "P1 Prob": edward_data.get("p1_prob"),
    "P2 Prob": edward_data.get("p2_prob"),
    "P3 Prob": edward_data.get("p3_prob"),
    "TCSP": edward_data.get("tcsp"),
}

print(f"\n{'Metric':<20} {'Original CSV':>15} {'New Rerun':>15} {'Delta':>10}")
print("-" * 62)
for key in csv_values:
    orig = csv_values[key]
    new = new_values[key]
    if isinstance(orig, (int, float)) and isinstance(new, (int, float)):
        delta = new - orig
        print(f"{key:<20} {orig:>15} {new:>15} {delta:>+10.2f}")
    else:
        match = "MATCH" if str(orig) == str(new) else "DIFF"
        print(f"{key:<20} {str(orig):>15} {str(new):>15} {match:>10}")

print("\n--- SALAH RATIONALE (NEW) ---")
print(salah_data.get("biological_rationale", "N/A"))
print("\n--- EDWARD RATIONALE (NEW) ---")
print(edward_data.get("rational", edward_data.get("rationale", "N/A")))
