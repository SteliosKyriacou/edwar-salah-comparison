# 🛡️ AlphaForge: Multi-Agent Clinical Attrition Predictor & Timestamp Registry

AlphaForge is an enterprise-grade, multi-agent AI pipeline and web application designed to predict the probability of clinical trial success for small-molecule drug candidates, and permanently log evaluations on a cryptographically certified temporal registry.

To prevent data tampering and provide institutional-grade due diligence, every prediction is hashed into a secure **SHA-256 fingerprint**, compiled into a plain-text manifest, and cryptographically signed/certified live by **DigiCert's Trusted Time-Stamp Authority (TSA)** under the globally recognized **RFC 3161 standard**.

---

## 🏗️ Core Architecture (The AlphaForge Pipeline)
The prediction pipeline simulates a professional pharmaceutical due diligence panel by orchestrating **4 specialized, domain-expert LLM agents** in parallel, followed by a sequential consensus synthesis step.

### Step 1: Parallel Domain Assessments (I/O-Bound)
The pipeline concurrently invokes 4 expert prompts using **Google Gemini 3.1 Pro Preview**:
*   **🧬 Biological-Rationalist:** Analyzes target biology, disease causal linkage, clinical mechanism validation, and druggability. Outputs `bio_p1/p2/p3` transition probabilities and a categorical verdict (`ELITE`, `CAUTION`, `TERMINATE`).
*   **☠️ Toxi-Predictive-Toxicologist:** Scans for off-target liabilities, structural alerts (like hERG pharmacophores), therapeutic window, and chronic organ toxicity. Outputs `tox_p1/p2/p3` probabilities and a verdict (`CLEAN`, `MANAGEABLE`, `NARROW`, `TOXIC`).
*   **💊 Pharma-Clinical-Pharmacologist:** Assesses PK/PD feasibility, predicted dosing, oral bioavailability, half-life, and CYP/OATP drug-drug interaction (DDI) risks. Outputs `pk_p1/p2/p3` probabilities and a verdict (`FAVORABLE`, `ADEQUATE`, `CHALLENGING`, `IMPRACTICAL`).
*   **🧪 MedChem-Rationalist (Pass 1):** Performs a blind, structure-only critique of the chemical scaffold (SMILES), evaluating metabolic soft spots, lipophilic efficiency, and synthetic developability. Outputs `chem_p1/p2/p3` probabilities.

### Step 2: Sequential Consensus Synthesis (Pass 2)
The MedChem-Rationalist agent ingests all 4 expert advisories as context to synthesize a unified, cross-disciplinary narrative, outputting calibrated consensus phase transition probabilities (`Final P1`, `Final P2`, `Final P3`).

### Step 3: Deterministic Scoring
The server applies a strict mathematical formula to compute the final success probability and developability risk:
*   **TCSP (Total Clinical Success Probability):** 
    $$\text{TCSP} = \text{Final P1} \times \text{Final P2} \times \text{Final P3}$$
*   **MedChem Score AlphaForge:** Calibrated against a historical benchmark database of 393 approved and failed drugs, mapped on a scale from 1 (lowest clinical risk/best) to 100 (highest risk/worst):
    $$\text{MedChem Score} = \text{round}\left(100 \times \left(1 - \sqrt{\frac{\text{TCSP}}{0.40}}\right)\right)$$

---

## 🔒 Cryptographic Trust & Verification Portal
To allow VCs, partners, and regulators to verify that a prediction report is authentic, has not been tampered with, and existed on a specific date, the system integrates a **Zero-Trust Registry**:

### The Verification Manifest (`.txt`)
When a prediction succeeds, the server compiles all input data, scores, verdicts, and full-prose agent rationales into a standardized, deterministic plain-text **Prediction Manifest** (`AlphaForge_Prediction_Manifest.txt`).

### The RFC 3161 Timestamp (`.tsr`)
The Python backend hashes the manifest into a **SHA-256 fingerprint** and sends it via a custom, native ASN.1 DER packet encoder to **DigiCert's Time-Stamp Authority (TSA)**. DigiCert signs the hash with atomic-clock time, returning a cryptographically sealed **`.tsr` signature token**.

### The Public Verification Portal (`/verify`)
*   **Path:** `http://localhost:4003/verify`
*   A third party can paste the SHA-256 fingerprint (or click a shared link) to instantly fetch the complete, original prediction results from the server's database and render the full visual dashboard.
*   It provides direct downloads for the original **Manifest (`.txt`)** and **DigiCert Signature (`.tsr`)**.
*   Auditors can verify the files locally in their own terminal using standard public-key cryptography:
    ```bash
    openssl ts -verify -data V25_Prediction_Manifest.txt -in V25_TSA_Certificate.tsr -CAfile /etc/ssl/cert.pem
    ```
    If successful, OpenSSL prints **`Verification: OK`**, certifying total authenticity.

---

## ⚙️ Quick Start

### 1. Installation
Ensure you have Python 3.11 and Node.js configured on your server, then install dependencies:
```bash
# Install backend dependencies
conda create -n edwar-salah python=3.11 -y
conda run -n edwar-salah pip install pandas scikit-learn matplotlib langchain-core langchain-google-vertexai google-genai python-dotenv fastapi uvicorn pydantic

# Install frontend dependencies (Vite + React 18)
cd web/frontend
npm install
npm run build
cd ../..
```

### 2. Launch the Application
Start both the backend FastAPI uvicorn server (on port 8001) and the frontend Vite web server (on port 4003):
```bash
./web/restart.sh
```

The application will be active live at:
*   **AlphaForge App:** `http://localhost:4003`
*   **Public Verification Portal:** `http://localhost:4003/verify`
*   **Admin Quota Dashboard:** `http://localhost:4003/usage`

---

## 📂 Project Structure
```text
.
├── Agent.md                         # Consolidated instructions & prompts for all 4 agents
├── web/                             # Web Application root
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