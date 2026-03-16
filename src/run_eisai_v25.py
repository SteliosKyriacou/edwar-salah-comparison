"""V25 Multi-Agent Pipeline — Eisai Clinical Trials (N=40).

Reads Eisai_Clinical_Trials_Predicted.csv, strips old predictions,
runs V25 pipeline, and outputs to Validation/Eisai/.
"""

import pandas as pd
import json
import os
import math
import time
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(BASE, ".env"))

INPUT_FILE = os.path.join(BASE, "Validation", "data", "Eisai_Clinical_Trials_Predicted.csv")
OUTPUT_FILE = os.path.join(BASE, "Validation", "Eisai", "Eisai_V25.csv")
PROGRESS_FILE = os.path.join(BASE, "eisai_v25_progress.jsonl")

# Old prediction columns to strip
PREDICTION_COLS = [
    'Prediction_TCSP', 'Prediction_Phase1', 'Prediction_Phase2',
    'Prediction_Phase3', 'Prediction_Verdict', 'Prediction_Rationale',
    'Binned Prediction_TCSP',
]

with open(os.path.join(BASE, "Agents/medchem-rationalist/INSTRUCTIONS.md")) as f:
    EDWARD_PROMPT = f.read()
with open(os.path.join(BASE, "Agents/biological-rationalist/INSTRUCTIONS.md")) as f:
    SALAH_PROMPT = f.read()
with open(os.path.join(BASE, "Agents/toxi-predictive-toxicologist/INSTRUCTIONS.md")) as f:
    TOXI_PROMPT = f.read()
with open(os.path.join(BASE, "Agents/pharma-clinical-pharmacologist/INSTRUCTIONS.md")) as f:
    PHARMA_PROMPT = f.read()

llm = ChatGoogleGenerativeAI(model="gemini-3-pro-preview", temperature=0.0)
TCSP_CEIL = 0.40


def parse_json(content):
    if isinstance(content, list):
        content = "".join(
            str(c.get('text', '')) if isinstance(c, dict) else str(c) for c in content
        )
    clean = content.replace("```json", "").replace("```", "").strip()
    start = clean.find('{')
    end = clean.rfind('}') + 1
    return json.loads(clean[start:end])


def norm_prob(p):
    if p is None:
        return 0.5
    p = float(p)
    if p > 1:
        p = p / 100
    return max(0.0, min(1.0, p))


def tcsp_to_score(tcsp):
    score = round(100 * (1 - math.sqrt(tcsp / TCSP_CEIL)))
    return max(1, min(100, score))


def run_salah(smiles, target, indication):
    msg = f"Evaluate the biological feasibility: Target {target}, Indication {indication} for molecule {smiles}."
    resp = llm.invoke([SystemMessage(content=SALAH_PROMPT), HumanMessage(content=msg)])
    return parse_json(resp.content)


def run_toxi(smiles, target, indication):
    msg = f"Evaluate the safety liabilities: Target {target}, Indication {indication} for molecule {smiles}."
    resp = llm.invoke([SystemMessage(content=TOXI_PROMPT), HumanMessage(content=msg)])
    return parse_json(resp.content)


def run_pharma(smiles, target, indication):
    msg = f"Evaluate the PK/PD feasibility: Target {target}, Indication {indication} for molecule {smiles}."
    resp = llm.invoke([SystemMessage(content=PHARMA_PROMPT), HumanMessage(content=msg)])
    return parse_json(resp.content)


def run_edward_pass1(smiles, target, indication):
    msg = f"""PASS 1 — Blind Structural Assessment (no advisory data).

Molecule SMILES: {smiles}
Target Class: {target}
Indication: {indication}

Provide your structural critique as Pass 1. Output JSON only."""
    resp = llm.invoke([SystemMessage(content=EDWARD_PROMPT), HumanMessage(content=msg)])
    return parse_json(resp.content)


