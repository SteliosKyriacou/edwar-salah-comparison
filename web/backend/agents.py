"""Agent logic — runs the 4-agent AlphaForge pipeline."""

import os
import json
import math
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from langchain_google_vertexai import ChatVertexAI
from langchain_core.messages import SystemMessage, HumanMessage

from web_search import run_web_search

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
load_dotenv(os.path.join(BASE, ".env"))

# Vertex AI configuration (auth via Application Default Credentials).
PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "ai-pipeline-461818")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")

TCSP_CEIL = 0.40


def _load_prompt(agent_name):
    path = os.path.join(BASE, "Agent.md")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Consolidated prompt file Agent.md not found at {path}")
    with open(path, "r") as f:
        content = f.read()

    # Find section starting with the agent name
    header = f"# {agent_name}"
    start_idx = content.find(header)
    if start_idx == -1:
        raise ValueError(f"Could not find instructions for {agent_name} in Agent.md")

    # The instructions start after the header line
    start_idx = content.find("\n", start_idx) + 1

    # Find next header to determine end index
    next_idx = content.find("\n# ", start_idx)
    if next_idx == -1:
        return content[start_idx:].strip()
    return content[start_idx:next_idx].strip()


MEDCHEM_PROMPT = _load_prompt("MedChem-Rationalist")
BIO_PROMPT = _load_prompt("Biological-Rationalist")
TOXI_PROMPT = _load_prompt("Toxi-Predictive-Toxicologist")
PHARMA_PROMPT = _load_prompt("Pharma-Clinical-Pharmacologist")

llm = ChatVertexAI(
    model="gemini-3.1-pro-preview",
    temperature=0.0,
    project=PROJECT,
    location=LOCATION,
)


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


def tcsp_to_score(tcsp):
    score = round(100 * (1 - math.sqrt(tcsp / TCSP_CEIL)))
    return max(1, min(100, score))


def run_biology(smiles, target, indication, auxiliary=""):
    ctx = f" Additional context: {auxiliary}" if auxiliary else ""
    msg = f"Evaluate the biological feasibility: Target {target}, Indication {indication} for molecule {smiles}.{ctx}"
    resp = llm.invoke([SystemMessage(content=BIO_PROMPT), HumanMessage(content=msg)])
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


def run_medchem_pass1(smiles, target, indication, auxiliary=""):
    ctx = f"\nAdditional Context: {auxiliary}" if auxiliary else ""
    msg = f"""PASS 1 — Blind Structural Assessment (no advisory data).

Molecule SMILES: {smiles}
Target Class: {target}
Indication: {indication}{ctx}

Provide your structural critique as Pass 1. Output JSON only."""
    resp = llm.invoke([SystemMessage(content=MEDCHEM_PROMPT), HumanMessage(content=msg)])
    return parse_json(resp.content)


