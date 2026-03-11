"""Prediction logger — scores/verdicts only, no SMILES or targets stored."""

import json
import os
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
LOG_FILE = os.path.join(LOG_DIR, "predictions.jsonl")


def log_prediction(result):
    """Append a prediction log entry. No SMILES, target, or indication stored."""
    os.makedirs(LOG_DIR, exist_ok=True)

    overview = result.get("overview", {})
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "medchem_score": overview.get("medchem_score"),
        "tcsp": overview.get("tcsp"),
        "final_p1": overview.get("final_p1"),
        "final_p2": overview.get("final_p2"),
        "final_p3": overview.get("final_p3"),
        "bio_verdict": result.get("biology", {}).get("verdict"),
        "toxi_verdict": result.get("toxicology", {}).get("verdict"),
        "pharma_verdict": result.get("pharmacology", {}).get("verdict"),
        "metabolic_stability": overview.get("metabolic_stability"),
    }

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
