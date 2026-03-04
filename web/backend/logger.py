"""Prediction logger — scores/verdicts only, NO SMILES or targets stored."""

import json
import os
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
LOG_FILE = os.path.join(LOG_DIR, "predictions.jsonl")


def log_prediction(edward_data: dict, salah_data: dict) -> None:
    """Append a single prediction entry (no SMILES, no target, no indication)."""
    os.makedirs(LOG_DIR, exist_ok=True)

    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "edward_score": edward_data.get("edward_score"),
        "salah_verdict": salah_data.get("salah_verdict"),
        "tcsp": edward_data.get("tcsp"),
        "p1_prob": edward_data.get("p1_prob"),
        "p2_prob": edward_data.get("p2_prob"),
        "p3_prob": edward_data.get("p3_prob"),
        "metabolic_stability": edward_data.get("metabolic_stability_estimate"),
        "clinical_attrition_risk": salah_data.get("clinical_attrition_risk"),
    }

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
