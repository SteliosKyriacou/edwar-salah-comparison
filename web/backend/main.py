"""FastAPI backend — Will Your Drug Succeed in the Clinic?"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os

from agents import run_pipeline
from logger import log_prediction

app = FastAPI(title="Drug Success Predictor", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    smiles: str
    target: str
    indication: str
    auxiliary: str = ""


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest):
    if not req.smiles.strip():
        raise HTTPException(400, "SMILES is required")
    if not req.target.strip():
        raise HTTPException(400, "Target is required")
    if not req.indication.strip():
        raise HTTPException(400, "Indication is required")

    try:
        result = run_pipeline(
            req.smiles.strip(),
            req.target.strip(),
            req.indication.strip(),
            req.auxiliary.strip(),
        )
    except Exception as e:
        raise HTTPException(500, f"Pipeline error: {e}")

    log_prediction(result)
    return result


# Serve frontend static build in production
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
