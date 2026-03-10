# Edward Comparison Archive: V20 vs. V22 Master Benchmark

This folder contains the definitive performance comparison between the purely structural medicinal chemistry engine and the coordinated dual-agent pipeline.

## 🏁 The Core Comparison
We are evaluating the impact of **Biological & Clinical Intelligence** on medicinal chemistry risk assessment.

*   **V20 (The Pure Chemist)**: Evaluates molecules based strictly on chemical structure, physical properties (MPO), and structural alerts (MBI, hERG, Toxicophores). It is strictly "Librarian-Blind" (no name identification).
*   **V22 (The Coordinated Pipeline)**: Uses **Salah (Biologist/Pharmacologist)** to perform a preliminary target/indication risk assessment. **Edward (Chemist)** then integrates Salah's advisory (Target Stigma, Dose-Mediated Toxicity, Graveyard Classes) into his structural critique to set the final score.

## 📊 Dataset Specifications (N=270 Modern Era)
The primary comparison focuses on the **Modern Era (Post-1995)**. Pre-1995 "Legacy" drugs (hydrazines, toxic fatty acids, greasy tricyclics) were removed to establish a high-fidelity benchmark consistent with 21st-century safety standards.

### Data Files
1.  **`EDWARD_V20_MASTER_MODERN.csv`**: Baseline scores (N=270) using the pure structural engine.
2.  **`EDWARD_V22_MASTER_MODERN.csv`**: Coordinated scores (N=270) integrating biological insights.
3.  **`EDWARD_V20_MASTER_GLOBAL.csv`**: The full 405-molecule baseline (all years included).

## 🧪 Key Figures (`/figures`)
*   **`edward_v20_vs_v22_modern_roc.png`**: Performance spike verification. Shows the AUC boost gained by adding biological intelligence.
*   **`edward_v20_vs_v22_modern_calibration.png`**: Side-by-side distribution of Success vs. Liability. Shows how V22 "cleans" the elite tier of biologically high-risk compounds.
*   **`edward_v20_vs_v22_factors_transposed.png`**: The "Salah Effect" map. Tracks the vertical median score jump for every clinical outcome tag (e.g., +33 for Hepatotoxicity).
*   **`edward_v20_vs_v22_score_drift.png`**: Scatter plot visualizing the "Biological Penalty" applied to chemically clean failures.

## 🛠 How to Recreate the V20/V22 Analysis
All necessary scripts and agent definitions are provided in this repository.

1.  **Environment**: Use the `openfe_elite` Conda environment or any environment with `pandas`, `seaborn`, `matplotlib`, `langchain`, and `langchain-google-genai`.
2.  **API Key**: Export your Google API Key: `export GOOGLE_API_KEY="your_key"`.
3.  **Run the Audit**:
    - The coordinated V22 audit uses `src/run_v22_coordinated_audit.py`. It requires the `Agents/` folder and the input CSVs.
4.  **Generate Figures**:
    - Use `src/generate_v20_vs_v22_coordinated.py` to recreate the ROC, Calibration, and Transposed Factors plots comparing the pure structural engine against the biological insight engine.

---

## 🧬 V23 — Calibrated Structural Alerts (branch: `v23`)

V23 applies two targeted prompt fixes to the V22 pipeline:
1. **Edward**: Prevent scaffold-similarity guessing + calibrate structural alert severity (alerts are risk factors, not automatic death sentences)
2. **Salah**: Add Librarian Ban (no molecule identification by name)

### V23 AUC Summary

| Set | V20 | V22 | V23 |
|---|---|---|---|
| Modern (N=219) | 0.774 | 0.933 | 0.877 |
| Legacy (N=175) | 0.806 | 0.916 | 0.813 |
| Global (N=394) | 0.740 | 0.900 | 0.828 |
| 2025 (N=29) | — | — | 0.643 |

### How to Recreate All V23 CSVs in `Salah/`

**Prerequisites**: Activate the `edward_salah` conda environment. Ensure `.env` contains your `GOOGLE_API_KEY`. The input dataset is `final_drug_data_SM_complete.csv` (394 molecules). The 2025 dataset is `2025_drug_data_complete.csv` (29 molecules).

```bash
conda activate edward_salah
```

**Step 1 — Run V23 Modern SM audit (219 molecules, ~5 hours)**
```bash
# Produces: Salah/modern/SM_V23_EDWARD_SALAH.csv
# Progress: sm_v23_progress.jsonl (resumable)
python -u src/run_v23_sm.py
```

**Step 2 — Run V23 Legacy SM audit (175 molecules, ~4 hours)**
```bash
# Produces: Salah/legacy/SM_V23_EDWARD_SALAH_LEGACY.csv
# Progress: legacy_v23_progress.jsonl (resumable)
python -u src/run_v23_legacy.py
```

**Step 3 — Run V23 on 2025 drug data (29 molecules, ~20 min)**
```bash
# Produces: Salah/2025/2025_V23_EDWARD_SALAH.csv
# Progress: 2025_v23_progress.jsonl (resumable)
python -u src/run_2025_v23.py
```

