"""V22 Coordinated Edward+Salah audit — BATCHED (20 molecules per LLM call)."""

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
OUTPUT_FILE = os.path.join(BASE, "SM_V22_BATCHED.csv")
PROGRESS_FILE = os.path.join(BASE, "sm_v22_batched_progress.jsonl")

BATCH_SIZE = 20

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


def filter_modern(df):
    df['year_clean'] = df['year-approved'].apply(extract_year).fillna(
        df['year_stopped'].apply(extract_year)
    )
    df = df[df['year_clean'] >= 1999].reset_index(drop=True)
    return df


def parse_json_array(content):
    """Extract a JSON array from LLM response."""
    if isinstance(content, list):
        content = "".join(
            str(c.get('text', '')) if isinstance(c, dict) else str(c) for c in content
        )
    clean = content.replace("```json", "").replace("```", "").strip()
    start = clean.find('[')
    end = clean.rfind(']') + 1
    if start == -1 or end == 0:
        raise ValueError(f"No JSON array found in response: {clean[:200]}")
    return json.loads(clean[start:end])


def build_batch_prompt(molecules, role):
    """Build a batch prompt for either Salah or Edward."""
    lines = []
    for i, mol in enumerate(molecules):
        lines.append(f"MOLECULE {i+1}:")
        lines.append(f"  SMILES: {mol['smiles']}")
        lines.append(f"  Target: {mol['target']}")
        lines.append(f"  Indication: {mol['indication']}")
        if role == "edward" and "salah_data" in mol:
            sd = mol["salah_data"]
            lines.append(f"  BIO-ADVISORY FROM SALAH:")
            lines.append(f"    Verdict: {sd['salah_verdict']}")
            lines.append(f"    Biological Rationale: {sd['biological_rationale']}")
            lines.append(f"    Target Stigma Penalty: {sd['target_stigma_penalty']} points")
        lines.append("")
    return "\n".join(lines)


def run_salah_batch(molecules):
    """Run Salah on a batch of molecules."""
    batch_prompt = build_batch_prompt(molecules, "salah")
    prompt = f"""Evaluate the biological risk for each of the following {len(molecules)} molecules.

{batch_prompt}

IMPORTANT: Return a JSON ARRAY with exactly {len(molecules)} objects, one per molecule in order.
Each object must contain: salah_verdict, biological_rationale, target_stigma_penalty, clinical_attrition_risk, p3_cap_reason.
Return ONLY the JSON array, nothing else."""

    resp = llm.invoke([SystemMessage(content=SALAH_PROMPT), HumanMessage(content=prompt)])
    return parse_json_array(resp.content)


def run_edward_batch(molecules):
    """Run Edward on a batch of molecules (with Salah advisories attached)."""
    batch_prompt = build_batch_prompt(molecules, "edward")
    prompt = f"""Provide your final MedChem audit for each of the following {len(molecules)} molecules.
Integrate each molecule's Biological Advisory from Salah into your rationale and final Edward Score.

{batch_prompt}

IMPORTANT: Return a JSON ARRAY with exactly {len(molecules)} objects, one per molecule in order.
Each object must contain: edward_score, rational, metabolic_stability_estimate, potential_toxic_fragments, p1_prob, p1_rationale, p2_prob, p2_rationale, p3_prob, p3_rationale, tcsp.
Return ONLY the JSON array, nothing else."""

    resp = llm.invoke([SystemMessage(content=EDWARD_PROMPT), HumanMessage(content=prompt)])
    return parse_json_array(resp.content)


def process_batch(batch_molecules):
    """Process a batch: Salah → Edward → merge."""
    # 1. Salah batch
    salah_results = run_salah_batch(batch_molecules)
    if len(salah_results) != len(batch_molecules):
        raise ValueError(f"Salah returned {len(salah_results)} results for {len(batch_molecules)} molecules")

    # 2. Attach Salah data and run Edward batch
    for mol, sd in zip(batch_molecules, salah_results):
        mol["salah_data"] = sd

    edward_results = run_edward_batch(batch_molecules)
    if len(edward_results) != len(batch_molecules):
        raise ValueError(f"Edward returned {len(edward_results)} results for {len(batch_molecules)} molecules")

    # 3. Merge and recalculate TCSP
    combined = []
    for ed, sd in zip(edward_results, salah_results):
        p1 = ed.get("p1_prob", 0)
        p2 = ed.get("p2_prob", 0)
        p3 = ed.get("p3_prob", 0)
        p1 = p1 / 100 if p1 > 1 else p1
        p2 = p2 / 100 if p2 > 1 else p2
        p3 = p3 / 100 if p3 > 1 else p3
        ed["tcsp"] = round(p1 * p2 * p3, 6)

        combined.append({
            **ed,
            "salah_verdict": sd.get("salah_verdict", ""),
            "biological_risk": sd.get("biological_rationale", ""),
            "clinical_attrition_risk": sd.get("clinical_attrition_risk", ""),
            "target_stigma_penalty": sd.get("target_stigma_penalty", 0),
            "p3_cap_reason": sd.get("p3_cap_reason", ""),
        })
    return combined