def run_edward_pass2(smiles, target, indication, pass1, salah, toxi, pharma):
    msg = f"""PASS 2 — Advisory Integration.

Molecule SMILES: {smiles}
Target Class: {target}
Indication: {indication}

YOUR PASS 1 STRUCTURAL ASSESSMENT:
{json.dumps(pass1, indent=2)}

SALAH ADVISORY (Biology):
Verdict: {salah.get('salah_verdict', 'N/A')}
Rationale: {salah.get('biological_rationale', 'N/A')}
Mechanism Validation: {salah.get('mechanism_validation', 'N/A')}
Druggability: {salah.get('druggability_assessment', 'N/A')}
bio_p1={salah.get('bio_p1', 'N/A')} — {salah.get('bio_p1_rationale', '')}
bio_p2={salah.get('bio_p2', 'N/A')} — {salah.get('bio_p2_rationale', '')}
bio_p3={salah.get('bio_p3', 'N/A')} — {salah.get('bio_p3_rationale', '')}

TOXI ADVISORY (Toxicology):
Verdict: {toxi.get('toxi_verdict', 'N/A')}
Rationale: {toxi.get('toxi_rationale', 'N/A')}
Therapeutic Window: {toxi.get('therapeutic_window', 'N/A')}
Primary Concern: {toxi.get('primary_tox_concern', 'N/A')}
On-Target Risk: {toxi.get('on_target_tox_risk', 'N/A')}
Off-Target Risk: {toxi.get('off_target_tox_risk', 'N/A')}
tox_p1={toxi.get('tox_p1', 'N/A')} — {toxi.get('tox_p1_rationale', '')}
tox_p2={toxi.get('tox_p2', 'N/A')} — {toxi.get('tox_p2_rationale', '')}
tox_p3={toxi.get('tox_p3', 'N/A')} — {toxi.get('tox_p3_rationale', '')}

PHARMA ADVISORY (Pharmacology):
Verdict: {pharma.get('pharma_verdict', 'N/A')}
Rationale: {pharma.get('pharma_rationale', 'N/A')}
Predicted Dose: {pharma.get('predicted_dose_range', 'N/A')}
Oral Feasibility: {pharma.get('oral_feasibility', 'N/A')}
DDI Risk: {pharma.get('ddi_risk', 'N/A')}
Half-life: {pharma.get('half_life_estimate', 'N/A')}
pk_p1={pharma.get('pk_p1', 'N/A')} — {pharma.get('pk_p1_rationale', '')}
pk_p2={pharma.get('pk_p2', 'N/A')} — {pharma.get('pk_p2_rationale', '')}
pk_p3={pharma.get('pk_p3', 'N/A')} — {pharma.get('pk_p3_rationale', '')}

TASK: Integrate all advisories with your own Pass 1 assessment. Produce final consensus probabilities (final_p1, final_p2, final_p3). Follow the integration principles. Output Pass 2 JSON only. Do NOT include edward_score — it is computed server-side."""
    resp = llm.invoke([SystemMessage(content=EDWARD_PROMPT), HumanMessage(content=msg)])
    return parse_json(resp.content)


