# V25 Multi-Agent Drug Approval Predictor

A multi-agent LLM pipeline that predicts clinical trial success probability for small-molecule drug candidates. Four specialized agents evaluate each molecule in parallel, then a lead agent integrates all assessments into a final score.

## Architecture

```
                    ┌─────────────────────────┐
                    │      Input Molecule      │
                    │  SMILES + Target + Ind.  │
                    └────────────┬────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                   │
              ▼                  ▼                   ▼
   ┌──────────────────┐ ┌───────────────┐ ┌─────────────────┐
   │  Biological-     │ │     Toxi      │ │     Pharma      │
   │  Rationalist     │ │  Toxicologist │ │  Pharmacologist  │
   │  (bio_p1/p2/p3)  │ │ (tox_p1/p2/p3)│ │ (pk_p1/p2/p3)   │
   └────────┬─────────┘ └──────┬────────┘ └────────┬────────┘
            │                  │                    │
            │    ┌─────────────────────────┐        │
            │    │  MedChem-Rationalist    │        │
            │    │  Pass 1 (blind struct.) │        │
            │    │  (chem_p1/p2/p3)        │        │
            │    └────────────┬────────────┘        │
            │                 │                     │
            └─────────────────┼─────────────────────┘
                              ▼
                 ┌─────────────────────────┐
                 │  MedChem-Rationalist    │
                 │  Pass 2 (integration)   │
                 │  → final_p1/p2/p3       │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │  Server-side scoring    │
                 │  TCSP = p1 × p2 × p3   │
                 │  Score = f(TCSP)        │
                 └─────────────────────────┘
```

**Step 1 (parallel):** Four LLM calls run concurrently — Biological-Rationalist, Toxi, Pharma, and MedChem Pass 1.
**Step 2 (sequential):** MedChem Pass 2 integrates all advisories into consensus probabilities.
**Step 3 (deterministic):** `TCSP = final_p1 × final_p2 × final_p3`, then `MedChem Score = round(100 × (1 - √(TCSP / 0.40)))`.

## Agents

| Agent | Role | Output |
|---|---|---|
| **Biological-Rationalist** | Target biology, mechanism validation, druggability | `bio_p1/p2/p3`, verdict (ELITE/CAUTION/TERMINATE) |
| **Toxi** | Safety liabilities, structural alerts, therapeutic window | `tox_p1/p2/p3`, verdict (CLEAN/MANAGEABLE/NARROW/TOXIC) |
| **Pharma** | PK/PD feasibility, dose, oral bioavailability, DDI | `pk_p1/p2/p3`, verdict (FAVORABLE/ADEQUATE/CHALLENGING/IMPRACTICAL) |
| **MedChem-Rationalist** | Structural critique (Pass 1) + advisory integration (Pass 2) | `chem_p1/p2/p3`, `final_p1/p2/p3`, MedChem Score |

## Installation

### 1. Create the conda environment

```bash
conda create -n edward_salah python=3.11 -y
conda activate edward_salah
```

### 2. Install dependencies

```bash
pip install pandas scikit-learn matplotlib langchain-google-genai python-dotenv
```

### 3. Set up your API key

Create a `.env` file in the project root:

```
GOOGLE_API_KEY=your_google_api_key_here
```

The pipeline uses **Google Gemini 3 Pro Preview** via `langchain-google-genai`.

## Usage

### Run on any CSV file

```bash
python src/main.py INPUT_FILE \
    --smiles SMILES_COLUMN \
    --target TARGET_COLUMN \
    --indication INDICATION_COLUMN \
    [-o OUTPUT_FILE] \
    [--name NAME_COLUMN]
```

**Arguments:**
- `INPUT_FILE` — path to input CSV
- `--smiles` — column containing SMILES strings
- `--target` — column containing target class (e.g., "Enzyme", "GPCR", "Kinase")
- `--indication` — column containing therapeutic area (e.g., "Oncology", "Cardiovascular")
- `-o` / `--output` — output CSV path (default: `<input>_V25.csv`)
- `--name` — optional column for compound name (shown in progress output)

**Example:**

```bash
conda activate edward_salah

# Run on a custom dataset
python src/main.py my_molecules.csv \
    --smiles canonical_smiles \
    --target target_class \
    --indication therapeutic_area \
    --name compound_name \
    -o results/my_molecules_scored.csv
```

The output CSV contains all original columns plus all V25 computed columns (scores, verdicts, probabilities, rationales).

### Resumability

All runs use append-only `.jsonl` progress files. If interrupted, re-run the same command — it resumes from where it left off. To start fresh, delete the progress file (printed at startup).

## Smoke Test

```bash
python test/test_v25_smoke.py
```

Runs the pipeline on 2 molecules:
- **Good:** Atorvastatin (HMG-CoA inhibitor) — expects low score
- **Bad:** Toxic design (nitroaromatic + hydrazine + hERG trap) — expects high score

