"""V25 Multi-Agent Pipeline — Generic CLI entry point.

Usage:
    python src/main.py input.csv --smiles isomeric --target target_class --indication therapeutic_area
    python src/main.py input.csv --smiles SMILES --target Target --indication Indication -o results.csv
"""

import pandas as pd
import json
import os
import sys
import math
import time
import argparse
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(BASE, ".env"))

TCSP_CEIL = 0.40


def load_agent_prompt(name):
    path = os.path.join(BASE, "Agents", name, "INSTRUCTIONS.md")
    with open(path) as f:
        return f.read()


EDWARD_PROMPT = load_agent_prompt("medchem-rationalist")
SALAH_PROMPT = load_agent_prompt("biological-rationalist")
TOXI_PROMPT = load_agent_prompt("toxi-predictive-toxicologist")
PHARMA_PROMPT = load_agent_prompt("pharma-clinical-pharmacologist")

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
        "MedChem Score V25": edward_score,
        "Rationale V25": pass2_data.get("rational", ""),
        "Metabolic Stability V25": pass2_data.get("metabolic_stability_estimate", ""),
        "Toxic Fragments V25": pass2_data.get("potential_toxic_fragments", ""),
        "Structural Assessment V25": pass2_data.get("structural_assessment", pass1_data.get("structural_assessment", "")),
        "Chem P1 V25": norm_prob(pass1_data.get("chem_p1")),
        "Chem P2 V25": norm_prob(pass1_data.get("chem_p2")),
        "Chem P3 V25": norm_prob(pass1_data.get("chem_p3")),
        "Final P1 V25": fp1, "Final P1 Rationale V25": pass2_data.get("final_p1_rationale", ""),
        "Final P2 V25": fp2, "Final P2 Rationale V25": pass2_data.get("final_p2_rationale", ""),
        "Final P3 V25": fp3, "Final P3 Rationale V25": pass2_data.get("final_p3_rationale", ""),
        "TCSP V25": tcsp,
        "Bio Verdict V25": salah_data.get("salah_verdict", ""),
        "Biological Rationale V25": salah_data.get("biological_rationale", ""),
        "Mechanism Validation V25": salah_data.get("mechanism_validation", ""),
        "Druggability V25": salah_data.get("druggability_assessment", ""),
        "Bio P1 V25": norm_prob(salah_data.get("bio_p1")),
        "Bio P2 V25": norm_prob(salah_data.get("bio_p2")),
        "Bio P3 V25": norm_prob(salah_data.get("bio_p3")),
        "Toxi Verdict V25": toxi_data.get("toxi_verdict", ""),
        "Toxi Rationale V25": toxi_data.get("toxi_rationale", ""),
        "Therapeutic Window V25": toxi_data.get("therapeutic_window", ""),
        "Primary Tox Concern V25": toxi_data.get("primary_tox_concern", ""),
        "On-Target Tox Risk V25": toxi_data.get("on_target_tox_risk", ""),
        "Off-Target Tox Risk V25": toxi_data.get("off_target_tox_risk", ""),
        "Tox P1 V25": norm_prob(toxi_data.get("tox_p1")),
        "Tox P2 V25": norm_prob(toxi_data.get("tox_p2")),
        "Tox P3 V25": norm_prob(toxi_data.get("tox_p3")),
        "Pharma Verdict V25": pharma_data.get("pharma_verdict", ""),
        "Pharma Rationale V25": pharma_data.get("pharma_rationale", ""),
        "Predicted Dose V25": pharma_data.get("predicted_dose_range", ""),
        "Oral Feasibility V25": pharma_data.get("oral_feasibility", ""),
        "DDI Risk V25": pharma_data.get("ddi_risk", ""),
        "Half-Life V25": pharma_data.get("half_life_estimate", ""),
        "PK P1 V25": norm_prob(pharma_data.get("pk_p1")),
        "PK P2 V25": norm_prob(pharma_data.get("pk_p2")),
        "PK P3 V25": norm_prob(pharma_data.get("pk_p3")),
    }