def run_v25_pipeline(smiles, target, indication):
    with ThreadPoolExecutor(max_workers=4) as executor:
        fut_salah = executor.submit(run_salah, smiles, target, indication)
        fut_toxi = executor.submit(run_toxi, smiles, target, indication)
        fut_pharma = executor.submit(run_pharma, smiles, target, indication)
        fut_pass1 = executor.submit(run_edward_pass1, smiles, target, indication)

        salah_data = fut_salah.result()
        toxi_data = fut_toxi.result()
        pharma_data = fut_pharma.result()
        pass1_data = fut_pass1.result()

    pass2_data = run_edward_pass2(smiles, target, indication, pass1_data, salah_data, toxi_data, pharma_data)

    fp1 = norm_prob(pass2_data.get("final_p1", 0.5))
    fp2 = norm_prob(pass2_data.get("final_p2", 0.3))
    fp3 = norm_prob(pass2_data.get("final_p3", 0.5))
    tcsp = round(fp1 * fp2 * fp3, 6)
    edward_score = tcsp_to_score(tcsp)

    return {
        "edward_score": edward_score,
        "rational": pass2_data.get("rational", ""),
        "metabolic_stability_estimate": pass2_data.get("metabolic_stability_estimate", ""),
        "potential_toxic_fragments": pass2_data.get("potential_toxic_fragments", ""),
        "structural_assessment": pass2_data.get("structural_assessment", pass1_data.get("structural_assessment", "")),
        "chem_p1": norm_prob(pass1_data.get("chem_p1")),
        "chem_p2": norm_prob(pass1_data.get("chem_p2")),
        "chem_p3": norm_prob(pass1_data.get("chem_p3")),
        "final_p1": fp1, "final_p1_rationale": pass2_data.get("final_p1_rationale", ""),
        "final_p2": fp2, "final_p2_rationale": pass2_data.get("final_p2_rationale", ""),
        "final_p3": fp3, "final_p3_rationale": pass2_data.get("final_p3_rationale", ""),
        "tcsp": tcsp,
        "salah_verdict": salah_data.get("salah_verdict", ""),
        "biological_rationale": salah_data.get("biological_rationale", ""),
        "mechanism_validation": salah_data.get("mechanism_validation", ""),
        "druggability_assessment": salah_data.get("druggability_assessment", ""),
        "bio_p1": norm_prob(salah_data.get("bio_p1")),
        "bio_p2": norm_prob(salah_data.get("bio_p2")),
        "bio_p3": norm_prob(salah_data.get("bio_p3")),
        "toxi_verdict": toxi_data.get("toxi_verdict", ""),
        "toxi_rationale": toxi_data.get("toxi_rationale", ""),
        "therapeutic_window": toxi_data.get("therapeutic_window", ""),
        "primary_tox_concern": toxi_data.get("primary_tox_concern", ""),
        "on_target_tox_risk": toxi_data.get("on_target_tox_risk", ""),
        "off_target_tox_risk": toxi_data.get("off_target_tox_risk", ""),
        "tox_p1": norm_prob(toxi_data.get("tox_p1")),
        "tox_p2": norm_prob(toxi_data.get("tox_p2")),
        "tox_p3": norm_prob(toxi_data.get("tox_p3")),
        "pharma_verdict": pharma_data.get("pharma_verdict", ""),
        "pharma_rationale": pharma_data.get("pharma_rationale", ""),
        "predicted_dose_range": pharma_data.get("predicted_dose_range", ""),
        "oral_feasibility": pharma_data.get("oral_feasibility", ""),
        "ddi_risk": pharma_data.get("ddi_risk", ""),
        "half_life_estimate": pharma_data.get("half_life_estimate", ""),
        "pk_p1": norm_prob(pharma_data.get("pk_p1")),
        "pk_p2": norm_prob(pharma_data.get("pk_p2")),
        "pk_p3": norm_prob(pharma_data.get("pk_p3")),
    }


BATCH_SIZE = 20


def clean_smiles(raw):
    """For combo drugs (dot-separated), take the first SMILES."""
    s = str(raw).split("<NL>")[0].strip()
    # Take first component if dot-separated combo
    if "." in s:
        parts = s.split(".")
        # Pick the longest SMILES (likely the active drug, not excipient)
        s = max(parts, key=len)
    return s


def clean_condition(raw):
    """Extract primary condition from pipe/NL-separated list."""
    s = str(raw).split("<NL>")[0].split("|")[0].strip()
    return s