def main():
    df = pd.read_csv(INPUT_FILE)
    df = filter_modern(df)
    n = len(df)

    # Resume from progress
    start_index = 0
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            start_index = sum(1 for line in f)

    print(f"Batched V22 Audit: {n} molecules, batch_size={BATCH_SIZE}, resuming from {start_index}", flush=True)

    for batch_start in range(start_index, n, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, n)
        batch_df = df.iloc[batch_start:batch_end]

        batch_molecules = []
        for _, row in batch_df.iterrows():
            batch_molecules.append({
                "smiles": str(row["isomeric"]),
                "target": str(row["target_class"]),
                "indication": str(row["therapeutic_area"]),
            })

        batch_num = batch_start // BATCH_SIZE + 1
        total_batches = (n + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"\n[Batch {batch_num}/{total_batches}] Molecules {batch_start+1}-{batch_end}...", flush=True)

        t0 = time.time()
        try:
            results = process_batch(batch_molecules)
            elapsed = time.time() - t0

            with open(PROGRESS_FILE, "a") as f:
                for r in results:
                    f.write(json.dumps(r) + "\n")

            scores = [r.get("edward_score", "?") for r in results]
            verdicts = [r.get("salah_verdict", "?") for r in results]
            print(f"    Done in {elapsed:.0f}s | Scores: {scores}", flush=True)
            print(f"    Verdicts: {verdicts}", flush=True)

        except Exception as e:
            elapsed = time.time() - t0
            print(f"    BATCH FAILED after {elapsed:.0f}s: {e}", flush=True)
            print(f"    Falling back to individual processing...", flush=True)

            # Fallback: process individually
            for j, mol in enumerate(batch_molecules):
                idx = batch_start + j
                print(f"    [{idx+1}/{n}] Individual fallback...", flush=True)
                try:
                    salah_results = run_salah_batch([mol])
                    mol["salah_data"] = salah_results[0]
                    edward_results = run_edward_batch([mol])
                    ed = edward_results[0]
                    sd = salah_results[0]

                    p1 = ed.get("p1_prob", 0)
                    p2 = ed.get("p2_prob", 0)
                    p3 = ed.get("p3_prob", 0)
                    p1 = p1 / 100 if p1 > 1 else p1
                    p2 = p2 / 100 if p2 > 1 else p2
                    p3 = p3 / 100 if p3 > 1 else p3
                    ed["tcsp"] = round(p1 * p2 * p3, 6)

                    result = {
                        **ed,
                        "salah_verdict": sd.get("salah_verdict", ""),
                        "biological_risk": sd.get("biological_rationale", ""),
                        "clinical_attrition_risk": sd.get("clinical_attrition_risk", ""),
                        "target_stigma_penalty": sd.get("target_stigma_penalty", 0),
                        "p3_cap_reason": sd.get("p3_cap_reason", ""),
                    }
                    with open(PROGRESS_FILE, "a") as f:
                        f.write(json.dumps(result) + "\n")
                    print(f"      Score={ed.get('edward_score')} Verdict={sd.get('salah_verdict')}", flush=True)
                except Exception as e2:
                    print(f"      FAILED: {e2}", flush=True)
                    with open(PROGRESS_FILE, "a") as f:
                        f.write(json.dumps({"error": str(e2)}) + "\n")

        time.sleep(2)

    # Finalize CSV
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
        "tcsp": "TCSP V22",
    })

    final_df = pd.concat([df.reset_index(drop=True), res_df.reset_index(drop=True)], axis=1)
    final_df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nDone! Output: {OUTPUT_FILE} ({len(final_df)} rows)", flush=True)


if __name__ == "__main__":
    main()
