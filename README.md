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

## 🛠 How to Recreate the Analysis
All necessary scripts and agent definitions are provided in this repository.

1.  **Environment**: Use the `openfe_elite` Conda environment or any environment with `pandas`, `seaborn`, `matplotlib`, `langchain`, and `langchain-google-genai`.
2.  **API Key**: Export your Google API Key: `export GOOGLE_API_KEY="your_key"`.
3.  **Run the Audit**: 
    - The coordinated V22 audit uses `src/run_v22_coordinated_audit.py`. It requires the `Agents/` folder and the input CSVs.
4.  **Generate Figures**: 
    - Use `src/generate_v20_vs_v22_coordinated.py` to recreate the ROC, Calibration, and Transposed Factors plots comparing the pure structural engine against the biological insight engine.

## 🏁 Conclusion
The transition from V20 to V22 represents the shift from a **Structural Filter** to a **Clinical Success Predictor**. The Edward x Salah partnership is now the absolute reference standard for our autonomous lead optimization pipeline. 🧬🦾