def process_one(i, row):
    smiles = clean_smiles(row['SMILES'])
    target = str(row.get('Small Molecule Interventions', 'Unknown'))
    indication = clean_condition(row['Conditions'])
    name = target

    try:
        result = run_v25_pipeline(smiles, target, indication)
        tcsp = result.get('tcsp', 0)
        tcsp_pct = tcsp * 100 if isinstance(tcsp, float) and tcsp <= 1 else tcsp
        print(f"  [{i+1}] {name}  Score={result.get('edward_score', 'N/A')}  Bio={result.get('salah_verdict', 'N/A')}  Toxi={result.get('toxi_verdict', 'N/A')}  Pharma={result.get('pharma_verdict', 'N/A')}  TCSP={tcsp_pct:.2f}%", flush=True)
        return (i, result)
    except Exception as e:
        print(f"  [{i+1}] {name}  ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return (i, {"error": str(e)})


def main():
    df = pd.read_csv(INPUT_FILE)

    # Strip old prediction columns
    cols_to_drop = [c for c in PREDICTION_COLS if c in df.columns]
    df = df.drop(columns=cols_to_drop)
    print(f"Dropped {len(cols_to_drop)} old prediction columns", flush=True)

    start_index = 0
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            start_index = sum(1 for line in f)

    remaining = len(df) - start_index
    print(f"V25 Multi-Agent Pipeline — Eisai (n={len(df)}), resuming from {start_index}, batch_size={BATCH_SIZE}", flush=True)
    print(f"  {remaining} molecules remaining, ~{remaining // BATCH_SIZE + 1} batches", flush=True)

    for batch_start in range(start_index, len(df), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(df))
        batch_rows = [(i, df.iloc[i]) for i in range(batch_start, batch_end)]

        print(f"\n--- Batch [{batch_start+1}-{batch_end}] / {len(df)} ---", flush=True)

        with ThreadPoolExecutor(max_workers=BATCH_SIZE) as batch_executor:
            futures = {
                batch_executor.submit(process_one, i, row): i
                for i, row in batch_rows
            }
            batch_results = {}
            for fut in futures:
                idx, result = fut.result()
                batch_results[idx] = result

        with open(PROGRESS_FILE, "a") as f:
            for i in range(batch_start, batch_end):
                f.write(json.dumps(batch_results[i]) + "\n")

    results_list = []
    with open(PROGRESS_FILE, "r") as f:
        for line in f:
            results_list.append(json.loads(line))

    res_df = pd.DataFrame(results_list)
    res_df = res_df.rename(columns={
        "edward_score": "MedChem Score V25",
        "rational": "Rationale V25",
        "metabolic_stability_estimate": "Metabolic Stability V25",
        "potential_toxic_fragments": "Toxic Fragments V25",
        "structural_assessment": "Structural Assessment V25",
        "chem_p1": "Chem P1 V25", "chem_p2": "Chem P2 V25", "chem_p3": "Chem P3 V25",
        "final_p1": "Final P1 V25", "final_p1_rationale": "Final P1 Rationale V25",
        "final_p2": "Final P2 V25", "final_p2_rationale": "Final P2 Rationale V25",
        "final_p3": "Final P3 V25", "final_p3_rationale": "Final P3 Rationale V25",
        "tcsp": "TCSP V25",
        "salah_verdict": "Bio Verdict V25",
        "biological_rationale": "Biological Rationale V25",
        "mechanism_validation": "Mechanism Validation V25",
        "druggability_assessment": "Druggability V25",
        "bio_p1": "Bio P1 V25", "bio_p2": "Bio P2 V25", "bio_p3": "Bio P3 V25",
        "toxi_verdict": "Toxi Verdict V25",
        "toxi_rationale": "Toxi Rationale V25",
        "therapeutic_window": "Therapeutic Window V25",
        "primary_tox_concern": "Primary Tox Concern V25",
        "on_target_tox_risk": "On-Target Tox Risk V25",
        "off_target_tox_risk": "Off-Target Tox Risk V25",
        "tox_p1": "Tox P1 V25", "tox_p2": "Tox P2 V25", "tox_p3": "Tox P3 V25",
        "pharma_verdict": "Pharma Verdict V25",
        "pharma_rationale": "Pharma Rationale V25",
        "predicted_dose_range": "Predicted Dose V25",
        "oral_feasibility": "Oral Feasibility V25",
        "ddi_risk": "DDI Risk V25",
        "half_life_estimate": "Half-Life V25",
        "pk_p1": "PK P1 V25", "pk_p2": "PK P2 V25", "pk_p3": "PK P3 V25",
    })

    final_df = pd.concat([df.reset_index(drop=True), res_df.reset_index(drop=True)], axis=1)
    final_df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nDone! Output: {OUTPUT_FILE} ({len(final_df)} rows)", flush=True)


if __name__ == "__main__":
    main()
