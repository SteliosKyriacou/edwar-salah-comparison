import matplotlib
matplotlib.use('Agg')
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc, precision_recall_curve, average_precision_score
import os

BASE = os.path.join(os.path.dirname(__file__), "..")
DATAROOM_DIR = os.path.join(BASE, "Validation", "dataroom")

def generate_individual_plots(df, model_name, score_col, truth_col):
    """Generate ROC, PRC, Calibration, and Scatter for a single model."""
    valid = ~df[score_col].isna()
    if not valid.any():
        return
        
    y_true = df[truth_col][valid]
    scores = df[score_col][valid]
    
    n = len(y_true)
    n_pos = y_true.sum()
    baseline = n_pos / n if n > 0 else 0
    
    # ── ROC ──────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 7))
    fig.patch.set_facecolor("white")
    
    fpr, tpr, _ = roc_curve(y_true, scores)
    roc_auc = auc(fpr, tpr)
    ax.plot(fpr, tpr, color="#9B59B6", lw=2.5, label=f"{model_name} AUC: {roc_auc:.3f}")
    ax.plot([0, 1], [0, 1], color="black", lw=1, ls=":")
    ax.set_xlabel("False Positive Rate", fontsize=12)
    ax.set_ylabel("True Positive Rate", fontsize=12)
    ax.set_title(f"ROC — {model_name}", fontsize=13, fontweight="bold")
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(True, alpha=0.2)
    ax.set_xlim([0, 1]); ax.set_ylim([0, 1.02])
    
    out = os.path.join(DATAROOM_DIR, f"{model_name}_roc.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved {out}")
    
    # ── PRC ──────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 7))
    fig.patch.set_facecolor("white")
    
    prec, rec, _ = precision_recall_curve(y_true, scores)
    ap = average_precision_score(y_true, scores)
    ax.plot(rec, prec, color="#9B59B6", lw=2.5, label=f"{model_name} AP: {ap:.3f}")
    ax.axhline(y=baseline, color="#555555", linestyle=":", linewidth=1, label=f"Random ({baseline:.2f})")
    ax.set_xlabel("Recall", fontsize=12)
    ax.set_ylabel("Precision", fontsize=12)
    ax.set_title(f"PRC — {model_name}", fontsize=13, fontweight="bold")
    ax.legend(loc="upper right", fontsize=10)
    ax.grid(True, alpha=0.2)
    ax.set_xlim([0, 1]); ax.set_ylim([0, 1.05])
    
    out = os.path.join(DATAROOM_DIR, f"{model_name}_prc.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved {out}")
    
    # ── Calibration ──────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 7))
    fig.patch.set_facecolor("white")
    
    score_bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    score_labels = ["0-10", "10-20", "20-30", "30-40", "40-50", "50-60", "60-70", "70-80", "80-90", "90-100"]
    
    df_temp = pd.DataFrame({"val": scores, "outcome": df['outcome'][valid]})
    df_temp["bin"] = pd.cut(df_temp["val"], bins=score_bins, labels=score_labels, include_lowest=True)
    ct = pd.crosstab(df_temp["bin"], df_temp["outcome"])
    for c in ["Approved", "Liability"]:
        if c not in ct.columns:
            ct[c] = 0
    ct = ct[["Approved", "Liability"]]
    ct_norm = ct.div(ct.sum(axis=1), axis=0).fillna(0)
    ct_norm.plot(kind="bar", stacked=True, ax=ax, color=["#B7E4C7", "#FF7F50"], edgecolor="black", width=0.8)
    
    for i, (idx, row) in enumerate(ct.iterrows()):
        total = row["Approved"] + row["Liability"]
        if total > 0:
            ax.text(i, 1.02, f"n={int(total)}", ha="center", va="bottom", fontsize=9, fontweight="bold")
            
    ax.set_title(f"Calibration — {model_name}", fontsize=13, fontweight="bold")
    ax.set_xlabel("Predicted Probability (%)", fontsize=11)
    ax.set_ylabel("Proportion", fontsize=11)
    ax.tick_params(axis="x", rotation=45)
    ax.legend(loc="upper left", fontsize=9)
    ax.set_ylim(0, 1.15)
    
    out = os.path.join(DATAROOM_DIR, f"{model_name}_calibration.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved {out}")
    
    # ── Scatter ────────────────────────────────────────────
    # For Gemini/Claude we just plot Score vs Index to show distribution since there is no TCSP counterpart
    fig, ax = plt.subplots(figsize=(9, 7))
    fig.patch.set_facecolor("white")
    colors = ["#2ECC71" if y == 1 else "#E74C3C" for y in y_true]
    
    # Random x jitter just to separate the points
    import numpy as np
    x_jitter = np.random.normal(0, 0.1, size=len(scores)) + np.where(y_true == 1, 1, 0)
    
    ax.scatter(x_jitter, scores, c=colors, s=80, edgecolors="black", linewidths=0.5, alpha=0.8)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Liability", "Approved"])
    ax.set_ylabel(f"{model_name} Score (%)", fontsize=12)
    ax.set_title(f"{model_name} Score Distribution", fontsize=13, fontweight="bold")
    ax.grid(True, alpha=0.2)
    out = os.path.join(DATAROOM_DIR, f"{model_name}_scatter.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved {out}")


