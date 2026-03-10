"""V20 Edward-Only audit on neurodegenerative clinical candidates (no Salah)."""

import pandas as pd
import json
import os
import time
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

BASE = os.path.join(os.path.dirname(__file__), "..")
load_dotenv(os.path.join(BASE, ".env"))

INPUT_FILE = os.path.join(BASE, "neuro_candidates.csv")
OUTPUT_FILE = os.path.join(BASE, "NEURO_V20_EDWARD_ONLY.csv")
PROGRESS_FILE = os.path.join(BASE, "neuro_v20_progress.jsonl")

with open(os.path.join(BASE, "Agents/edward-medchem-rationalist/INSTRUCTIONS.md")) as f:
    EDWARD_PROMPT = f.read()

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


def run_edward_only(smiles, target, indication):
    edward_input = f"""
    Molecule SMILES: {smiles}
    Target Class: {target}
    Indication: {indication}

    TASK: Provide your MedChem audit as Edward. Evaluate this molecule strictly on chemical structure and physical chemistry.
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

    return edward_data


def main():
    df = pd.read_csv(INPUT_FILE)

    start_index = 0
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            start_index = sum(1 for line in f)

    print(f"Starting Neuro V20 Edward-Only Audit from index {start_index} (n={len(df)})...", flush=True)

    for i in range(start_index, len(df)):
        row = df.iloc[i]
        smiles = str(row['isomeric'])
        target = str(row['target_class'])
        indication = str(row['therapeutic_area'])
        name = str(row['name'])

        print(f"[{i+1}/{len(df)}] {name}...", flush=True)

        try:
            result = run_edward_only(smiles, target, indication)
            with open(PROGRESS_FILE, "a") as f:
                f.write(json.dumps(result) + "\n")
            score = result.get('edward_score', 'N/A')
            tcsp = result.get('tcsp', 0)
            tcsp_pct = tcsp * 100 if isinstance(tcsp, float) and tcsp <= 1 else tcsp
            print(f"    Score={score}  TCSP={tcsp_pct:.2f}%", flush=True)
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
        "edward_score": "Edward Score V20",
        "rational": "Rationale V20",
        "p1_prob": "P1 Prob V20",
        "p1_rationale": "P1 Rationale V20",
        "p2_prob": "P2 Prob V20",
        "p2_rationale": "P2 Rationale V20",
        "p3_prob": "P3 Prob V20",
        "p3_rationale": "P3 Rationale V20",
        "tcsp": "TCSP V20",
    })

    final_df = pd.concat([df.reset_index(drop=True), res_df.reset_index(drop=True)], axis=1)
    final_df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nDone! Output: {OUTPUT_FILE} ({len(final_df)} rows)", flush=True)


if __name__ == "__main__":
    main()