def main():
    parser = argparse.ArgumentParser(
        description="V25 Multi-Agent Pipeline — Run on any CSV file."
    )
    parser.add_argument("input", help="Path to input CSV file")
    parser.add_argument("--smiles", required=True, help="Column name containing SMILES strings")
    parser.add_argument("--target", required=True, help="Column name containing target class")
    parser.add_argument("--indication", required=True, help="Column name containing indication/therapeutic area")
    parser.add_argument("-o", "--output", help="Output CSV path (default: <input>_V25.csv)")
    parser.add_argument("--name", help="Column name for compound name (for progress display)")
    parser.add_argument("--batch-size", type=int, default=10, help="Molecules to process concurrently (default: 10)")
    args = parser.parse_args()

    input_path = os.path.abspath(args.input)
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(input_path)
    for col in [args.smiles, args.target, args.indication]:
        if col not in df.columns:
            print(f"Error: column '{col}' not found in {input_path}", file=sys.stderr)
            print(f"Available columns: {', '.join(df.columns)}", file=sys.stderr)
            sys.exit(1)

    if args.output:
        output_path = os.path.abspath(args.output)
    else:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_V25{ext}"

    progress_path = output_path.replace(".csv", "_progress.jsonl")
    batch_size = args.batch_size
    smiles_col = args.smiles
    target_col = args.target
    indication_col = args.indication
    name_col = args.name

    start_index = 0
    if os.path.exists(progress_path):
        with open(progress_path, 'r') as f:
            start_index = sum(1 for line in f)

    remaining = len(df) - start_index
    print(f"V25 Multi-Agent Pipeline (n={len(df)}), resuming from {start_index}, batch_size={batch_size}", flush=True)
    print(f"  Input:  {input_path}", flush=True)
    print(f"  Output: {output_path}", flush=True)
    print(f"  Columns: SMILES={smiles_col}, Target={target_col}, Indication={indication_col}", flush=True)
    print(f"  {remaining} molecules remaining, ~{remaining // batch_size + 1} batches", flush=True)

    def process_one(i, row):
        smiles = str(row[smiles_col])
        target = str(row[target_col])
        indication = str(row[indication_col])
        name = str(row[name_col]) if name_col and name_col in df.columns else f"row {i}"

        try:
            result = run_v25_pipeline(smiles, target, indication)
            score = result.get("MedChem Score V25", "N/A")
            bio = result.get("Bio Verdict V25", "N/A")
            toxi = result.get("Toxi Verdict V25", "N/A")
            pharma = result.get("Pharma Verdict V25", "N/A")
            tcsp = result.get("TCSP V25", 0)
            tcsp_pct = tcsp * 100 if isinstance(tcsp, float) and tcsp <= 1 else tcsp
            print(f"  [{i+1}] {name}  Score={score}  Bio={bio}  Toxi={toxi}  Pharma={pharma}  TCSP={tcsp_pct:.2f}%", flush=True)
            return (i, result)
        except Exception as e:
            print(f"  [{i+1}] {name}  ERROR: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return (i, {"error": str(e)})

    for batch_start in range(start_index, len(df), batch_size):
        batch_end = min(batch_start + batch_size, len(df))
        batch_rows = [(i, df.iloc[i]) for i in range(batch_start, batch_end)]

        print(f"\n--- Batch [{batch_start+1}-{batch_end}] / {len(df)} ---", flush=True)

        with ThreadPoolExecutor(max_workers=batch_size) as batch_executor:
            futures = {
                batch_executor.submit(process_one, i, row): i
                for i, row in batch_rows
            }
            batch_results = {}
            for fut in futures:
                idx, result = fut.result()
                batch_results[idx] = result

        with open(progress_path, "a") as f:
            for i in range(batch_start, batch_end):
                f.write(json.dumps(batch_results[i]) + "\n")

    results_list = []
    with open(progress_path, "r") as f:
        for line in f:
            results_list.append(json.loads(line))

    res_df = pd.DataFrame(results_list)
    final_df = pd.concat([df.reset_index(drop=True), res_df.reset_index(drop=True)], axis=1)
    final_df.to_csv(output_path, index=False)
    print(f"\nDone! Output: {output_path} ({len(final_df)} rows)", flush=True)


if __name__ == "__main__":
    main()