def main():
    # Load ground truth
    df_v25 = pd.read_csv(os.path.join(DATAROOM_DIR, "SM_V25_GLOBAL.csv"))
    # Make sure we have the isomeric column for merging
    if 'isomeric' not in df_v25.columns:
        print("Error: 'isomeric' missing in V25 data.")
        return
        
    df_v25['Smiles'] = df_v25['isomeric']
    df_v25['y_true'] = (df_v25["category"].astype(str).str.lower() == "approved").astype(int)
    
    medchem_d_col = "MedChem_Descriptor_Tag" if "MedChem_Descriptor_Tag" in df_v25.columns else "MedChem_D"
    if medchem_d_col in df_v25.columns:
        df_v25['outcome'] = df_v25[medchem_d_col].apply(lambda x: "Approved" if "approved_control" in str(x).lower() else "Liability")
    else:
        df_v25['outcome'] = df_v25["category"].apply(lambda x: "Approved" if str(x).lower() == "approved" else "Liability")

    # Lower is better for V25 MedChem Score V25, so we convert it to a "probability" proxy
    # 101 - score
    df_v25['V25_Prob'] = 101 - pd.to_numeric(df_v25['MedChem Score V25'], errors='coerce')
    
    # Load Gemini
    df_gemini = pd.read_csv(os.path.join(DATAROOM_DIR, "gemini-predictions.csv"))
    # 'Probability of Success (%)' -> e.g. "28%"
    df_gemini['Gemini_Prob'] = df_gemini['Probability of Success (%)'].astype(str).str.replace('%', '', regex=False)
    df_gemini['Gemini_Prob'] = pd.to_numeric(df_gemini['Gemini_Prob'], errors='coerce')
    
    # Load Claude
    df_claude = pd.read_csv(os.path.join(DATAROOM_DIR, "Claude-predictions.csv"))
    df_claude['Claude_Prob'] = pd.to_numeric(df_claude['P(success)'], errors='coerce') * 100
    
    # Merge
    merged = df_v25.merge(df_gemini[['Smiles', 'Gemini_Prob']], on='Smiles', how='inner')
    merged = merged.merge(df_claude[['Smiles', 'Claude_Prob']], on='Smiles', how='inner')
    
    print(f"Merged dataset size: N={len(merged)}")
    
    # Generate individual plots
    generate_individual_plots(merged, "gemini-3.5 thinking", "Gemini_Prob", "y_true")
    generate_individual_plots(merged, "Opus 4.8 high", "Claude_Prob", "y_true")
    
    # Comparison Plots
    fig_roc, ax_roc = plt.subplots(figsize=(9, 7))
    fig_roc.patch.set_facecolor("white")
    
    fig_prc, ax_prc = plt.subplots(figsize=(9, 7))
    fig_prc.patch.set_facecolor("white")
    
    baseline = merged['y_true'].mean()
    ax_prc.axhline(y=baseline, color="#555555", linestyle=":", linewidth=1, label=f"Random ({baseline:.2f})")
    
    colors = {"ReneuBio": "#3498DB", "gemini-3.5 thinking": "#2ECC71", "Opus 4.8 high": "#E74C3C"}
    
    for model_name, col in [("ReneuBio", "V25_Prob"), ("gemini-3.5 thinking", "Gemini_Prob"), ("Opus 4.8 high", "Claude_Prob")]:
        valid = ~merged[col].isna()
        y_val = merged['y_true'][valid]
        scores = merged[col][valid]
        
        if len(y_val) == 0:
            continue
            
        # ROC
        fpr, tpr, _ = roc_curve(y_val, scores)
        roc_auc = auc(fpr, tpr)
        ax_roc.plot(fpr, tpr, color=colors[model_name], lw=2.5, label=f"{model_name} AUC: {roc_auc:.3f}")
        
        # PRC
        prec, rec, _ = precision_recall_curve(y_val, scores)
        ap = average_precision_score(y_val, scores)
        ax_prc.plot(rec, prec, color=colors[model_name], lw=2.5, label=f"{model_name} AP: {ap:.3f}")

    # Finalize Comparison ROC
    ax_roc.plot([0, 1], [0, 1], color="black", lw=1, ls=":")
    ax_roc.set_xlabel("False Positive Rate", fontsize=12)
    ax_roc.set_ylabel("True Positive Rate", fontsize=12)
    ax_roc.set_title("ROC Comparison (ReneuBio vs gemini-3.5 thinking vs Opus 4.8 high)", fontsize=13, fontweight="bold")
    ax_roc.legend(loc="lower right", fontsize=10)
    ax_roc.grid(True, alpha=0.2)
    ax_roc.set_xlim([0, 1]); ax_roc.set_ylim([0, 1.02])
    out_roc = os.path.join(DATAROOM_DIR, "Comparison_ROC.png")
    fig_roc.savefig(out_roc, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig_roc)
    print(f"Saved {out_roc}")
    
    # Finalize Comparison PRC
    ax_prc.set_xlabel("Recall", fontsize=12)
    ax_prc.set_ylabel("Precision", fontsize=12)
    ax_prc.set_title("PRC Comparison (ReneuBio vs gemini-3.5 thinking vs Opus 4.8 high)", fontsize=13, fontweight="bold")
    ax_prc.legend(loc="upper right", fontsize=10)
    ax_prc.grid(True, alpha=0.2)
    ax_prc.set_xlim([0, 1]); ax_prc.set_ylim([0, 1.05])
    out_prc = os.path.join(DATAROOM_DIR, "Comparison_PRC.png")
    fig_prc.savefig(out_prc, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig_prc)
    print(f"Saved {out_prc}")

    # ── Bootstrapped AUC Box Plot ────────────────────────────────────────────
    import numpy as np
    n_bootstraps = 1000
    np.random.seed(42)
    roc_auc_results = {"ReneuBio": [], "gemini-3.5 thinking": [], "Opus 4.8 high": []}
    prc_auc_results = {"ReneuBio": [], "gemini-3.5 thinking": [], "Opus 4.8 high": []}
    
    for i in range(n_bootstraps):
        sample = merged.sample(frac=1.0, replace=True)
        if len(sample['y_true'].unique()) < 2:
            continue
            
        for model_name, col in [("ReneuBio", "V25_Prob"), ("gemini-3.5 thinking", "Gemini_Prob"), ("Opus 4.8 high", "Claude_Prob")]:
            valid = ~sample[col].isna()
            y_val = sample['y_true'][valid]
            scores = sample[col][valid]
            if len(y_val.unique()) < 2:
                continue
            fpr, tpr, _ = roc_curve(y_val, scores)
            roc_auc_results[model_name].append(auc(fpr, tpr))
            
            prec, rec, _ = precision_recall_curve(y_val, scores)
            prc_auc_results[model_name].append(average_precision_score(y_val, scores))
            
    def plot_box(results_dict, title, ylabel, filename):
        fig_box, ax_box = plt.subplots(figsize=(8, 6))
        fig_box.patch.set_facecolor("white")
        
        labels = ["ReneuBio", "gemini-3.5 thinking", "Opus 4.8 high"]
        data_to_plot = [results_dict[label] for label in labels]
        box = ax_box.boxplot(data_to_plot, tick_labels=labels, patch_artist=True)
        
        colors_list = ["#3498DB", "#2ECC71", "#E74C3C"]
        for patch, color in zip(box['boxes'], colors_list):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
            
        ax_box.set_ylabel(ylabel, fontsize=12)
        ax_box.set_title(title, fontsize=13, fontweight="bold")
        ax_box.grid(True, alpha=0.2, axis='y')
        
        out_box = os.path.join(DATAROOM_DIR, filename)
        fig_box.savefig(out_box, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig_box)
        print(f"Saved {out_box}")

    plot_box(roc_auc_results, "Bootstrapped ROC AUC Comparison (1000 resamples)", "ROC AUC", "Comparison_ROC_AUC_Boxplot.png")
    plot_box(prc_auc_results, "Bootstrapped PRC AP Comparison (1000 resamples)", "Average Precision (PRC AUC)", "Comparison_PRC_AUC_Boxplot.png")

if __name__ == "__main__":
    main()
