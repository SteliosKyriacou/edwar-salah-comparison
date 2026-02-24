import pandas as pd
import json
import os
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

os.environ["GOOGLE_API_KEY"] = "AIzaSyAE4QTjaE2K_28m3QlSdhpbBJBN8ZmH3fA"

# Load Instructions
with open("/home/node/.openclaw/workspace/Agents/edward-medchem-rationalist/INSTRUCTIONS.md", "r") as f:
    EDWARD_PROMPT = f.read()
with open("/home/node/.openclaw/workspace/Agents/salah-biological-rationalist/INSTRUCTIONS.md", "r") as f:
    SALAH_PROMPT = f.read()

INPUT_FILE = "/home/node/.openclaw/workspace/Edward_test/data/EDWARD_V20_MODERN_ERA_COMPLETE.csv"
OUTPUT_FILE = "/home/node/.openclaw/workspace/Edward_test/EDWARD_V22_COORDINATED_MODERN.csv"
PROGRESS_FILE = "/home/node/.openclaw/workspace/Edward_test/edward_v22_progress.jsonl"

llm = ChatGoogleGenerativeAI(model="gemini-3-pro-preview", temperature=0.0)

def run_coordinated_audit(smiles, target, indication):
    # 1. SALAH'S TURN
    salah_input = f"Evaluate the biological risk: Target {target}, Indication {indication} for molecule {smiles}."
    salah_resp = llm.invoke([SystemMessage(content=SALAH_PROMPT), HumanMessage(content=salah_input)])
    
    salah_content = salah_resp.content
    if isinstance(salah_content, list):
        salah_content = "".join([str(c.get('text', '')) if isinstance(c, dict) else str(c) for c in salah_content])
    
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
    edward_resp = llm.invoke([SystemMessage(content=EDWARD_PROMPT), HumanMessage(content=edward_input)])
    
    edward_content = edward_resp.content
    if isinstance(edward_content, list):
        edward_content = "".join([str(c.get('text', '')) if isinstance(c, dict) else str(c) for c in edward_content])
        
    edward_clean = edward_content.replace("```json", "").replace("```", "").strip()
    start_e = edward_clean.find('{')
    end_e = edward_clean.rfind('}') + 1
    edward_data = json.loads(edward_clean[start_e:end_e])
    
    # Combine
    return {**edward_data, "salah_verdict": salah_data['salah_verdict'], "biological_risk": salah_data['biological_rationale']}

def main():
    df = pd.read_csv(INPUT_FILE)
    
    start_index = 0
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            start_index = sum(1 for line in f)

    print(f"🦾 Starting Global Edward V22 Coordinated Audit (Edward + Salah) from index {start_index} (n={len(df)})...", flush=True)

    for i in range(start_index, len(df)):
        row = df.iloc[i]
        print(f"Processing {i+1}/{len(df)}: {row['compound']}...", flush=True)
        try:
            res = run_coordinated_audit(str(row['isomeric']), str(row['target_class']), str(row['therapeutic_area']))
            with open(PROGRESS_FILE, "a") as f:
                f.write(json.dumps(res) + "\n")
            print(f"  Success.", flush=True)
        except Exception as e:
            print(f"  Error on {row['compound']}: {e}", flush=True)
            with open(PROGRESS_FILE, "a") as f:
                f.write(json.dumps({"error": str(e)}) + "\n")
        
        time.sleep(1) # Rate limit respect

    # Finalize
    results_list = []
    with open(PROGRESS_FILE, "r") as f:
        for line in f:
            results_list.append(json.loads(line))
    
    res_df = pd.DataFrame(results_list)
    # Rename to V22
    res_df = res_df.rename(columns={
        "edward_score": "Edward Score V22",
        "rational": "Rationale V22",
        "p1_prob": "P1 Prob V22",
        "p2_prob": "P2 Prob V22",
        "p3_prob": "P3 Prob V22",
        "tcsp": "TCSP V22"
    })
    
    final_df = pd.concat([df.reset_index(drop=True), res_df.reset_index(drop=True)], axis=1)
    final_df.to_csv(OUTPUT_FILE, index=False)
    print(f"🦾 V22 Coordinated Audit Complete: {OUTPUT_FILE}", flush=True)

if __name__ == "__main__":
    main()
