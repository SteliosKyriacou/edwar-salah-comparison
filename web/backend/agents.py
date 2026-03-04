"""Salah + Edward LLM agent logic (ported from app.py)."""

import json
import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

# ── Config ──────────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE, "..", ".."))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


# ── Load prompts once at import time ────────────────────────────────────────
def _load_prompts() -> tuple[str, str]:
    edward_path = os.path.join(
        PROJECT_ROOT, "Agents", "edward-medchem-rationalist", "INSTRUCTIONS.md"
    )
    salah_path = os.path.join(
        PROJECT_ROOT, "Agents", "salah-biological-rationalist", "INSTRUCTIONS.md"
    )
    with open(edward_path) as f:
        edward = f.read()
    with open(salah_path) as f:
        salah = f.read()
    return edward, salah


EDWARD_PROMPT, SALAH_PROMPT = _load_prompts()

llm = ChatGoogleGenerativeAI(model="gemini-3-pro-preview", temperature=0.0)


# ── Helpers ─────────────────────────────────────────────────────────────────
def parse_json_response(content) -> dict:
    """Extract JSON object from LLM response content."""
    if isinstance(content, list):
        content = "".join(
            str(c.get("text", "")) if isinstance(c, dict) else str(c) for c in content
        )
    clean = content.replace("```json", "").replace("```", "").strip()
    start = clean.find("{")
    end = clean.rfind("}") + 1
    return json.loads(clean[start:end])


def get_fragment_smarts(fragment_text: str, smiles: str) -> list[dict]:
    """Ask the LLM to convert toxic fragment descriptions into SMARTS."""
    prompt = f"""Given this molecule SMILES: {smiles}

And these toxic fragment descriptions: {fragment_text}

Return a JSON array of objects, one per fragment. Each object must have:
- "name": the fragment name (short label)
- "smarts": a valid SMARTS pattern that matches the toxic substructure in this specific molecule

Rules:
- The SMARTS MUST match a substructure in the given SMILES. Test mentally before returning.
- Use simple, robust SMARTS (prefer atom-by-atom patterns over complex recursive ones).
- If a fragment is vague (e.g., "lipophilic core"), skip it and do not include it.
- Return ONLY the JSON array, nothing else.

Example output:
[{{"name": "Thiophene", "smarts": "c1ccsc1"}}, {{"name": "Dimethylamine", "smarts": "CN(C)"}}]"""

    try:
        resp = llm.invoke([HumanMessage(content=prompt)])
        content = resp.content
        if isinstance(content, list):
            content = "".join(
                str(c.get("text", "")) if isinstance(c, dict) else str(c)
                for c in content
            )
        clean = content.replace("```json", "").replace("```", "").strip()
        start = clean.find("[")
        end = clean.rfind("]") + 1
        return json.loads(clean[start:end])
    except Exception:
        return []


# ── Agent Runners ───────────────────────────────────────────────────────────
def run_salah(smiles: str, target: str, indication: str, auxiliary: str = "") -> dict:
    """Run Salah — biological & clinical risk evaluation."""
    prompt = (
        f"Evaluate the biological risk: Target {target}, "
        f"Indication {indication} for molecule {smiles}."
    )
    if auxiliary:
        prompt += f"\n\nAdditional context from the user: {auxiliary}"
    resp = llm.invoke([SystemMessage(content=SALAH_PROMPT), HumanMessage(content=prompt)])
    return parse_json_response(resp.content)


def run_edward(
    smiles: str,
    target: str,
    indication: str,
    salah_data: dict,
    auxiliary: str = "",
) -> dict:
    """Run Edward — MedChem structural critique integrating Salah's advisory."""
    prompt = f"""
Molecule SMILES: {smiles}
Target Class: {target}
Indication: {indication}

BIO-ADVISORY FROM SALAH (Biological/Clinical Expert):
Verdict: {salah_data['salah_verdict']}
Biological Rationale: {salah_data['biological_rationale']}
Penalty for Historical Target Stigma: {salah_data['target_stigma_penalty']} points

TASK: Provide your final MedChem audit as Edward. Integrate the Biological Advisory above into your rationale and final Edward Score.
"""
    if auxiliary:
        prompt += f"\n\nAdditional context from the user: {auxiliary}"
    resp = llm.invoke([SystemMessage(content=EDWARD_PROMPT), HumanMessage(content=prompt)])
    return parse_json_response(resp.content)