def run_medchem_pass2(smiles, target, indication, pass1, bio_data, toxi_data, pharma_data):
    msg = f"""PASS 2 — Advisory Integration.

Molecule SMILES: {smiles}
Target Class: {target}
Indication: {indication}

YOUR PASS 1 STRUCTURAL ASSESSMENT:
{json.dumps(pass1, indent=2)}

BIOLOGICAL-RATIONALIST ADVISORY (Biology):
Verdict: {bio_data.get('bio_verdict', 'N/A')}
Rationale: {bio_data.get('biological_rationale', 'N/A')}
Mechanism Validation: {bio_data.get('mechanism_validation', 'N/A')}
Druggability: {bio_data.get('druggability_assessment', 'N/A')}
bio_p1={bio_data.get('bio_p1', 'N/A')} — {bio_data.get('bio_p1_rationale', '')}
bio_p2={bio_data.get('bio_p2', 'N/A')} — {bio_data.get('bio_p2_rationale', '')}
bio_p3={bio_data.get('bio_p3', 'N/A')} — {bio_data.get('bio_p3_rationale', '')}

TOXI ADVISORY (Toxicology):
Verdict: {toxi_data.get('toxi_verdict', 'N/A')}
Rationale: {toxi_data.get('toxi_rationale', 'N/A')}
Therapeutic Window: {toxi_data.get('therapeutic_window', 'N/A')}
Primary Concern: {toxi_data.get('primary_tox_concern', 'N/A')}
On-Target Risk: {toxi_data.get('on_target_tox_risk', 'N/A')}
Off-Target Risk: {toxi_data.get('off_target_tox_risk', 'N/A')}
tox_p1={toxi_data.get('tox_p1', 'N/A')} — {toxi_data.get('tox_p1_rationale', '')}
tox_p2={toxi_data.get('tox_p2', 'N/A')} — {toxi_data.get('tox_p2_rationale', '')}
tox_p3={toxi_data.get('tox_p3', 'N/A')} — {toxi_data.get('tox_p3_rationale', '')}

PHARMA ADVISORY (Pharmacology):
Verdict: {pharma_data.get('pharma_verdict', 'N/A')}
Rationale: {pharma_data.get('pharma_rationale', 'N/A')}
Predicted Dose: {pharma_data.get('predicted_dose_range', 'N/A')}
Oral Feasibility: {pharma_data.get('oral_feasibility', 'N/A')}
DDI Risk: {pharma_data.get('ddi_risk', 'N/A')}
Half-life: {pharma_data.get('half_life_estimate', 'N/A')}
pk_p1={pharma.get('pk_p1', 'N/A')} — {pharma.get('pk_p1_rationale', '')}
pk_p2={pharma.get('pk_p2', 'N/A')} — {pharma.get('pk_p2_rationale', '')}
pk_p3={pharma.get('pk_p3', 'N/A')} — {pharma.get('pk_p3_rationale', '')}

TASK: Integrate all advisories with your own Pass 1 assessment. Produce final consensus probabilities (final_p1, final_p2, final_p3). Follow the integration principles. Output Pass 2 JSON only. Do NOT include medchem_score — it is computed server-side."""
    resp = llm.invoke([SystemMessage(content=MEDCHEM_PROMPT), HumanMessage(content=msg)])
    return parse_json(resp.content)


def run_pipeline(smiles, target, indication, auxiliary="", web_search=False):
    """Run the full 4-agent AlphaForge pipeline. Returns structured result dict.

    If web_search is True, a grounded literature search is run first and its
    validated summary is appended to the auxiliary context fed to every agent.
    """
    web_search_result = None
    if web_search:
        ws = run_web_search(smiles, target, indication, auxiliary)
        if ws and ws.get("summary"):
            evidence = (
                "Validated web-search literature summary (references provided):\n"
                + ws["summary"]
            )
            auxiliary = f"{auxiliary}\n\n{evidence}" if auxiliary else evidence
        web_search_result = ws

    with ThreadPoolExecutor(max_workers=4) as executor:
        fut_bio = executor.submit(run_biology, smiles, target, indication, auxiliary)
        fut_toxi = executor.submit(run_toxi, smiles, target, indication, auxiliary)
        fut_pharma = executor.submit(run_pharma, smiles, target, indication, auxiliary)
        fut_pass1 = executor.submit(run_medchem_pass1, smiles, target, indication, auxiliary)

        bio_data = fut_bio.result()
        toxi_data = fut_toxi.result()
        pharma_data = fut_pharma.result()
        pass1_data = fut_pass1.result()

    pass2_data = run_medchem_pass2(
        smiles, target, indication, pass1_data, bio_data, toxi_data, pharma_data
    )

    fp1 = norm_prob(pass2_data.get("final_p1", 0.5))
    fp2 = norm_prob(pass2_data.get("final_p2", 0.3))
    fp3 = norm_prob(pass2_data.get("final_p3", 0.5))
    tcsp = round(fp1 * fp2 * fp3, 6)
    score = tcsp_to_score(tcsp)

    return {
        "web_search": web_search_result,
        "overview": {
            "medchem_score": score,
            "tcsp": tcsp,
            "tcsp_pct": round(tcsp * 100, 2),
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
            "verdict": bio_data.get("bio_verdict", ""),
            "rationale": bio_data.get("biological_rationale", ""),
            "mechanism_validation": bio_data.get("mechanism_validation", ""),
            "druggability": bio_data.get("druggability_assessment", ""),
            "bio_p1": norm_prob(bio_data.get("bio_p1")),
            "bio_p2": norm_prob(bio_data.get("bio_p2")),
            "bio_p3": norm_prob(bio_data.get("bio_p3")),
            "bio_p1_rationale": bio_data.get("bio_p1_rationale", ""),
            "bio_p2_rationale": bio_data.get("bio_p2_rationale", ""),
            "bio_p3_rationale": bio_data.get("bio_p3_rationale", ""),
            "raw": bio_data,
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