**Step 4 — Combine Modern + Legacy into Global CSV**
```bash
python -c "
import pandas as pd
modern = pd.read_csv('Salah/modern/SM_V23_EDWARD_SALAH.csv')
legacy = pd.read_csv('Salah/legacy/SM_V23_EDWARD_SALAH_LEGACY.csv')
pd.concat([modern, legacy], ignore_index=True).to_csv('Salah/global/SM_V23_EDWARD_SALAH_GLOBAL.csv', index=False)
print(f'Global: {len(modern) + len(legacy)} rows')
"
```

### How to Recreate All V23 Plots

All figure scripts read from the CSVs above. No LLM calls needed.

```bash
# Modern: V20 vs V22 vs V23 ROC + PRC (3-way comparison)
python src/generate_v23_roc.py
# Output: Salah/modern/sm_v20_v22_v23_roc.png
#         Salah/modern/sm_v20_v22_v23_prc.png

# Modern: V20 vs V23 ROC + calibration bar chart (3-panel)
python src/generate_v23_figures.py
# Output: Salah/modern/sm_v20_vs_v23_roc.png
#         Salah/modern/sm_v20_v22_v23_calibration.png

# Global + Legacy: V20 vs V22 vs V23 ROC, PRC, calibration
python src/generate_global_v23_figures.py
# Output: Salah/global/sm_v20_v22_v23_roc.png
#         Salah/global/sm_v20_v22_v23_prc.png
#         Salah/global/sm_v20_v22_v23_calibration.png
#         Salah/legacy/sm_v20_v22_v23_roc.png

# 2025: Calibration, ROC, PRC
python src/generate_2025_figures.py
# Output: Salah/2025/2025_v23_calibration.png
#         Salah/2025/2025_v23_roc.png
#         Salah/2025/2025_v23_prc.png

# V20 vs V22 PRC curves (all sets, existing)
python src/generate_prc_curves.py
# Output: Salah/modern/sm_edward_vs_edward_salah_prc.png
#         Salah/global/sm_edward_vs_edward_salah_prc.png
#         Salah/legacy/sm_edward_vs_edward_salah_prc.png
#         Salah/prc_all_sets_combined.png
```

### Salah Folder Structure

```
Salah/
├── modern/
│   ├── SM_V20_EDWARD_ONLY.csv              # V20 Edward-only (219 molecules)
│   ├── SM_V22_EDWARD_SALAH.csv             # V22 Edward+Salah (219 molecules)
│   ├── SM_V23_EDWARD_SALAH.csv             # V23 Calibrated (219 molecules)
│   ├── sm_v20_v22_v23_roc.png              # 3-way ROC comparison
│   ├── sm_v20_v22_v23_prc.png              # 3-way PRC comparison
│   ├── sm_v20_v22_v23_calibration.png      # 3-panel calibration bar chart
│   ├── sm_v20_vs_v23_roc.png              # V20 vs V23 direct ROC
│   ├── sm_edward_vs_edward_salah_*.png     # V20 vs V22 figures
│   └── sm_v2*_progress.jsonl              # Progress files
├── legacy/
│   ├── SM_V20_EDWARD_ONLY_LEGACY.csv       # V20 (175 molecules)
│   ├── SM_V22_EDWARD_SALAH_LEGACY.csv      # V22 (175 molecules)
│   ├── SM_V23_EDWARD_SALAH_LEGACY.csv      # V23 (175 molecules)
│   ├── sm_v20_v22_v23_roc.png              # 3-way ROC
│   └── sm_edward_vs_edward_salah_*.png     # V20 vs V22 figures
├── global/
│   ├── SM_V20_EDWARD_ONLY_GLOBAL.csv       # V20 (394 molecules)
│   ├── SM_V22_EDWARD_SALAH_GLOBAL.csv      # V22 (394 molecules)
│   ├── SM_V23_EDWARD_SALAH_GLOBAL.csv      # V23 (394 molecules)
│   ├── sm_v20_v22_v23_roc.png              # 3-way ROC
│   ├── sm_v20_v22_v23_prc.png              # 3-way PRC
│   ├── sm_v20_v22_v23_calibration.png      # 3-panel calibration
│   └── sm_edward_vs_edward_salah_*.png     # V20 vs V22 figures
└── 2025/
    ├── 2025_V23_EDWARD_SALAH.csv           # V23 (29 molecules)
    ├── 2025_v23_calibration.png            # Calibration bar chart
    ├── 2025_v23_roc.png                    # ROC curve (AUC 0.643)
    └── 2025_v23_prc.png                    # PRC curve
```

### Notes on Resumability

All audit scripts use append-only `.jsonl` progress files. If a run is interrupted, simply re-run the same script — it will count existing lines in the progress file and resume from where it left off. To start fresh, delete the corresponding progress file first.

### Notes on 2025 Dataset

The 2025 drug data (`2025_drug_data_complete.csv`) contains 29 molecules after removing 3 data-quality exclusions (Pasodacigib, BAY-2965501, Bitopertin). V23 achieves AUC 0.643 on this set due to a paradigm shift in drug design — see `post_2025_instructions.md` for detailed failure analysis and V24 upgrade priorities.

## 🏁 Conclusion
The transition from V20 to V22 represents the shift from a **Structural Filter** to a **Clinical Success Predictor**. V23 adds structural alert calibration and Librarian Ban enforcement, maintaining strong performance on historical data (Global AUC 0.828) while revealing the need for era-aware updates on 2025 drugs. See `post_2025_instructions.md` for the roadmap to V24.
