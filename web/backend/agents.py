"""Agent logic — runs the 4-agent V25 pipeline."""

import os
import json
import math
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
load_dotenv(os.path.join(BASE, ".env"))

TCSP_CEIL = 0.40

# Post-hoc calibration coefficients (linear Platt scaling).
# Fitted on V25 Global dataset (N=394): actual_approval_rate = CALIB_SLOPE * TCSP + CALIB_INTERCEPT
# R²=0.875. The raw TCSP has excellent discrimination (monotonic ranking) but is
# compressed ~2.7x due to multiplicative anchoring (P1~0.65 × P2~0.30 × P3~0.58).
# This rescaling corrects the probability scale without changing the ranking.
CALIB_SLOPE = 2.67
CALIB_INTERCEPT = 0.08


def _load_prompt(name):
    path = os.path.join(BASE, "Agents", name, "INSTRUCTIONS.md")
    with open(path) as f:
        return f.read()


EDWARD_PROMPT = _load_prompt("medchem-rationalist")
SALAH_PROMPT = _load_prompt("biological-rationalist")
TOXI_PROMPT = _load_prompt("toxi-predictive-toxicologist")
PHARMA_PROMPT = _load_prompt("pharma-clinical-pharmacologist")

llm = ChatGoogleGenerativeAI(model="gemini-3-pro-preview", temperature=0.0)


def parse_json(content):
    if isinstance(content, list):
        content = "".join(
            str(c.get("text", "")) if isinstance(c, dict) else str(c)
            for c in content
        )
    clean = content.replace("```json", "").replace("```", "").strip()
    start = clean.find("{")
    end = clean.rfind("}") + 1
    return json.loads(clean[start:end])


def norm_prob(p):
    if p is None:
        return 0.5
    p = float(p)
    if p > 1:
        p = p / 100
    return max(0.0, min(1.0, p))


def calibrate_tcsp(tcsp):
    """Post-hoc linear calibration: maps compressed TCSP to calibrated probability."""
    return max(0.0, min(1.0, CALIB_SLOPE * tcsp + CALIB_INTERCEPT))


def tcsp_to_score(tcsp):
    score = round(100 * (1 - math.sqrt(tcsp / TCSP_CEIL)))
    return max(1, min(100, score))


def run_salah(smiles, target, indication, auxiliary=""):
    ctx = f" Additional context: {auxiliary}" if auxiliary else ""
    msg = f"Evaluate the biological feasibility: Target {target}, Indication {indication} for molecule {smiles}.{ctx}"
    resp = llm.invoke([SystemMessage(content=SALAH_PROMPT), HumanMessage(content=msg)])
    return parse_json(resp.content)


def run_toxi(smiles, target, indication, auxiliary=""):
    ctx = f" Additional context: {auxiliary}" if auxiliary else ""
    msg = f"Evaluate the safety liabilities: Target {target}, Indication {indication} for molecule {smiles}.{ctx}"
    resp = llm.invoke([SystemMessage(content=TOXI_PROMPT), HumanMessage(content=msg)])
    return parse_json(resp.content)


def run_pharma(smiles, target, indication, auxiliary=""):
    ctx = f" Additional context: {auxiliary}" if auxiliary else ""
    msg = f"Evaluate the PK/PD feasibility: Target {target}, Indication {indication} for molecule {smiles}.{ctx}"
    resp = llm.invoke([SystemMessage(content=PHARMA_PROMPT), HumanMessage(content=msg)])
    return parse_json(resp.content)


