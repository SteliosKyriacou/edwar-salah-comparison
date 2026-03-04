import pandas as pd
import json
import os
import re
import time
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

BASE = os.path.join(os.path.dirname(__file__), "..")
load_dotenv(os.path.join(BASE, ".env"))

INPUT_FILE = os.path.join(BASE, "final_drug_data_SM_complete.csv")
OUTPUT_FILE = os.path.join(BASE, "SM_V22_EDWARD_SALAH_LEGACY.csv")
PROGRESS_FILE = os.path.join(BASE, "sm_v22_legacy_progress.jsonl")

with open(os.path.join(BASE, "Agents/edward-medchem-rationalist/INSTRUCTIONS.md")) as f:
    EDWARD_PROMPT = f.read()
with open(os.path.join(BASE, "Agents/salah-biological-rationalist/INSTRUCTIONS.md")) as f:
    SALAH_PROMPT = f.read()

llm = ChatGoogleGenerativeAI(model="gemini-3-pro-preview", temperature=0.0)


def extract_year(val):
    if pd.isna(val):
        return None
    m = re.search(r'(\d{4})', str(val))
    return int(m.group(1)) if m else None


def filter_legacy(df):
    df['year_clean'] = df['year-approved'].apply(extract_year).fillna(
        df['year_stopped'].apply(extract_year)
    )
    df = df[df['year_clean'] < 1999].reset_index(drop=True)
    return df


def run_coordinated_audit(smiles, target, indication):
    # 1. SALAH'S TURN
    salah_input = f"Evaluate the biological risk: Target {target}, Indication {indication} for molecule {smiles}."
    salah_resp = llm.invoke([
        SystemMessage(content=SALAH_PROMPT),
        HumanMessage(content=salah_input)
    ])

    salah_content = salah_resp.content
    if isinstance(salah_content, list):
        salah_content = "".join(
            [str(c.get('text', '')) if isinstance(c, dict) else str(c) for c in salah_content]
        )

    salah_clean = salah_content.replace("```json", "").replace("```", "").strip()
    start_s = salah_clean.find('{')
    end_s = salah_clean.rfind('}') + 1
    salah_data = json.loads(salah_clean[start_s:end_s])

    # 2. EDWARD'S TURN
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
    edward_resp = llm.invoke([
        SystemMessage(content=EDWARD_PROMPT),
        HumanMessage(content=edward_input)
    ])

    edward_content = edward_resp.content
    if isinstance(edward_content, list):
        edward_content = "".join(
            [str(c.get('text', '')) if isinstance(c, dict) else str(c) for c in edward_content]
        )

    edward_clean = edward_content.replace("```json", "").replace("```", "").strip()
    start_e = edward_clean.find('{')
    end_e = edward_clean.rfind('}') + 1
    edward_data = json.loads(edward_clean[start_e:end_e])

    return {**edward_data, "salah_verdict": salah_data['salah_verdict'], "biological_risk": salah_data['biological_rationale']}


def main():
    df = pd.read_csv(INPUT_FILE)
    df = filter_legacy(df)

    start_index = 0
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            start_index = sum(1 for line in f)

    print(f"Starting V22 Edward+Salah LEGACY Audit from index {start_index} (n={len(df)})...", flush=True)

    for i in range(start_index, len(df)):
        row = df.iloc[i]
        smiles = str(row['isomeric'])
        target = str(row['target_class'])
        indication = str(row['therapeutic_area'])

        print(f"Processing {i+1}/{len(df)}...", flush=True)

        try:
            result = run_coordinated_audit(smiles, target, indication)
            with open(PROGRESS_FILE, "a") as f:
                f.write(json.dumps(result) + "\n")
            print(f"  Score: {result.get('edward_score', 'N/A')} | Salah: {result.get('salah_verdict', 'N/A')}", flush=True)
        except Exception as e:
            print(f"  Error at index {i}: {e}", flush=True)
            with open(PROGRESS_FILE, "a") as f:
                f.write(json.dumps({"error": str(e)}) + "\n")

        time.sleep(1)

    # Finalize
    results_list = []
    with open(PROGRESS_FILE, "r") as f:
        for line in f:
            results_list.append(json.loads(line))

    res_df = pd.DataFrame(results_list)
    res_df = res_df.rename(columns={
        "edward_score": "Edward Score V22",
        "rational": "Rationale V22",
        "p1_prob": "P1 Prob V22",
        "p1_rationale": "P1 Rationale V22",
        "p2_prob": "P2 Prob V22",
        "p2_rationale": "P2 Rationale V22",
        "p3_prob": "P3 Prob V22",
        "p3_rationale": "P3 Rationale V22",
        "tcsp": "TCSP V22"
    })

    final_df = pd.concat([df.reset_index(drop=True), res_df.reset_index(drop=True)], axis=1)
    final_df.to_csv(OUTPUT_FILE, index=False)
    print(f"V22 Edward+Salah LEGACY Audit Complete: {OUTPUT_FILE} ({len(final_df)} rows)", flush=True)


if __name__ == "__main__":
    main()