Verifies the system correctly differentiates good from bad molecules.

## Recreating Validation Results

The `Validation/` folder contains input data and output subfolders for reproducible benchmarking.

### Input Data

All input CSVs are in `Validation/data/`:

| File | Description |
|---|---|
| `2025_drug_data_complete.csv` | 29 drugs with known 2025 outcomes |
| `final_drug_data_SM_complete.csv` | 394 small molecules (split into Modern ≥1999 and Legacy <1999) |
| `neuro_candidates.csv` | Neurological drug candidates |

### Step 1 — Run V25 on 2025 drugs (N=29, ~30 min)

```bash
python -u src/run_2025_v25.py
# Output: Validation/2025/2025_V25_EDWARD_SALAH.csv
# Progress: 2025_v25_progress.jsonl
```

### Step 2 — Run V25 on Modern SM (N=219, ~5 hours)

```bash
python -u src/run_v25_sm.py
# Output: Validation/modern/SM_V25_EDWARD_SALAH.csv
# Progress: sm_v25_progress.jsonl
```

### Step 3 — Run V25 on Legacy SM (N=175, ~4 hours)

```bash
python -u src/run_v25_legacy.py
# Output: Validation/legacy/SM_V25_EDWARD_SALAH_LEGACY.csv
# Progress: legacy_v25_progress.jsonl
```

### Step 4 — Combine Modern + Legacy into Global

```bash
python -c "
import pandas as pd
modern = pd.read_csv('Validation/modern/SM_V25_EDWARD_SALAH.csv')
legacy = pd.read_csv('Validation/legacy/SM_V25_EDWARD_SALAH_LEGACY.csv')
pd.concat([modern, legacy], ignore_index=True).to_csv('Validation/global/SM_V25_EDWARD_SALAH_GLOBAL.csv', index=False)
print(f'Global: {len(modern) + len(legacy)} rows')
"
```

### Step 5 — Generate comparison figures

The figure scripts read from the V25 CSVs above (plus earlier version CSVs if available). No LLM calls needed.

```bash
# 2025: V24 vs V25 ROC, PRC, calibration, score drift
python src/generate_2025_v25_figures.py
# Output: Validation/2025/2025_v24_vs_v25_roc.png
#         Validation/2025/2025_v24_vs_v25_prc.png
#         Validation/2025/2025_v24_vs_v25_calibration.png
#         Validation/2025/2025_v24_vs_v25_score_drift.png
#         Validation/2025/2025_v25_calibration.png
#         Validation/2025/2025_v25_raw_tcsp_calibration.png

# Modern/Legacy/Global: V20→V25 5-way comparison
python src/generate_v25_figures.py
# Output: Validation/{modern,legacy,global}/sm_v20_v22_v23_v24_v25_roc.png
#         Validation/{modern,legacy,global}/sm_v20_v22_v23_v24_v25_prc.png
#         Validation/{modern,legacy,global}/sm_v20_v22_v23_v24_v25_calibration.png
```

### Validation Folder Structure

```
Validation/
├── data/
│   ├── 2025_drug_data_complete.csv
│   ├── final_drug_data_SM_complete.csv
│   └── neuro_candidates.csv
├── 2025/          # 2025 drug results + figures
├── modern/        # Modern era (≥1999) results + figures
├── legacy/        # Legacy era (<1999) results + figures
└── global/        # Combined modern+legacy results + figures
```

## Project Structure

```
.
├── Agents/
│   ├── medchem-rationalist/INSTRUCTIONS.md
│   ├── biological-rationalist/INSTRUCTIONS.md
│   ├── toxi-predictive-toxicologist/INSTRUCTIONS.md
│   └── pharma-clinical-pharmacologist/INSTRUCTIONS.md
├── src/
│   ├── main.py                      # Generic CLI entry point
│   ├── run_2025_v25.py              # V25 pipeline for 2025 drugs
│   ├── run_v25_sm.py                # V25 pipeline for Modern SM
│   ├── run_v25_legacy.py            # V25 pipeline for Legacy SM
│   ├── generate_2025_v25_figures.py # 2025 comparison figures
│   └── generate_v25_figures.py      # Multi-version comparison figures
├── test/
│   └── test_v25_smoke.py            # Smoke test (1 good + 1 bad molecule)
├── Validation/                      # Input data + output results
├── .env                             # API key (not committed)
└── README.md
```

## Scoring

- **MedChem Score**: 1 (best) to 100 (worst). Derived deterministically from TCSP.
- **TCSP** (Total Clinical Success Probability): `final_p1 × final_p2 × final_p3`. Raw probability of approval.
- **P1/P2/P3**: Per-phase probabilities calibrated against industry base rates (P1~0.65, P2~0.30, P3~0.58).
