"""V23 Coordinated Edward+Salah audit on 2025 drug data."""

import pandas as pd
import json
import os
import time
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

BASE = os.path.join(os.path.dirname(__file__), "..")
load_dotenv(os.path.join(BASE, ".env"))

INPUT_FILE = os.path.join(BASE, "2025_drug_data_complete.csv")
OUTPUT_FILE = os.path.join(BASE, "Salah", "2025_V23_EDWARD_SALAH.csv")
PROGRESS_FILE = os.path.join(BASE, "2025_v23_progress.jsonl")

with open(os.path.join(BASE, "Agents/edward-medchem-rationalist/INSTRUCTIONS.md")) as f:
    EDWARD_PROMPT = f.read()
with open(os.path.join(BASE, "Agents/salah-biological-rationalist/INSTRUCTIONS.md")) as f:
    SALAH_PROMPT = f.read()

llm = ChatGoogleGenerativeAI(model="gemini-3-pro-preview", temperature=0.0)


def parse_json(content):
    if isinstance(content, list):
        content = "".join(
            str(c.get('text', '')) if isinstance(c, dict) else str(c) for c in content
        )
    clean = content.replace("```json", "").replace("```", "").strip()
    start = clean.find('{')
    end = clean.rfind('}') + 1
    return json.loads(clean[start:end])


def run_coordinated_audit(smiles, target, indication):
    # 1. SALAH
    salah_input = f"Evaluate the biological risk: Target {target}, Indication {indication} for molecule {smiles}."
    salah_resp = llm.invoke([SystemMessage(content=SALAH_PROMPT), HumanMessage(content=salah_input)])
    salah_data = parse_json(salah_resp.content)

    # 2. EDWARD
    edward_input = f"""
    Molecule SMILES: {smiles}
    Target Class: {target}
    Indication: {indication}

    BIO-ADVISORY FROM SALAH (Biological/Clinical Expert):
    Verdict: {salah_data['salah_verdict']}
    Biological Rationale: {salah_data['biological_rationale']}
    Penalty for Historical Target Stigma: {salah_data['target_stigma_penalty']} points

    TASK: Provide your final MedChem audit as Edward. Integrate the Biological Advisory above into your rationale and final Edward Score.
    """
    edward_resp = llm.invoke([SystemMessage(content=EDWARD_PROMPT), HumanMessage(content=edward_input)])
    edward_data = parse_json(edward_resp.content)

    # Recalculate TCSP
    p1 = edward_data.get("p1_prob", 0)
    p2 = edward_data.get("p2_prob", 0)
    p3 = edward_data.get("p3_prob", 0)
    p1 = p1 / 100 if p1 > 1 else p1
    p2 = p2 / 100 if p2 > 1 else p2
    p3 = p3 / 100 if p3 > 1 else p3
    edward_data["tcsp"] = round(p1 * p2 * p3, 6)

    return {
        **edward_data,
        "salah_verdict": salah_data['salah_verdict'],
        "biological_risk": salah_data['biological_rationale'],
        "clinical_attrition_risk": salah_data.get('clinical_attrition_risk', ''),
        "target_stigma_penalty": salah_data.get('target_stigma_penalty', 0),
        "p3_cap_reason": salah_data.get('p3_cap_reason', ''),
    }


def main():
    df = pd.read_csv(INPUT_FILE)

    start_index = 0
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            start_index = sum(1 for line in f)

    print(f"Starting 2025 V23 Coordinated Audit from index {start_index} (n={len(df)})...", flush=True)

    for i in range(start_index, len(df)):
        row = df.iloc[i]
        smiles = str(row['isomeric'])
        target = str(row['target_class'])
        indication = str(row['therapeutic_area'])
        name = str(row['compound'])

        print(f"[{i+1}/{len(df)}] {name}...", flush=True)

        try:
            result = run_coordinated_audit(smiles, target, indication)
            with open(PROGRESS_FILE, "a") as f:
                f.write(json.dumps(result) + "\n")
            score = result.get('edward_score', 'N/A')
            verdict = result.get('salah_verdict', 'N/A')
            tcsp = result.get('tcsp', 0)
            tcsp_pct = tcsp * 100 if isinstance(tcsp, float) and tcsp <= 1 else tcsp
            print(f"    Score={score}  Verdict={verdict}  TCSP={tcsp_pct:.2f}%", flush=True)
        except Exception as e:
            print(f"    ERROR: {e}", flush=True)
            with open(PROGRESS_FILE, "a") as f:
                f.write(json.dumps({"error": str(e)}) + "\n")

        time.sleep(1)

    # Finalize CSV
    results_list = []
    with open(PROGRESS_FILE, "r") as f:
        for line in f:
            results_list.append(json.loads(line))

    res_df = pd.DataFrame(results_list)
    res_df = res_df.rename(columns={
        "edward_score": "Edward Score V23",
        "rational": "Rationale V23",
        "p1_prob": "P1 Prob V23",
        "p1_rationale": "P1 Rationale V23",
        "p2_prob": "P2 Prob V23",
        "p2_rationale": "P2 Rationale V23",
        "p3_prob": "P3 Prob V23",
        "p3_rationale": "P3 Rationale V23",
        "tcsp": "TCSP V23",
        "salah_verdict": "Salah Verdict V23",
        "biological_risk": "Biological Risk V23",
        "clinical_attrition_risk": "Clinical Attrition Risk V23",
        "target_stigma_penalty": "Target Stigma Penalty V23",
        "p3_cap_reason": "P3 Cap Reason V23",
    })

    final_df = pd.concat([df.reset_index(drop=True), res_df.reset_index(drop=True)], axis=1)
    final_df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nDone! Output: {OUTPUT_FILE} ({len(final_df)} rows)", flush=True)


if __name__ == "__main__":
    main()
