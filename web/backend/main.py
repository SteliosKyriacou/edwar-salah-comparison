"""FastAPI backend — Will Your Drug Succeed in the Clinic?"""

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agents import run_salah, run_edward, get_fragment_smarts
from molecule import draw_molecule_with_highlights
from logger import log_prediction

app = FastAPI(title="Edward x Salah — Drug Success Predictor")

# ── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Models ──────────────────────────────────────────────────────────────────
class AnalyzeRequest(BaseModel):
    smiles: str
    target: str
    indication: str
    auxiliary: str = ""


class AnalyzeResponse(BaseModel):
    edward: dict
    salah: dict
    molecule_image: str | None = None
    fragment_matches: list[dict] = []


# ── Routes ──────────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    if not req.smiles or not req.target or not req.indication:
        raise HTTPException(status_code=400, detail="smiles, target, and indication are required.")

    # Step 1: Salah — biological & clinical risk
    try:
        salah_data = run_salah(req.smiles, req.target, req.indication, req.auxiliary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Salah error: {e}")

    # Step 2: Edward — MedChem critique with Salah's advisory
    try:
        edward_data = run_edward(req.smiles, req.target, req.indication, salah_data, req.auxiliary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Edward error: {e}")

    # Step 3: Fragment highlighting
    fragments = edward_data.get("potential_toxic_fragments", "None identified")
    if isinstance(fragments, list):
        fragments_text = ", ".join(str(f) for f in fragments)
    else:
        fragments_text = str(fragments)

    smarts_list = get_fragment_smarts(fragments_text, req.smiles)
    mol_image, fragment_matches = draw_molecule_with_highlights(req.smiles, smarts_list)

    # Step 4: Recalculate TCSP — LLM often gets the multiplication wrong
    p1 = edward_data.get("p1_prob", 0)
    p2 = edward_data.get("p2_prob", 0)
    p3 = edward_data.get("p3_prob", 0)
    # Normalise to 0-1 if given as percentages
    p1 = p1 / 100 if p1 > 1 else p1
    p2 = p2 / 100 if p2 > 1 else p2
    p3 = p3 / 100 if p3 > 1 else p3
    edward_data["tcsp"] = round(p1 * p2 * p3, 6)

    # Step 5: Log prediction (scores only — no SMILES/target)
    log_prediction(edward_data, salah_data)

    return AnalyzeResponse(
        edward=edward_data,
        salah=salah_data,
        molecule_image=mol_image,
        fragment_matches=fragment_matches,
    )


# ── Serve benchmark figures ──────────────────────────────────────────────────
FIGURES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "Salah", "global")
if os.path.isdir(FIGURES_DIR):
    app.mount("/api/figures", StaticFiles(directory=FIGURES_DIR), name="figures")

# ── Serve frontend static build in production ───────────────────────────────
FRONTEND_BUILD = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(FRONTEND_BUILD):
    app.mount("/", StaticFiles(directory=FRONTEND_BUILD, html=True), name="frontend")