def run_edward_pass1(smiles, target, indication, auxiliary=""):
    ctx = f"\nAdditional Context: {auxiliary}" if auxiliary else ""
    msg = f"""PASS 1 — Blind Structural Assessment (no advisory data).

Molecule SMILES: {smiles}
Target Class: {target}
Indication: {indication}{ctx}

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


def run_pipeline(smiles, target, indication, auxiliary=""):
    """Run the full 4-agent V25 pipeline. Returns structured result dict."""
    with ThreadPoolExecutor(max_workers=4) as executor:
        fut_salah = executor.submit(run_salah, smiles, target, indication, auxiliary)
        fut_toxi = executor.submit(run_toxi, smiles, target, indication, auxiliary)
        fut_pharma = executor.submit(run_pharma, smiles, target, indication, auxiliary)
        fut_pass1 = executor.submit(run_edward_pass1, smiles, target, indication, auxiliary)

        salah_data = fut_salah.result()
        toxi_data = fut_toxi.result()
        pharma_data = fut_pharma.result()
        pass1_data = fut_pass1.result()

    pass2_data = run_edward_pass2(
        smiles, target, indication, pass1_data, salah_data, toxi_data, pharma_data
    )

    fp1 = norm_prob(pass2_data.get("final_p1", 0.5))
    fp2 = norm_prob(pass2_data.get("final_p2", 0.3))
    fp3 = norm_prob(pass2_data.get("final_p3", 0.5))
    tcsp_raw = round(fp1 * fp2 * fp3, 6)
    tcsp_calibrated = round(calibrate_tcsp(tcsp_raw), 4)
    score = tcsp_to_score(tcsp_raw)

    return {
        "overview": {
            "medchem_score": score,
            "tcsp_raw": tcsp_raw,
            "tcsp_raw_pct": round(tcsp_raw * 100, 2),
            "tcsp_calibrated": tcsp_calibrated,
            "tcsp_calibrated_pct": round(tcsp_calibrated * 100, 1),
            "final_p1": fp1,
            "final_p2": fp2,
            "final_p3": fp3,
            "final_p1_rationale": pass2_data.get("final_p1_rationale", ""),
            "final_p2_rationale": pass2_data.get("final_p2_rationale", ""),
            "final_p3_rationale": pass2_data.get("final_p3_rationale", ""),
            "rationale": pass2_data.get("rational", ""),
            "metabolic_stability": pass2_data.get("metabolic_stability_estimate", ""),
            "toxic_fragments": pass2_data.get("potential_toxic_fragments", ""),
            "structural_assessment": pass2_data.get(
                "structural_assessment",
                pass1_data.get("structural_assessment", ""),
            ),
        },
        "medchem": {
            "agent": "MedChem-Rationalist",
            "icon": "flask",
            "pass1": pass1_data,
            "pass2": pass2_data,
            "chem_p1": norm_prob(pass1_data.get("chem_p1")),
            "chem_p2": norm_prob(pass1_data.get("chem_p2")),
            "chem_p3": norm_prob(pass1_data.get("chem_p3")),
        },
        "biology": {
            "agent": "Biological-Rationalist",
            "icon": "dna",
            "verdict": salah_data.get("salah_verdict", ""),
            "rationale": salah_data.get("biological_rationale", ""),
            "mechanism_validation": salah_data.get("mechanism_validation", ""),
            "druggability": salah_data.get("druggability_assessment", ""),
            "bio_p1": norm_prob(salah_data.get("bio_p1")),
            "bio_p2": norm_prob(salah_data.get("bio_p2")),
            "bio_p3": norm_prob(salah_data.get("bio_p3")),
            "bio_p1_rationale": salah_data.get("bio_p1_rationale", ""),
            "bio_p2_rationale": salah_data.get("bio_p2_rationale", ""),
            "bio_p3_rationale": salah_data.get("bio_p3_rationale", ""),
            "raw": salah_data,
        },
        "toxicology": {
            "agent": "Toxi-Predictive-Toxicologist",
            "icon": "skull",
            "verdict": toxi_data.get("toxi_verdict", ""),
            "rationale": toxi_data.get("toxi_rationale", ""),
            "therapeutic_window": toxi_data.get("therapeutic_window", ""),
            "primary_concern": toxi_data.get("primary_tox_concern", ""),
            "on_target_risk": toxi_data.get("on_target_tox_risk", ""),
            "off_target_risk": toxi_data.get("off_target_tox_risk", ""),
            "tox_p1": norm_prob(toxi_data.get("tox_p1")),
            "tox_p2": norm_prob(toxi_data.get("tox_p2")),
            "tox_p3": norm_prob(toxi_data.get("tox_p3")),
            "tox_p1_rationale": toxi_data.get("tox_p1_rationale", ""),
            "tox_p2_rationale": toxi_data.get("tox_p2_rationale", ""),
            "tox_p3_rationale": toxi_data.get("tox_p3_rationale", ""),
            "raw": toxi_data,
        },
        "pharmacology": {
            "agent": "Pharma-Clinical-Pharmacologist",
            "icon": "pills",
            "verdict": pharma_data.get("pharma_verdict", ""),
            "rationale": pharma_data.get("pharma_rationale", ""),
            "predicted_dose": pharma_data.get("predicted_dose_range", ""),
            "oral_feasibility": pharma_data.get("oral_feasibility", ""),
            "ddi_risk": pharma_data.get("ddi_risk", ""),
            "half_life": pharma_data.get("half_life_estimate", ""),
            "pk_p1": norm_prob(pharma_data.get("pk_p1")),
            "pk_p2": norm_prob(pharma_data.get("pk_p2")),
            "pk_p3": norm_prob(pharma_data.get("pk_p3")),
            "pk_p1_rationale": pharma_data.get("pk_p1_rationale", ""),
            "pk_p2_rationale": pharma_data.get("pk_p2_rationale", ""),
            "pk_p3_rationale": pharma_data.get("pk_p3_rationale", ""),
            "raw": pharma_data,
        },
    }
