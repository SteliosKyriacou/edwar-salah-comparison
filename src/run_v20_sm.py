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
OUTPUT_FILE = os.path.join(BASE, "SM_V20_EDWARD_ONLY.csv")
PROGRESS_FILE = os.path.join(BASE, "sm_v20_progress.jsonl")

with open(os.path.join(BASE, "Agents/edward-medchem-rationalist/INSTRUCTIONS.md")) as f:
    EDWARD_PROMPT = f.read()

llm = ChatGoogleGenerativeAI(model="gemini-3-pro-preview", temperature=0.0)


def extract_year(val):
    if pd.isna(val):
        return None
    m = re.search(r'(\d{4})', str(val))
    return int(m.group(1)) if m else None


def filter_modern(df):
    df['year_clean'] = df['year-approved'].apply(extract_year).fillna(
        df['year_stopped'].apply(extract_year)
    )
    df = df[df['year_clean'] >= 1999].reset_index(drop=True)
    return df


def run_edward_only(smiles):
    edward_input = f"Evaluate this molecule: {smiles}"
    resp = llm.invoke([
        SystemMessage(content=EDWARD_PROMPT),
        HumanMessage(content=edward_input)
    ])

    content = resp.content
    if isinstance(content, list):
        content = "".join(
            [str(c.get('text', '')) if isinstance(c, dict) else str(c) for c in content]
        )

    clean = content.replace("```json", "").replace("```", "").strip()
    start_idx = clean.find('{')
    end_idx = clean.rfind('}') + 1
    return json.loads(clean[start_idx:end_idx])


def main():
    df = pd.read_csv(INPUT_FILE)
    df = filter_modern(df)

    start_index = 0
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            start_index = sum(1 for line in f)

    print(f"Starting V20 Edward-Only SM Audit from index {start_index} (n={len(df)})...", flush=True)

    for i in range(start_index, len(df)):
        row = df.iloc[i]
        smiles = str(row['isomeric'])

        print(f"Processing {i+1}/{len(df)}...", flush=True)

        try:
            result = run_edward_only(smiles)
            with open(PROGRESS_FILE, "a") as f:
                f.write(json.dumps(result) + "\n")
            print(f"  Score: {result.get('edward_score', 'N/A')}", flush=True)
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
        "edward_score": "Edward Score V20",
        "rational": "Rationale V20",
        "p1_prob": "P1 Prob V20",
        "p1_rationale": "P1 Rationale V20",
        "p2_prob": "P2 Prob V20",
        "p2_rationale": "P2 Rationale V20",
        "p3_prob": "P3 Prob V20",
        "p3_rationale": "P3 Rationale V20",
        "tcsp": "TCSP V20"
    })

    final_df = pd.concat([df.reset_index(drop=True), res_df.reset_index(drop=True)], axis=1)
    final_df.to_csv(OUTPUT_FILE, index=False)
    print(f"V20 Edward-Only Audit Complete: {OUTPUT_FILE} ({len(final_df)} rows)", flush=True)


if __name__ == "__main__":
    main()
