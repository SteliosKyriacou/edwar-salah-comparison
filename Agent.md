# 🛡️ AlphaForge AI Developer Agent Instructions

Welcome, Developer Agent! This document contains the definitive technical specifications, deployment instructions, and repository structure for **AlphaForge**. Use this guide to operate, refactor, and back up the platform with 100% precision.

---

## 🏗️ 1. Platform Architecture
AlphaForge is an enterprise-grade multi-agent AI pipeline and web application designed to predict the probability of clinical trial success for small-molecule drug candidates, and permanently log evaluations on a cryptographically certified temporal registry.

### Core Pipeline Steps:
1. **Parallel Domain Assessments (I/O-Bound):** 
   Concurrently invokes 4 expert prompts using **Google Gemini 3.1 Pro Preview** via LangChain and Vertex AI:
   *   🧬 **Biological-Rationalist:** Target validation depth, disease causality, druggability.
   *   ☠️ **Toxi-Predictive-Toxicologist:** Safety liabilities, structural alerts (like hERG), therapeutic window.
   *   💊 **Pharma-Clinical-Pharmacologist:** PK/PD feasibility, predicted dose, oral bioavailability, CYP/OATP DDI risks.
   *   🧪 **MedChem-Rationalist (Pass 1):** Blind, structure-only chemical critique (SMILES).
2. **Sequential Consensus Synthesis (Pass 2):** 
   The MedChem-Rationalist agent ingests all 4 expert advisories to synthesize a unified Consensus Rationale and output calibrated phase transition probabilities (`Final P1`, `Final P2`, `Final P3`).
3. **Deterministic Scoring:** 
   Computes Total Clinical Success Probability (TCSP) and the final Developability Risk Score (1 to 100, where lower = better):
   $$\text{TCSP} = P_1 \times P_2 \times P_3$$
   $$\text{Score} = \text{round}\left(100 \times \left(1 - \sqrt{\frac{\text{TCSP}}{0.40}}\right)\right)$$

---

## 🔒 2. Cryptographic Timestamp Registry (RFC 3161)
To ensure unforgeable, legally binding proof-of-existence:
1. **The Manifest (`.txt`):** When a prediction is done, the backend compiles all inputs, scores, and full rationales of all 4 agents into a standardized, deterministic plain-text **Prediction Manifest** (`AlphaForge_Prediction_Manifest.txt`).
2. **DigiCert TSR Token (`.tsr`):** The backend hashes this manifest into a secure **SHA-256 fingerprint**, packages it into an ASN.1 DER packet, and sends it to DigiCert's official TSA (`http://timestamp.digicert.com`). The returned Base64-encoded signed `.tsr` token is saved on the server.
3. **Audit Verification:** Anyone can download the manifest and the TSR certificate, and mathematically verify them together locally:
   ```bash
   openssl ts -verify -data V25_Prediction_Manifest.txt -in V25_TSA_Certificate.tsr -CAfile /etc/ssl/cert.pem
   ```

---

## ⚙️ 3. Tech Stack & Deployment Guide

*   **Frontend:** React 18 & Vite SPA. Serves `/` (Predictor), `/verify` (Public Verification), and `/usage` (Admin Dashboard). Includes a customized `@media print` CSS engine for printing crisp light-theme vector PDFs.
*   **Backend:** FastAPI (Python 3.11) with Uvicorn. Uses async event loops with threadpools for parallel agent execution.
*   **Database:** SQLite 3 in **WAL (Write-Ahead Log) mode** for high-concurrency read/write operations. Indexes on `tsa_fingerprint` ensure O(1) verify queries of **<0.5ms**.
*   **Backups:** Local and Google Cloud Storage (GCS) mirroring via `/home/stylianos_kyriacou/repos/edwar-salah-comparison/web/backup.sh`.

### Operational Commands:
*   **Model Selection:** Every run uses the model picked in the UI's *Evaluation Model* dropdown (default `gemini-3.1-pro-preview`). The catalog lives in `web/backend/models_catalog.py`; all transports go through `web/backend/llm.py`.
*   **Start/Restart Web App:** `bash web/restart.sh` (restarts backend on port `8101` and frontend on port `4103`).
*   **Stop Web App:** `bash web/stop.sh` (kills all active `uvicorn` and `vite` processes).
*   **Trigger GCS Backup:** `bash web/backup.sh` (archives database, keys, and configs, and uploads the `.tar.gz` to `gs://reneu001/timestamps-database-backup/`).

---

## 📂 4. Repository Layout
```text
.
├── Agent.md                         # This file (AI developer agent guidelines)
├── README.md                        # Product documentation & quickstart
├── Agents/                          # Domain-expert system prompts (separately stored!)
│   ├── biological-rationalist/      # Biology-Rationalist instructions
│   ├── toxi-predictive-toxicologist/# Toxi-Predictive-Toxicologist instructions
│   ├── pharma-clinical-pharmacologist/# Pharma-Clinical-Pharmacologist instructions
│   └── medchem-rationalist/          # MedChem-Rationalist instructions
└── web/                             # Web Application root
    ├── backend/                     # FastAPI ASGI backend source
    │   ├── main.py                  # Core REST API (SQLite, Semaphore, DigiCert, endpoints)
    │   ├── agents.py                # LangChain & Vertex AI model orchestration
    │   └── visits.py / logger.py    # Analytics loggers
    ├── frontend/                    # Vite + React 18 single page application
    │   ├── src/App.jsx              # Main App layout & Verification router
    │   ├── src/App.css              # Main dark stylesheet + @media print styles
    │   └── src/components/          # Visual modular cards & forms
    ├── backup.sh                    # Automated GCS shell backup script
    ├── config.json                  # Global server configuration parameters
    ├── keys.json                    # API Keys database with admin permissions
    └── restart.sh / stop.sh         # Deployment control scripts
```